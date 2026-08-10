from __future__ import annotations

import json
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse

from src.core.provider_manager import ProviderManager
from src.core.provider_runtime import (
    ProviderRuntime,
    ProviderRuntimeError,
    effective_capabilities,
    preflight_runtime_inputs,
    provider_adapter_contract,
)
from src.core.state import AppState
from src.core.storage import CredentialStore, DomainStore
from src.customers.models import CustomerRecord
from src.invoices.templates import InvoiceItemTemplate, InvoiceTemplate
from src.tasks.delivery_ledger import (
    DELIVERY_OPERATION_FAILED,
    DELIVERY_OPERATION_SUCCEEDED,
    DELIVERY_OPERATION_UNCERTAIN,
)

ROOT = Path(__file__).resolve().parents[1]


class _Keyring:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def set_password(self, service_name: str, username: str, password: str) -> None:
        self.values[(service_name, username)] = password

    def get_password(self, service_name: str, username: str) -> str | None:
        return self.values.get((service_name, username))

    def delete_password(self, service_name: str, username: str) -> None:
        self.values.pop((service_name, username), None)


class _Context:
    def __init__(self, task) -> None:
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


class P11RefrensTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = DomainStore(self.root / "domain.sqlite3")
        self.credentials = CredentialStore(_Keyring())

    def state(self) -> AppState:
        return AppState(
            domain_store=self.store,
            credential_store=self.credentials,
            loaded=self.store.load(self.credentials),
        )

    def task_state(self, customers: list[CustomerRecord], *, account_count: int = 1):
        state = self.state()
        accounts = []
        for index in range(account_count):
            suffix = chr(ord("A") + index)
            account = state.add_account(
                "refrens",
                "Refrens",
                f"Refrens {suffix}",
                "Default",
                {
                    "base_url": "https://api.refrens.com",
                    "url_key": f"biz-{suffix.lower()}",
                    "app_id": f"app-{suffix}",
                    "app_secret": f"P11_SECRET_{suffix}",
                },
                status="Verified",
                last_verification_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
            accounts.append(account)
        customer_list = state.create_customer_list("Refrens Customers")
        state.add_customers(customer_list.id, customers)
        template = state.save_invoice_template(
            template_id=None,
            name="Refrens Template",
            currency="USD",
            days_until_due=14,
            memo="Memo",
            footer="Footer",
            automatic_tax=False,
            reuse_customer=False,
            items=[("Service", "1", "10", "5")],
            invoice_title="Invoice",
            invoice_subtitle="P11",
            invoice_type="INVOICE",
            customer_note="Thank you",
            terms=["Net 14"],
        )
        task = state.create_task(
            "refrens",
            "Refrens",
            [account.id for account in accounts],
            customer_list.id,
            template.id,
        )
        return state, task, accounts

    @staticmethod
    def _success_transport(calls: list[tuple], *, invoice_ids: list[str] | None = None):
        ids = iter(invoice_ids or ["inv_1", "inv_2", "inv_3"])

        def transport(method, url, headers, body, timeout):
            del timeout
            calls.append((method, url, headers, body))
            path = urlparse(url).path
            if path == "/authentication":
                payload = json.loads((body or b"{}").decode("utf-8"))
                return {"accessToken": f"token-{payload['appId']}"}
            if path.endswith("/invoices"):
                return {"_id": next(ids)}
            raise AssertionError(path)

        return transport

    def test_adapter_enables_exact_p11_execution_and_safety_policy(self):
        adapter = provider_adapter_contract("refrens")
        self.assertIsNotNone(adapter)
        assert adapter is not None and adapter.scheduling_policy is not None
        self.assertTrue(adapter.supports_task_execution)
        self.assertEqual(adapter.task_batch_handler, "_run_refrens_batch")
        self.assertEqual(adapter.profile.executable_capabilities, frozenset({"invoice", "send_invoice", "api_test"}))
        self.assertEqual(adapter.scheduling_policy.requests_per_second_per_account, 1.0)
        self.assertEqual(adapter.scheduling_policy.burst_capacity, 1)
        self.assertEqual(adapter.scheduling_policy.account_cooldown_base_seconds, 5.0)
        self.assertEqual(adapter.scheduling_policy.account_cooldown_cap_seconds, 60.0)
        self.assertEqual(adapter.scheduling_policy.provider_cooldown_base_seconds, 5.0)
        self.assertEqual(adapter.scheduling_policy.provider_cooldown_cap_seconds, 60.0)
        self.assertEqual(adapter.scheduling_policy.account_rate_limit_reasons, frozenset())
        packaged = ProviderManager(ROOT).get_packaged("refrens")
        assert packaged is not None
        self.assertEqual(effective_capabilities(packaged), ("invoice", "send_invoice", "api_test"))

    def test_explicit_name_country_and_india_gst_state_gate_are_fail_closed(self):
        template = InvoiceTemplate(
            id="tpl", name="T", currency="USD", days_until_due=7, automatic_tax=False,
            reuse_customer=False, items=[InvoiceItemTemplate("S", 1, 10, 0)]
        )
        missing = preflight_runtime_inputs(
            provider_id="refrens", template=template, customers=(CustomerRecord("a@example.com"),)
        )
        self.assertFalse(missing.passed)
        self.assertIn("name, country", missing.message)
        india = preflight_runtime_inputs(
            provider_id="refrens", template=template, customers=(CustomerRecord("a@example.com", "Alice", "IN"),)
        )
        self.assertFalse(india.passed)
        self.assertEqual(india.first_issue.code, "refrens-india-gst-state-unavailable")
        calls: list[tuple] = []
        state, task, _accounts = self.task_state([CustomerRecord("india@example.com", "India Customer", "IN")])
        runtime = ProviderRuntime(transport=lambda *args: calls.append(args) or {}, domain_store=self.store)
        with self.assertRaisesRegex(ProviderRuntimeError, "gstState"):
            runtime.make_task_runner(task, state)
        self.assertEqual(calls, [])

    def test_payload_never_substitutes_email_for_missing_name(self):
        state, task, _accounts = self.task_state([CustomerRecord("a@example.com", "Alice", "BD")])
        template = state.invoice_templates[task.invoice_template_id]
        runtime = ProviderRuntime(transport=lambda *_args: {})
        with self.assertRaisesRegex(ProviderRuntimeError, "customer name is required"):
            runtime.build_refrens_invoice_payload(
                template, customer_email="a@example.com", customer_country="BD", customer_name=""
            )
        payload = runtime.build_refrens_invoice_payload(
            template, customer_email="a@example.com", customer_country="BD", customer_name="Alice"
        )
        self.assertEqual(payload["billedTo"], {"name": "Alice", "country": "BD", "email": "a@example.com"})

    def test_task_success_write_ahead_ledgers_auth_invoice_and_provider_id_without_secrets(self):
        calls: list[tuple] = []
        state, task, _accounts = self.task_state([CustomerRecord("a@example.com", "Alice", "BD")])
        runtime = ProviderRuntime(transport=self._success_transport(calls), domain_store=self.store)
        context = _Context(task)
        with patch.object(runtime, "_await_account_rate_slot", return_value=True):
            runtime.make_task_runner(task, state)(context)
        self.assertEqual([urlparse(call[1]).path for call in calls], ["/authentication", "/businesses/biz-a/invoices"])
        invoice_payload = json.loads((calls[1][3] or b"{}").decode("utf-8"))
        self.assertEqual(invoice_payload["billedTo"]["name"], "Alice")
        self.assertEqual(invoice_payload["billedTo"]["country"], "BD")
        self.assertEqual(invoice_payload["email"]["to"], {"email": "a@example.com", "name": "Alice"})
        with closing(sqlite3.connect(self.store.path)) as connection:
            connection.row_factory = sqlite3.Row
            ops = connection.execute(
                "SELECT stage, status, attempt_number, idempotency_key, provider_reference FROM task_delivery_operations ORDER BY rowid"
            ).fetchall()
            recipient = connection.execute(
                "SELECT provider_customer_id, provider_invoice_id, final_result FROM task_delivery_recipients"
            ).fetchone()
        self.assertEqual([row["stage"] for row in ops], ["refrens_authentication", "refrens_invoice_create_email"])
        self.assertEqual([row["status"] for row in ops], [DELIVERY_OPERATION_SUCCEEDED, DELIVERY_OPERATION_SUCCEEDED])
        self.assertEqual([row["attempt_number"] for row in ops], [1, 1])
        self.assertEqual([row["idempotency_key"] for row in ops], ["", ""])
        self.assertEqual(ops[1]["provider_reference"], "inv_1")
        self.assertEqual(recipient["provider_customer_id"], "")
        self.assertEqual(recipient["provider_invoice_id"], "inv_1")
        self.assertEqual(recipient["final_result"], "Succeeded")
        raw_db = self.store.path.read_bytes()
        self.assertNotIn(b"P11_SECRET_A", raw_db)
        self.assertNotIn(b"token-app-A", raw_db)

    def test_authentication_retries_three_times_but_invoice_posts_once(self):
        calls: list[str] = []
        auth_attempts = 0

        def transport(method, url, headers, body, timeout):
            nonlocal auth_attempts
            del headers, body, timeout
            path = urlparse(url).path
            calls.append(path)
            if path == "/authentication":
                auth_attempts += 1
                if auth_attempts < 3:
                    raise ProviderRuntimeError("temporary disconnect", category="network", retryable=True)
                return {"accessToken": "token"}
            if path.endswith("/invoices"):
                return {"_id": "inv_1"}
            raise AssertionError((method, path))

        state, task, _accounts = self.task_state([CustomerRecord("a@example.com", "Alice", "BD")])
        runtime = ProviderRuntime(transport=transport, domain_store=self.store, retry_jitter_source=lambda: 0.0)
        with patch.object(runtime, "_await_account_rate_slot", return_value=True), patch(
            "src.core.provider_runtime.runtime._cooperative_retry_wait", return_value=True
        ):
            runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(calls.count("/authentication"), 3)
        self.assertEqual(sum(path.endswith("/invoices") for path in calls), 1)
        with closing(sqlite3.connect(self.store.path)) as connection:
            auth_rows = connection.execute(
                "SELECT attempt_number, status FROM task_delivery_operations WHERE stage='refrens_authentication' ORDER BY attempt_number"
            ).fetchall()
        self.assertEqual(auth_rows, [(1, DELIVERY_OPERATION_FAILED), (2, DELIVERY_OPERATION_FAILED), (3, DELIVERY_OPERATION_SUCCEEDED)])

    def test_ambiguous_invoice_post_is_uncertain_and_never_blindly_replayed(self):
        calls: list[str] = []

        def transport(method, url, headers, body, timeout):
            del method, headers, body, timeout
            path = urlparse(url).path
            calls.append(path)
            if path == "/authentication":
                return {"accessToken": "token"}
            if path.endswith("/invoices"):
                raise ProviderRuntimeError("read timed out", category="timeout", retryable=True)
            raise AssertionError(path)

        state, task, _accounts = self.task_state([CustomerRecord("a@example.com", "Alice", "BD")])
        runtime = ProviderRuntime(transport=transport, domain_store=self.store)
        with patch.object(runtime, "_await_account_rate_slot", return_value=True):
            with self.assertRaisesRegex(ProviderRuntimeError, "uncertain provider outcome"):
                runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(sum(path.endswith("/invoices") for path in calls), 1)
        with closing(sqlite3.connect(self.store.path)) as connection:
            operation = connection.execute(
                "SELECT status, idempotency_key FROM task_delivery_operations WHERE stage='refrens_invoice_create_email'"
            ).fetchone()
            recipient = connection.execute("SELECT final_result FROM task_delivery_recipients").fetchone()
        self.assertEqual(operation, (DELIVERY_OPERATION_UNCERTAIN, ""))
        self.assertEqual(recipient[0], "Uncertain")
        summary = self.store.delivery_summary(task)
        assert summary is not None
        self.assertEqual(summary.uncertain_recipients, ("a@example.com",))
        self.assertGreater(runtime._provider_cooldown_remaining("refrens"), 0.0)

    def test_missing_invoice_id_is_uncertain_not_definitive_failure(self):
        calls: list[str] = []

        def transport(method, url, headers, body, timeout):
            del method, headers, body, timeout
            path = urlparse(url).path
            calls.append(path)
            if path == "/authentication":
                return {"accessToken": "token"}
            if path.endswith("/invoices"):
                return {"status": "created"}
            raise AssertionError(path)

        state, task, _accounts = self.task_state([CustomerRecord("a@example.com", "Alice", "BD")])
        runtime = ProviderRuntime(transport=transport, domain_store=self.store)
        with patch.object(runtime, "_await_account_rate_slot", return_value=True):
            with self.assertRaisesRegex(ProviderRuntimeError, "uncertain provider outcome"):
                runtime.make_task_runner(task, state)(_Context(task))
        with closing(sqlite3.connect(self.store.path)) as connection:
            operation = connection.execute(
                "SELECT status FROM task_delivery_operations WHERE stage='refrens_invoice_create_email'"
            ).fetchone()
        self.assertEqual(operation[0], DELIVERY_OPERATION_UNCERTAIN)

    def test_two_accounts_keep_frozen_round_robin_without_speculative_failover(self):
        calls: list[tuple[str, str, str]] = []

        def transport(method, url, headers, body, timeout):
            del timeout
            path = urlparse(url).path
            if path == "/authentication":
                payload = json.loads((body or b"{}").decode("utf-8"))
                token = f"token-{payload['appId']}"
                calls.append((path, payload["appId"], ""))
                return {"accessToken": token}
            if path.endswith("/invoices"):
                payload = json.loads((body or b"{}").decode("utf-8"))
                calls.append((path, headers["Authorization"], payload["billedTo"]["email"]))
                return {"_id": f"inv-{payload['billedTo']['email']}"}
            raise AssertionError((method, path))

        state, task, _accounts = self.task_state(
            [CustomerRecord("a@example.com", "A", "BD"), CustomerRecord("b@example.com", "B", "US")],
            account_count=2,
        )
        runtime = ProviderRuntime(transport=transport, domain_store=self.store)
        with patch.object(runtime, "_await_account_rate_slot", return_value=True):
            runtime.make_task_runner(task, state)(_Context(task))
        invoice_calls = [item for item in calls if item[0].endswith("/invoices")]
        self.assertEqual(invoice_calls[0][1:], ("Bearer token-app-A", "a@example.com"))
        self.assertEqual(invoice_calls[1][1:], ("Bearer token-app-B", "b@example.com"))

    def test_restart_resume_excludes_uncertain_recipient_and_processes_pending_only(self):
        state, task, _accounts = self.task_state(
            [CustomerRecord("a@example.com", "A", "BD"), CustomerRecord("b@example.com", "B", "US")]
        )
        first_context = _Context(task)
        first_invoice = True

        def first_transport(method, url, headers, body, timeout):
            nonlocal first_invoice
            del method, headers, body, timeout
            path = urlparse(url).path
            if path == "/authentication":
                return {"accessToken": "token"}
            if path.endswith("/invoices") and first_invoice:
                first_invoice = False
                first_context.stop_flag.set()
                raise ProviderRuntimeError("connection reset", category="network", retryable=True)
            raise AssertionError(path)

        runtime = ProviderRuntime(transport=first_transport, domain_store=self.store)
        runner = runtime.make_task_runner(task, state)
        state.set_task_status(task.id, "Running", "Running")
        with patch.object(runtime, "_await_account_rate_slot", return_value=True):
            runner(first_context)
        state.set_task_status(task.id, "Stopped", "Stopped")

        restarted = self.store.load(self.credentials)
        restarted_state = AppState(domain_store=self.store, credential_store=self.credentials, loaded=restarted)
        restarted_task = restarted_state.tasks[task.id]
        summary = self.store.delivery_summary(restarted_task)
        assert summary is not None
        self.assertEqual(summary.uncertain_recipients, ("a@example.com",))
        self.assertEqual(summary.pending_recipients, ("b@example.com",))

        resumed_invoices: list[str] = []

        def resume_transport(method, url, headers, body, timeout):
            del method, headers, timeout
            path = urlparse(url).path
            if path == "/authentication":
                return {"accessToken": "token"}
            if path.endswith("/invoices"):
                payload = json.loads((body or b"{}").decode("utf-8"))
                resumed_invoices.append(payload["billedTo"]["email"])
                return {"_id": "inv_b"}
            raise AssertionError(path)

        resumed_runtime = ProviderRuntime(transport=resume_transport, domain_store=self.store)
        resume_runner = resumed_runtime.make_task_runner(restarted_task, restarted_state, resume_remaining=True)
        with patch.object(resumed_runtime, "_await_account_rate_slot", return_value=True):
            with self.assertRaisesRegex(ProviderRuntimeError, "Automatic replay is disabled"):
                resume_runner(_Context(restarted_task))
        self.assertEqual(resumed_invoices, ["b@example.com"])

        restarted_task.status = "Stopped"
        with self.assertRaisesRegex(ProviderRuntimeError, "only uncertain provider outcomes remain"):
            resumed_runtime.make_task_runner(restarted_task, restarted_state, resume_remaining=True)

    def test_refrens_429_is_provider_wide_not_account_specific_health(self):
        state, task, accounts = self.task_state([CustomerRecord("a@example.com", "Alice", "BD")])
        del state, task
        runtime = ProviderRuntime()
        account = ProviderRuntime._snapshot  # keep source-contract imports untouched
        del account
        snapshot = accounts[0]
        from src.core.provider_runtime import AccountSnapshot
        account_snapshot = AccountSnapshot(snapshot.id, snapshot.name, snapshot.mode, dict(snapshot.credentials))
        messages = runtime._record_scheduler_failure(
            "refrens",
            account_snapshot,
            ProviderRuntimeError("slow down", category="rate-limit", retryable=True, http_status=429, retry_after_seconds=7),
        )
        self.assertTrue(messages)
        self.assertGreaterEqual(runtime._provider_cooldown_remaining("refrens"), 7.0 - 0.05)
        blocked, account_cooldown = runtime._account_health_status("refrens", account_snapshot.id)
        self.assertEqual(blocked, "")
        self.assertEqual(account_cooldown, 0.0)

    def test_ui_source_disables_uncertain_only_refrens_resume_without_new_page(self):
        source = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertIn('task.provider_id == "refrens"', source)
        self.assertIn("Only uncertain Refrens provider outcomes remain", source)
        self.assertIn("Automatic Resume is disabled to prevent duplicate invoice/email delivery", source)
        self.assertNotIn("Delivery Ledger Page", source)


if __name__ == "__main__":
    unittest.main()
