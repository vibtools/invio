from __future__ import annotations

import base64
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

from src.core.provider_runtime import AccountSnapshot, ProviderRuntime, ProviderRuntimeError, provider_adapter_contract
from src.core.provider_runtime.runtime import _SchedulerHealthState, _stdlib_transport
from src.core.state import AppState


class _Context:
    def __init__(self, task):
        self.task = task
        self.pause_gate = threading.Event()
        self.pause_gate.set()
        self.stop_flag = threading.Event()
        self.logs: list[str] = []
        self.progress_events: list[tuple[int, int, int, str]] = []

    def log(self, message: str) -> None:
        self.logs.append(message)

    def progress(self, processed: int, success: int, failed: int, message: str) -> None:
        self.progress_events.append((processed, success, failed, message))


class P09SchedulingTests(unittest.TestCase):
    def _state(self, emails=None, *, account_count=2):
        state = AppState()
        accounts = []
        for index in range(account_count):
            suffix = chr(ord("A") + index)
            accounts.append(
                state.add_account(
                    "stripe",
                    "Stripe",
                    suffix,
                    "Test",
                    {"secret_key": f"sk_test_account{suffix}"},
                    status="Verified",
                )
            )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, emails or ["a@example.com"])
        template = state.save_invoice_template(
            template_id=None,
            name="Monthly",
            currency="usd",
            days_until_due=30,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            invoice_title="Invoice",
            invoice_subtitle="",
            customer_note="",
            terms=[],
            items=[("Service", "1", "10.00", "0")],
        )
        task = state.create_task(
            "stripe",
            "Stripe",
            [account.id for account in accounts],
            customer_list.id,
            template.id,
        )
        return state, task, accounts

    @staticmethod
    def _account_snapshot(account) -> AccountSnapshot:
        return AccountSnapshot(account.id, account.name, account.mode, dict(account.credentials))

    def test_stripe_adapter_declares_exact_owner_approved_rate_policy(self):
        adapter = provider_adapter_contract("stripe")
        self.assertIsNotNone(adapter)
        policy = adapter.scheduling_policy
        self.assertIsNotNone(policy)
        self.assertEqual(policy.requests_per_second_per_account, 20.0)
        self.assertEqual(policy.burst_capacity, 1)
        self.assertEqual(policy.account_cooldown_base_seconds, 5.0)
        self.assertEqual(policy.account_cooldown_cap_seconds, 60.0)
        self.assertEqual(policy.provider_cooldown_base_seconds, 5.0)
        self.assertEqual(policy.provider_cooldown_cap_seconds, 60.0)
        self.assertIsNone(provider_adapter_contract("refrens").scheduling_policy)
        self.assertIsNone(provider_adapter_contract("agiled").scheduling_policy)

    def test_transport_preserves_stripe_rate_limit_reason(self):
        error = HTTPError(
            "https://api.stripe.com/v1/invoices",
            429,
            "rate limited",
            {"Retry-After": "7", "Stripe-Rate-Limited-Reason": "endpoint-rate"},
            None,
        )
        error.read = lambda: b'{"error":{"message":"slow down"}}'  # type: ignore[method-assign]
        with patch("src.core.provider_runtime.runtime.urlopen", side_effect=error):
            with self.assertRaises(ProviderRuntimeError) as raised:
                _stdlib_transport("GET", "https://api.stripe.com/v1/invoices", {}, None, 30.0)
        self.assertEqual(raised.exception.rate_limit_reason, "endpoint-rate")
        self.assertEqual(raised.exception.retry_after_seconds, 7.0)
        self.assertTrue(raised.exception.retryable)

    def test_per_account_rate_slots_are_independent_and_spaced_at_twenty_per_second(self):
        state, task, accounts = self._state()
        del state
        runtime = ProviderRuntime()
        context = _Context(task)
        account_a = self._account_snapshot(accounts[0])
        account_b = self._account_snapshot(accounts[1])
        clock = [100.0]
        waits: list[float] = []

        def wait(_context, delay):
            waits.append(delay)
            clock[0] += delay
            return True

        with patch("src.core.provider_runtime.runtime.time.monotonic", side_effect=lambda: clock[0]), patch(
            "src.core.provider_runtime.runtime._cooperative_retry_wait", side_effect=wait
        ):
            self.assertTrue(runtime._await_account_rate_slot(context, "stripe", account_a))
            self.assertTrue(runtime._await_account_rate_slot(context, "stripe", account_b))
            self.assertTrue(runtime._await_account_rate_slot(context, "stripe", account_a))

        self.assertEqual(len(waits), 1)
        self.assertAlmostEqual(waits[0], 0.05, places=6)

    def test_account_rate_limit_cooldown_progresses_and_retry_after_can_extend_it(self):
        _state, _task, accounts = self._state()
        runtime = ProviderRuntime()
        account = self._account_snapshot(accounts[0])
        with patch("src.core.provider_runtime.runtime.time.monotonic", return_value=100.0):
            for expected in (5.0, 10.0, 20.0, 40.0, 60.0):
                messages = runtime._record_scheduler_failure(
                    "stripe",
                    account,
                    ProviderRuntimeError(
                        "rate limited",
                        category="rate-limit",
                        retryable=True,
                        http_status=429,
                        retry_after_seconds=0.0,
                        rate_limit_reason="endpoint-rate",
                    ),
                )
                state = runtime._account_health[("stripe", account.id)]
                self.assertAlmostEqual(state.cooldown_until, 100.0 + expected)
                self.assertTrue(messages)
            runtime._record_scheduler_failure(
                "stripe",
                account,
                ProviderRuntimeError(
                    "rate limited",
                    category="rate-limit",
                    retryable=True,
                    http_status=429,
                    retry_after_seconds=90.0,
                    rate_limit_reason="endpoint-rate",
                ),
            )
        self.assertEqual(runtime._account_health[("stripe", account.id)].cooldown_until, 190.0)

    def test_unknown_429_and_deterministic_4xx_do_not_create_failover_health(self):
        _state, _task, accounts = self._state()
        runtime = ProviderRuntime()
        account = self._account_snapshot(accounts[0])
        for exc in (
            ProviderRuntimeError("unknown 429", category="rate-limit", retryable=True, http_status=429),
            ProviderRuntimeError("bad customer", category="http", retryable=False, http_status=400),
            ProviderRuntimeError("conflict", category="http", retryable=False, http_status=409),
            ProviderRuntimeError("invalid", category="http", retryable=False, http_status=422),
        ):
            self.assertEqual(runtime._record_scheduler_failure("stripe", account, exc), ())
        self.assertNotIn(("stripe", account.id), runtime._account_health)
        self.assertNotIn("stripe", runtime._provider_health)

    def test_provider_transient_failure_creates_provider_cooldown_not_account_failover_state(self):
        _state, _task, accounts = self._state()
        runtime = ProviderRuntime()
        account = self._account_snapshot(accounts[0])
        with patch("src.core.provider_runtime.runtime.time.monotonic", return_value=50.0):
            messages = runtime._record_scheduler_failure(
                "stripe",
                account,
                ProviderRuntimeError("unavailable", category="http", retryable=True, http_status=503),
            )
        self.assertNotIn(("stripe", account.id), runtime._account_health)
        self.assertEqual(runtime._provider_health["stripe"].cooldown_until, 55.0)
        self.assertTrue(any("account hopping is disabled" in message for message in messages))

    def test_unattempted_recipient_uses_deterministic_circular_fallback_when_primary_is_cooling(self):
        state, task, accounts = self._state(["a@example.com"], account_count=3)
        runtime = ProviderRuntime()
        snapshot = runtime._snapshot(task, state)
        context = _Context(task)
        primary = snapshot.accounts[0]
        runtime._account_health[("stripe", primary.id)] = _SchedulerHealthState(
            consecutive_incidents=1,
            cooldown_until=time.monotonic() + 30.0,
            last_reason="endpoint-rate",
        )
        selected = runtime._select_stripe_account(context, snapshot, "a@example.com", 0, allow_failover=True)
        self.assertEqual(selected.id, snapshot.accounts[1].id)
        self.assertTrue(any("routing unattempted recipient" in message for message in context.logs))

    def test_all_eligible_accounts_cooling_waits_for_earliest_expiry_without_spinning(self):
        state, task, _accounts = self._state(["a@example.com"], account_count=2)
        runtime = ProviderRuntime()
        snapshot = runtime._snapshot(task, state)
        context = _Context(task)
        clock = [100.0]
        runtime._account_health[("stripe", snapshot.accounts[0].id)] = _SchedulerHealthState(
            consecutive_incidents=1, cooldown_until=105.0
        )
        runtime._account_health[("stripe", snapshot.accounts[1].id)] = _SchedulerHealthState(
            consecutive_incidents=1, cooldown_until=110.0
        )
        waits: list[float] = []

        def wait(_context, delay):
            waits.append(delay)
            clock[0] += delay
            return True

        with patch("src.core.provider_runtime.runtime.time.monotonic", side_effect=lambda: clock[0]), patch(
            "src.core.provider_runtime.runtime._cooperative_retry_wait", side_effect=wait
        ):
            selected = runtime._select_stripe_account(context, snapshot, "a@example.com", 0, allow_failover=True)
        self.assertEqual(selected.id, snapshot.accounts[0].id)
        self.assertEqual(waits, [5.0])

    def test_attempted_pending_recipient_never_cross_account_fails_over_on_resume(self):
        state, task, _accounts = self._state(["a@example.com"], account_count=2)
        runtime = ProviderRuntime()
        runtime.make_task_runner(task, state)  # initialize current-session delivery state without executing transport
        delivery = runtime._delivery_state[task.id]
        primary_id = task.account_ids[0]
        delivery.attempted_recipients.add("a@example.com")
        delivery.attempted_account_ids["a@example.com"] = primary_id
        task.status = "Stopped"
        runtime._account_health[("stripe", primary_id)] = _SchedulerHealthState(
            consecutive_incidents=1, cooldown_until=time.monotonic() + 30.0
        )
        used: list[str] = []

        def send(_context, _snapshot, account, _email):
            used.append(account.id)
            return {"id": "in_1"}

        runtime._send_stripe_invoice_with_retry = send  # type: ignore[method-assign]
        with patch.object(runtime, "_wait_for_account_health", return_value=True):
            runtime.make_task_runner(task, state, resume_remaining=True)(_Context(task))
        self.assertEqual(used, [primary_id])

    def test_failed_over_attempted_recipient_reuses_selected_fallback_account_on_resume(self):
        state, task, _accounts = self._state(["a@example.com"], account_count=2)
        runtime = ProviderRuntime()
        runtime.make_task_runner(task, state)
        delivery = runtime._delivery_state[task.id]
        fallback_id = task.account_ids[1]
        delivery.attempted_recipients.add("a@example.com")
        delivery.attempted_account_ids["a@example.com"] = fallback_id
        task.status = "Stopped"
        used: list[str] = []

        def send(_context, _snapshot, account, _email):
            used.append(account.id)
            return {"id": "in_1"}

        runtime._send_stripe_invoice_with_retry = send  # type: ignore[method-assign]
        runtime.make_task_runner(task, state, resume_remaining=True)(_Context(task))
        self.assertEqual(used, [fallback_id])

    def test_attempted_recipient_without_exact_account_binding_fails_closed(self):
        state, task, _accounts = self._state(["a@example.com"], account_count=2)
        runtime = ProviderRuntime()
        runtime.make_task_runner(task, state)
        runtime._delivery_state[task.id].attempted_recipients.add("a@example.com")
        task.status = "Stopped"
        with self.assertRaisesRegex(ProviderRuntimeError, "no exact account binding"):
            runtime.make_task_runner(task, state, resume_remaining=True)(_Context(task))

    def test_unattempted_pending_recipient_can_fail_over_on_resume(self):
        state, task, _accounts = self._state(["a@example.com"], account_count=2)
        runtime = ProviderRuntime()
        runtime.make_task_runner(task, state)
        task.status = "Stopped"
        primary_id, fallback_id = task.account_ids
        runtime._account_health[("stripe", primary_id)] = _SchedulerHealthState(
            consecutive_incidents=1, cooldown_until=time.monotonic() + 30.0
        )
        used: list[str] = []

        def send(_context, _snapshot, account, _email):
            used.append(account.id)
            return {"id": "in_1"}

        runtime._send_stripe_invoice_with_retry = send  # type: ignore[method-assign]
        runtime.make_task_runner(task, state, resume_remaining=True)(_Context(task))
        self.assertEqual(used, [fallback_id])

    def test_auth_failure_blocks_account_and_future_primary_recipient_fails_without_network_replay(self):
        state, task, accounts = self._state(
            ["first@example.com", "second@example.com", "third@example.com"], account_count=2
        )
        runtime = ProviderRuntime()
        calls: list[tuple[str, str]] = []

        def send(_context, _snapshot, account, email):
            calls.append((account.id, email))
            if account.id == accounts[0].id:
                raise ProviderRuntimeError("unauthorized", category="http", retryable=False, http_status=401)
            return {"id": "in_1"}

        runtime._send_stripe_invoice_with_retry = send  # type: ignore[method-assign]
        context = _Context(task)
        with self.assertRaisesRegex(ProviderRuntimeError, r"2 recipient\(s\) failed"):
            runtime.make_task_runner(task, state)(context)
        self.assertEqual(
            calls,
            [
                (accounts[0].id, "first@example.com"),
                (accounts[1].id, "second@example.com"),
            ],
        )
        self.assertTrue(any("blocked for this runtime" in message for message in context.logs))
        self.assertEqual(context.progress_events[-1][:3], (3, 1, 2))

    def test_account_rate_failure_exhaustion_cools_primary_and_next_unattempted_primary_uses_fallback(self):
        state, task, accounts = self._state(
            ["first@example.com", "second@example.com", "third@example.com"], account_count=2
        )
        runtime = ProviderRuntime(retry_jitter_source=lambda: 0.0)
        runtime._retry_delay_seconds = lambda *_args: 0.0  # type: ignore[method-assign]
        runtime._await_account_rate_slot = lambda *_args, **_kwargs: True  # type: ignore[method-assign]
        auth_a = "Basic " + base64.b64encode(b"sk_test_accountA:").decode("ascii")
        current_email: dict[str, str] = {}
        sends: list[tuple[str, str]] = []

        def transport(method, url, headers, body, timeout):
            del timeout
            path = urlparse(url).path
            auth = headers.get("Authorization", "")
            if method == "GET" and path.endswith("/customers"):
                email = parse_qs(urlparse(url).query).get("email", [""])[0]
                current_email[auth] = email
                return {"data": []}
            if method == "POST" and path.endswith("/customers"):
                email = parse_qs((body or b"").decode()).get("email", [""])[0]
                current_email[auth] = email
                return {"id": "cus_1"}
            if method == "POST" and path.endswith("/invoices"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/invoiceitems"):
                return {"id": "ii_1"}
            if method == "POST" and path.endswith("/finalize"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/send"):
                email = current_email.get(auth, "")
                sends.append((auth, email))
                if auth == auth_a and email == "first@example.com":
                    raise ProviderRuntimeError(
                        "rate limited",
                        category="rate-limit",
                        retryable=True,
                        http_status=429,
                        retry_after_seconds=0.0,
                        rate_limit_reason="endpoint-rate",
                    )
                return {"id": "in_1"}
            raise AssertionError((method, url))

        runtime._transport = transport
        context = _Context(task)
        with self.assertRaisesRegex(ProviderRuntimeError, r"1 recipient\(s\) failed"):
            runtime.make_task_runner(task, state)(context)
        first_attempts = [item for item in sends if item[1] == "first@example.com"]
        third_attempts = [item for item in sends if item[1] == "third@example.com"]
        self.assertEqual(len(first_attempts), 3)
        self.assertTrue(all(auth == auth_a for auth, _email in first_attempts))
        self.assertEqual(len(third_attempts), 1)
        self.assertNotEqual(third_attempts[0][0], auth_a)
        self.assertEqual(context.progress_events[-1][:3], (3, 2, 1))

    def test_success_resets_transient_account_and_provider_health(self):
        _state, _task, accounts = self._state()
        runtime = ProviderRuntime()
        account = self._account_snapshot(accounts[0])
        runtime._account_health[("stripe", account.id)] = _SchedulerHealthState(
            consecutive_incidents=3, cooldown_until=time.monotonic() + 30.0, last_reason="endpoint-rate"
        )
        runtime._provider_health["stripe"] = _SchedulerHealthState(
            consecutive_incidents=2, cooldown_until=time.monotonic() + 30.0, last_reason="HTTP 503"
        )
        runtime._record_scheduler_success("stripe", account)
        self.assertEqual(runtime._account_health[("stripe", account.id)].consecutive_incidents, 0)
        self.assertEqual(runtime._account_health[("stripe", account.id)].cooldown_until, 0.0)
        self.assertEqual(runtime._provider_health["stripe"].consecutive_incidents, 0)
        self.assertEqual(runtime._provider_health["stripe"].cooldown_until, 0.0)

    def test_successful_reverification_clears_health_and_rate_slot_for_account(self):
        _state, _task, accounts = self._state()
        runtime = ProviderRuntime()
        account = self._account_snapshot(accounts[0])
        key = ("stripe", account.id)
        runtime._account_health[key] = _SchedulerHealthState(blocked_reason="unauthorized")
        runtime._account_next_request_at[key] = time.monotonic() + 30.0
        runtime.reset_account_health(account.id, provider_id="stripe")
        self.assertNotIn(key, runtime._account_health)
        self.assertNotIn(key, runtime._account_next_request_at)

    def test_rate_wait_stops_before_reserving_another_request_slot(self):
        state, task, accounts = self._state()
        del state
        runtime = ProviderRuntime()
        context = _Context(task)
        account = self._account_snapshot(accounts[0])
        self.assertTrue(runtime._await_account_rate_slot(context, "stripe", account))
        context.stop_flag.set()
        self.assertFalse(runtime._await_account_rate_slot(context, "stripe", account))

    def test_successful_reverification_reset_hook_is_wired_without_new_ui(self):
        root = Path(__file__).resolve().parents[1]
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        worker = (root / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(window.count("reset_account_health(updated.id, provider_id=updated.provider_id)"), 2)
        self.assertNotIn("ThreadPoolExecutor", worker)
        self.assertNotIn("asyncio", worker)
        self.assertEqual(worker.count("QThread("), 1)


if __name__ == "__main__":
    unittest.main()
