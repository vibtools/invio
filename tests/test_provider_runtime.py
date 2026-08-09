from __future__ import annotations

import json
import threading
import unittest
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from src.core.provider_runtime import ProviderRuntime, ProviderRuntimeError
from src.core.provider_runtime.runtime import _idempotency_key
from src.customers.models import CustomerRecord
from src.core.state import AppState
from src.tasks.models import TaskExecutionSnapshot


@dataclass
class _Context:
    task: object

    def __post_init__(self):
        self.pause_gate = threading.Event()
        self.pause_gate.set()
        self.stop_flag = threading.Event()
        self.progress_events: list[tuple[int, int, int, str]] = []
        self.logs: list[str] = []

    def progress(self, processed: int, success: int, failed: int, message: str) -> None:
        self.progress_events.append((processed, success, failed, message))

    def log(self, message: str) -> None:
        self.logs.append(message)


class ProviderRuntimeTests(unittest.TestCase):
    def test_api_test_support_is_executable_adapter_based(self):
        runtime = ProviderRuntime(transport=lambda *_args: {})
        self.assertTrue(runtime.supports_api_test("stripe"))
        self.assertTrue(runtime.supports_api_test("refrens"))
        self.assertFalse(runtime.supports_api_test("external-provider"))

    def test_stripe_api_test_is_mode_aware_and_uses_real_permission_requests(self):
        calls: list[tuple[str, str]] = []

        def transport(method, url, headers, body, timeout):
            calls.append((method, urlparse(url).path))
            return {"data": []}

        runtime = ProviderRuntime(transport=transport)
        message = runtime.test_account(
            "stripe",
            {"secret_key": "sk_test_contractkey"},
            mode="Test",
        )
        self.assertEqual(message, "Stripe API connection verified.")
        self.assertEqual(calls, [("GET", "/v1/customers"), ("GET", "/v1/invoices")])

    def test_stripe_api_test_rejects_mode_mismatch_before_network(self):
        calls = []
        runtime = ProviderRuntime(transport=lambda *args: calls.append(args) or {})
        with self.assertRaisesRegex(ProviderRuntimeError, "mode is Live"):
            runtime.test_account("stripe", {"secret_key": "sk_test_contractkey"}, mode="Live")
        self.assertEqual(calls, [])

    def test_refrens_api_test_authenticates_and_checks_invoice_access(self):
        calls: list[tuple[str, str]] = []

        def transport(method, url, headers, body, timeout):
            calls.append((method, urlparse(url).path))
            if urlparse(url).path == "/authentication":
                return {"accessToken": "token"}
            if urlparse(url).path == "/businesses/biz/invoices":
                return {"data": []}
            raise AssertionError(f"Unexpected request: {method} {url}")

        runtime = ProviderRuntime(transport=transport)
        message = runtime.test_account(
            "refrens",
            {"base_url": "https://api.refrens.com", "url_key": "biz", "app_id": "app", "app_secret": "secret"},
            mode="Default",
        )
        self.assertEqual(message, "Refrens API connection verified.")
        self.assertEqual(calls, [("POST", "/authentication"), ("GET", "/businesses/biz/invoices")])

    def test_api_test_without_runtime_adapter_fails_closed(self):
        runtime = ProviderRuntime(transport=lambda *_args: {})
        with self.assertRaisesRegex(ProviderRuntimeError, "No built-in API-test adapter"):
            runtime.test_account("external-provider", {"token": "secret"}, mode="Default")

    def _stripe_state(self, emails: list[str] | None = None):
        state = AppState()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_contractkey"}, status="Verified"
        )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, emails or ["customer@example.com"])
        template = state.save_invoice_template(
            template_id=None,
            name="Monthly",
            currency="usd",
            days_until_due=30,
            memo="Invoice note",
            footer="Footer",
            automatic_tax=False,
            reuse_customer=True,
            invoice_title="Service Invoice",
            invoice_subtitle="August",
            customer_note="Thank you",
            terms=["Net 30"],
            items=[("Service", "2", "10.25", "0")],
        )
        task = state.create_task("stripe", "Stripe", [account.id], customer_list.id, template.id)
        return state, task

    def test_stripe_task_runner_creates_finalizes_and_sends_invoice(self):
        calls: list[tuple[str, str, dict[str, str], bytes | None]] = []

        def transport(method, url, headers, body, timeout):
            calls.append((method, url, headers, body))
            path = urlparse(url).path
            if method == "GET" and path.endswith("/customers"):
                return {"data": []}
            if method == "POST" and path.endswith("/customers"):
                return {"id": "cus_1"}
            if method == "POST" and path.endswith("/invoices"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/invoiceitems"):
                return {"id": "ii_1"}
            if method == "POST" and path.endswith("/finalize"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/send"):
                return {"id": "in_1", "status": "open"}
            raise AssertionError(f"Unexpected request: {method} {url}")

        state, task = self._stripe_state()
        runtime = ProviderRuntime(transport=transport)
        runner = runtime.make_task_runner(task, state)
        context = _Context(task)
        runner(context)

        paths = [urlparse(url).path for _method, url, _headers, _body in calls]
        self.assertIn("/v1/invoices", paths)
        self.assertIn("/v1/invoiceitems", paths)
        self.assertIn("/v1/invoices/in_1/finalize", paths)
        self.assertIn("/v1/invoices/in_1/send", paths)
        customer_call = next(call for call in calls if call[0] == "POST" and urlparse(call[1]).path == "/v1/customers")
        customer_form = parse_qs((customer_call[3] or b"").decode("utf-8"))
        self.assertEqual(customer_form, {"email": ["customer@example.com"]})
        invoice_call = next(call for call in calls if call[0] == "POST" and urlparse(call[1]).path == "/v1/invoices")
        invoice_form = parse_qs((invoice_call[3] or b"").decode("utf-8"))
        self.assertEqual(invoice_form["currency"], ["usd"])
        self.assertEqual(invoice_form["collection_method"], ["send_invoice"])
        self.assertEqual(invoice_form["days_until_due"], ["30"])
        self.assertEqual(context.progress_events[-1][:3], (1, 1, 0))
        self.assertTrue(any("completed successfully" in message.lower() for message in context.logs))

    def test_stripe_retry_failed_retries_only_failed_recipient(self):
        failed_once = {"bad@example.com"}
        send_emails: list[str] = []
        customer_by_id: dict[str, str] = {}
        current_email = {"value": ""}

        def transport(method, url, headers, body, timeout):
            path = urlparse(url).path
            form = parse_qs((body or b"").decode("utf-8"))
            if method == "GET" and path.endswith("/customers"):
                return {"data": []}
            if method == "POST" and path.endswith("/customers"):
                email = form["email"][0]
                current_email["value"] = email
                cid = "cus_" + str(len(customer_by_id) + 1)
                customer_by_id[cid] = email
                return {"id": cid}
            if method == "POST" and path.endswith("/invoices"):
                current_email["value"] = customer_by_id[form["customer"][0]]
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/invoiceitems"):
                return {"id": "ii_1"}
            if method == "POST" and path.endswith("/finalize"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/send"):
                email = current_email["value"]
                send_emails.append(email)
                if email in failed_once:
                    failed_once.remove(email)
                    raise ProviderRuntimeError("temporary provider failure")
                return {"id": "in_1"}
            raise AssertionError(f"Unexpected request: {method} {url}")

        state, task = self._stripe_state(["good@example.com", "bad@example.com"])
        runtime = ProviderRuntime(transport=transport)
        with self.assertRaises(ProviderRuntimeError):
            runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(send_emails, ["good@example.com", "bad@example.com"])
        task.success = 1
        task.failed = 1
        task.processed = 2
        task.status = "Failed"
        runtime.make_task_runner(task, state, retry_failed=True)(_Context(task))
        self.assertEqual(send_emails, ["good@example.com", "bad@example.com", "bad@example.com"])

    def test_refrens_payload_maps_template_only_when_required_customer_country_exists(self):
        state, task = self._stripe_state()
        template = state.invoice_templates[task.invoice_template_id]
        template.invoice_type = "BOS"
        template.items[0].tax_rate = type(template.items[0].tax_rate)("5")
        runtime = ProviderRuntime(transport=lambda *_args: {})
        payload = runtime.build_refrens_invoice_payload(
            template,
            customer_email="a@example.com",
            customer_country="BD",
        )
        self.assertEqual(payload["invoiceType"], "BOS")
        self.assertEqual(payload["currency"], "USD")
        self.assertEqual(payload["billedTo"]["country"], "BD")
        self.assertEqual(payload["items"][0]["taxRate"], 5.0)
        self.assertIn("Thank you", payload["terms"])

    def test_refrens_create_and_send_uses_documented_create_email_payload(self):
        calls = []

        def transport(method, url, headers, body, timeout):
            calls.append((method, url, headers, body))
            path = urlparse(url).path
            if path == "/authentication":
                return {"accessToken": "token"}
            if path == "/businesses/biz/invoices":
                payload = json.loads((body or b"{}").decode("utf-8"))
                self.assertEqual(payload["email"]["to"]["email"], "a@example.com")
                self.assertEqual(payload["billedTo"]["country"], "BD")
                return {"_id": "inv_1"}
            raise AssertionError(f"Unexpected request: {method} {url}")

        state, task = self._stripe_state()
        template = state.invoice_templates[task.invoice_template_id]
        runtime = ProviderRuntime(transport=transport)
        payload = runtime.build_refrens_invoice_payload(
            template, customer_email="a@example.com", customer_country="BD"
        )
        created = runtime.create_and_send_refrens_invoice(
            {"base_url": "https://api.refrens.com", "url_key": "biz", "app_id": "app", "app_secret": "secret"},
            payload,
            customer_email="a@example.com",
        )
        self.assertEqual(created["_id"], "inv_1")
        self.assertEqual(len(calls), 2)

    def test_refrens_task_runner_blocks_before_network_without_required_country(self):
        called = []
        state = AppState()
        account = state.add_account(
            "refrens",
            "Refrens",
            "Primary",
            "Live",
            {"base_url": "https://api.refrens.com", "url_key": "biz", "app_id": "app", "app_secret": "secret"},
            status="Verified",
        )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, ["a@example.com"])
        template = state.save_invoice_template(
            template_id=None,
            name="Invoice",
            currency="USD",
            days_until_due=7,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "1", "10", "0")],
        )
        task = state.create_task("refrens", "Refrens", [account.id], customer_list.id, template.id)
        runtime = ProviderRuntime(transport=lambda *args: called.append(args) or {})
        with self.assertRaisesRegex(ProviderRuntimeError, r"P11"):
            runtime.make_task_runner(task, state)
        self.assertEqual(called, [])


    def test_task_snapshot_carries_customer_records_while_stripe_email_view_is_unchanged(self):
        state, task = self._stripe_state()
        customer_list = state.customer_lists[task.customer_list_id]
        state.add_customers(
            customer_list.id,
            [CustomerRecord("customer@example.com", "Explicit Name", "US")],
        )
        snapshot = ProviderRuntime._snapshot(task, state)
        self.assertEqual(snapshot.customer_emails, ("customer@example.com",))
        # P05 freezes customer data at Task creation. Later Customer List
        # enrichment must not silently alter this Task's approved run.
        self.assertEqual(snapshot.customers[0].name, "")
        self.assertEqual(snapshot.customers[0].country, "")

        state.close_task(task.id)
        new_task = state.create_task(
            "stripe",
            "Stripe",
            [next(iter(state.accounts))],
            customer_list.id,
            next(iter(state.invoice_templates)),
        )
        new_snapshot = ProviderRuntime._snapshot(new_task, state)
        self.assertEqual(new_snapshot.customers[0].name, "Explicit Name")
        self.assertEqual(new_snapshot.customers[0].country, "US")

    def test_refrens_task_runner_remains_disabled_even_when_explicit_customer_data_exists(self):
        called = []
        state = AppState()
        account = state.add_account(
            "refrens",
            "Refrens",
            "Primary",
            "Live",
            {"base_url": "https://api.refrens.com", "url_key": "biz", "app_id": "app", "app_secret": "secret"},
            status="Verified",
        )
        customer_list = state.create_customer_list("Customers")
        state.add_customers(customer_list.id, [CustomerRecord("a@example.com", "Alice", "BD")])
        template = state.save_invoice_template(
            template_id=None,
            name="Invoice",
            currency="USD",
            days_until_due=7,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "1", "10", "0")],
        )
        task = state.create_task("refrens", "Refrens", [account.id], customer_list.id, template.id)
        runtime = ProviderRuntime(transport=lambda *args: called.append(args) or {})
        with self.assertRaisesRegex(ProviderRuntimeError, r"P11"):
            runtime.make_task_runner(task, state)
        self.assertEqual(called, [])

    def test_task_snapshot_preserves_old_positional_email_constructor(self):
        from src.core.provider_runtime import AccountSnapshot, TaskSnapshot
        state, task = self._stripe_state()
        template = state.invoice_templates[task.invoice_template_id]
        snapshot = TaskSnapshot(
            task.id, task.name, task.provider_id,
            (AccountSnapshot("acct", "A", "Test", {}),),
            ("legacy@example.com",), template,
        )
        self.assertEqual(snapshot.customer_emails, ("legacy@example.com",))
        self.assertEqual(snapshot.customers[0].name, "")
        self.assertEqual(snapshot.customers[0].country, "")

    def test_refrens_country_rejects_non_ascii_two_letter_values(self):
        state, task = self._stripe_state()
        template = state.invoice_templates[task.invoice_template_id]
        runtime = ProviderRuntime(transport=lambda *_args: {})
        with self.assertRaisesRegex(ProviderRuntimeError, "ISO 3166-1 alpha-2"):
            runtime.build_refrens_invoice_payload(
                template, customer_email="a@example.com", customer_country="éé"
            )

if __name__ == "__main__":
    unittest.main()


class P05ProviderRuntimeSnapshotTests(unittest.TestCase):
    def _stripe_state(self):
        state = AppState()
        first = state.add_account(
            "stripe", "Stripe", "First", "Test", {"secret_key": "sk_test_P05_FIRST"}, status="Verified"
        )
        second = state.add_account(
            "stripe", "Stripe", "Second", "Test", {"secret_key": "sk_test_P05_SECOND"}, status="Verified"
        )
        customer_list = state.create_customer_list("Customers")
        state.add_customers(
            customer_list.id,
            [
                CustomerRecord("one@example.com", "One", "US"),
                CustomerRecord("two@example.com", "Two", "BD"),
            ],
        )
        template = state.save_invoice_template(
            template_id=None,
            name="Original",
            currency="USD",
            days_until_due=30,
            memo="Original memo",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Original item", "1", "10", "0")],
            terms=["Original term"],
        )
        task = state.create_task("stripe", "Stripe", [second.id, first.id], customer_list.id, template.id)
        return state, task, customer_list, template, first, second

    def test_runtime_snapshot_uses_creation_time_customers_template_and_account_order(self):
        state, task, customer_list, template, first, second = self._stripe_state()
        state.add_customers(customer_list.id, [CustomerRecord("three@example.com", "Three", "GB")])
        state.save_invoice_template(
            template_id=template.id,
            name=template.name,
            currency="EUR",
            days_until_due=14,
            memo="Edited memo",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Edited item", "1", "20", "0")],
            terms=["Edited term"],
        )
        snapshot = ProviderRuntime._snapshot(task, state)
        self.assertEqual(snapshot.customer_emails, ("one@example.com", "two@example.com"))
        self.assertEqual(snapshot.template.currency, "USD")
        self.assertEqual(snapshot.template.memo, "Original memo")
        self.assertEqual(snapshot.template.items[0].description, "Original item")
        self.assertEqual(snapshot.template.terms, ["Original term"])
        self.assertEqual([account.id for account in snapshot.accounts], [second.id, first.id])

    def test_legacy_task_without_trustworthy_snapshot_is_blocked(self):
        state, task, _customer_list, _template, _first, _second = self._stripe_state()
        task.execution_snapshot = TaskExecutionSnapshot.legacy_unavailable(
            provider_id=task.provider_id,
            account_ids=task.account_ids,
        )
        runtime = ProviderRuntime(transport=lambda *_args: {})
        with self.assertRaisesRegex(ProviderRuntimeError, "predates immutable execution snapshots"):
            runtime.make_task_runner(task, state)

    def test_task_id_remains_canonical_stripe_idempotency_run_identity(self):
        state, task, _customer_list, _template, _first, _second = self._stripe_state()
        key = _idempotency_key(task.id, task.execution_snapshot.customers[0].email, "send")
        self.assertTrue(key.startswith(f"invio:{task.id}:"))
        self.assertTrue(task.has_immutable_execution_snapshot)

    def test_runtime_blocks_snapshot_account_order_drift(self):
        state, task, _customer_list, _template, _first, _second = self._stripe_state()
        task.account_ids.reverse()
        with self.assertRaisesRegex(ProviderRuntimeError, "snapshot account order"):
            ProviderRuntime._snapshot(task, state)

    def test_runtime_blocks_task_total_drift_from_snapshot(self):
        state, task, _customer_list, _template, _first, _second = self._stripe_state()
        task.total += 1
        with self.assertRaisesRegex(ProviderRuntimeError, "task total"):
            ProviderRuntime._snapshot(task, state)


class P07ProviderRuntimeResendSafetyTests(unittest.TestCase):
    def _stripe_state(self, emails: list[str]):
        state = AppState()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_p07"}, status="Verified"
        )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, emails)
        template = state.save_invoice_template(
            template_id=None,
            name="P07",
            currency="usd",
            days_until_due=30,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "1", "10", "0")],
        )
        task = state.create_task("stripe", "Stripe", [account.id], customer_list.id, template.id)
        return state, task

    @staticmethod
    def _transport(send_handler):
        customer_by_id: dict[str, str] = {}
        current_email = {"value": ""}

        def transport(method, url, headers, body, timeout):
            path = urlparse(url).path
            form = parse_qs((body or b"").decode("utf-8"))
            if method == "GET" and path.endswith("/customers"):
                return {"data": []}
            if method == "POST" and path.endswith("/customers"):
                email = form["email"][0]
                current_email["value"] = email
                customer_id = f"cus_{len(customer_by_id) + 1}"
                customer_by_id[customer_id] = email
                return {"id": customer_id}
            if method == "POST" and path.endswith("/invoices"):
                current_email["value"] = customer_by_id[form["customer"][0]]
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/invoiceitems"):
                return {"id": "ii_1"}
            if method == "POST" and path.endswith("/finalize"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/send"):
                return send_handler(current_email["value"])
            raise AssertionError(f"Unexpected request: {method} {url}")

        return transport

    @staticmethod
    def _apply_summary(task, summary, status: str) -> None:
        task.processed = summary.processed
        task.success = summary.success
        task.failed = summary.failed
        task.status = status

    def test_stopped_resume_remaining_excludes_successful_recipients(self):
        state, task = self._stripe_state(["a@example.com", "b@example.com", "c@example.com", "d@example.com"])
        sent: list[str] = []
        attempts: dict[str, int] = {}
        context = _Context(task)

        def on_send(email: str):
            sent.append(email)
            attempts[email] = attempts.get(email, 0) + 1
            if email == "b@example.com" and attempts[email] == 1:
                raise ProviderRuntimeError("temporary failure")
            if email == "c@example.com" and attempts[email] == 1:
                context.stop_flag.set()
            return {"id": "in_1"}

        runtime = ProviderRuntime(transport=self._transport(on_send))
        runtime.make_task_runner(task, state)(context)
        summary = runtime.delivery_summary(task)
        self.assertIsNotNone(summary)
        self.assertTrue(summary.continuation_safe)
        self.assertEqual(summary.failed_recipients, ("b@example.com",))
        self.assertEqual(summary.pending_recipients, ("d@example.com",))
        self.assertEqual((summary.processed, summary.success, summary.failed, summary.remaining), (3, 2, 1, 1))

        self._apply_summary(task, summary, "Stopped")
        resume_context = _Context(task)
        runtime.make_task_runner(task, state, resume_remaining=True)(resume_context)
        self.assertEqual(
            sent,
            ["a@example.com", "b@example.com", "c@example.com", "b@example.com", "d@example.com"],
        )
        self.assertEqual(sent.count("a@example.com"), 1)
        self.assertEqual(sent.count("c@example.com"), 1)
        final = runtime.delivery_summary(task)
        self.assertTrue(final.continuation_safe)
        self.assertEqual((final.processed, final.success, final.failed, final.remaining), (4, 4, 0, 0))


    def test_stop_after_last_success_keeps_safe_empty_continuation(self):
        state, task = self._stripe_state(["a@example.com"])
        context = _Context(task)

        def on_send(_email: str):
            context.stop_flag.set()
            return {"id": "in_1"}

        runtime = ProviderRuntime(transport=self._transport(on_send))
        runtime.make_task_runner(task, state)(context)
        summary = runtime.delivery_summary(task)
        self.assertIsNotNone(summary)
        self.assertTrue(summary.continuation_safe)
        self.assertEqual(summary.failed_recipients, ())
        self.assertEqual(summary.pending_recipients, ())
        self.assertEqual((summary.processed, summary.success, summary.failed, summary.remaining), (1, 1, 0, 0))
        self.assertFalse(summary.resume_remaining_available)

    def test_repeated_retry_failed_shrinks_to_unresolved_failure_set(self):
        state, task = self._stripe_state(["a@example.com", "b@example.com", "c@example.com"])
        sent: list[str] = []
        attempts: dict[str, int] = {}

        def on_send(email: str):
            sent.append(email)
            attempts[email] = attempts.get(email, 0) + 1
            if email == "b@example.com" and attempts[email] == 1:
                raise ProviderRuntimeError("b first failure")
            if email == "c@example.com" and attempts[email] <= 2:
                raise ProviderRuntimeError("c remains failed")
            return {"id": "in_1"}

        runtime = ProviderRuntime(transport=self._transport(on_send))
        with self.assertRaises(ProviderRuntimeError):
            runtime.make_task_runner(task, state)(_Context(task))
        first = runtime.delivery_summary(task)
        self.assertEqual(first.failed_recipients, ("b@example.com", "c@example.com"))
        self._apply_summary(task, first, "Failed")

        with self.assertRaises(ProviderRuntimeError):
            runtime.make_task_runner(task, state, retry_failed=True)(_Context(task))
        second = runtime.delivery_summary(task)
        self.assertEqual(second.failed_recipients, ("c@example.com",))
        self.assertEqual((second.processed, second.success, second.failed), (3, 2, 1))
        self._apply_summary(task, second, "Failed")

        runtime.make_task_runner(task, state, retry_failed=True)(_Context(task))
        third = runtime.delivery_summary(task)
        self.assertEqual(third.failed_recipients, ())
        self.assertEqual((third.processed, third.success, third.failed), (3, 3, 0))
        self.assertEqual(
            sent,
            ["a@example.com", "b@example.com", "c@example.com", "b@example.com", "c@example.com", "c@example.com"],
        )

    def test_retry_failed_is_fail_closed_after_runtime_restart(self):
        state, task = self._stripe_state(["a@example.com", "b@example.com"])

        def on_send(email: str):
            if email == "b@example.com":
                raise ProviderRuntimeError("failure")
            return {"id": "in_1"}

        first_runtime = ProviderRuntime(transport=self._transport(on_send))
        with self.assertRaises(ProviderRuntimeError):
            first_runtime.make_task_runner(task, state)(_Context(task))
        summary = first_runtime.delivery_summary(task)
        self._apply_summary(task, summary, "Failed")

        calls: list[object] = []
        restarted_runtime = ProviderRuntime(transport=lambda *args: calls.append(args) or {})
        with self.assertRaisesRegex(ProviderRuntimeError, "exact failed recipient set"):
            restarted_runtime.make_task_runner(task, state, retry_failed=True)
        self.assertEqual(calls, [])

    def test_resume_remaining_is_fail_closed_after_runtime_restart(self):
        state, task = self._stripe_state(["a@example.com", "b@example.com"])
        context = _Context(task)

        def on_send(email: str):
            if email == "a@example.com":
                context.stop_flag.set()
            return {"id": "in_1"}

        first_runtime = ProviderRuntime(transport=self._transport(on_send))
        first_runtime.make_task_runner(task, state)(context)
        summary = first_runtime.delivery_summary(task)
        self.assertEqual(summary.pending_recipients, ("b@example.com",))
        self._apply_summary(task, summary, "Stopped")

        calls: list[object] = []
        restarted_runtime = ProviderRuntime(transport=lambda *args: calls.append(args) or {})
        with self.assertRaisesRegex(ProviderRuntimeError, "exact continuation recipient set"):
            restarted_runtime.make_task_runner(task, state, resume_remaining=True)
        self.assertEqual(calls, [])

    def test_unexpected_runtime_exception_isolated_per_recipient_with_safe_progress(self):
        state, task = self._stripe_state(["a@example.com", "b@example.com"])

        def on_send(_email: str):
            raise RuntimeError("unexpected execution defect")

        runtime = ProviderRuntime(transport=self._transport(on_send))
        context = _Context(task)
        with self.assertRaisesRegex(ProviderRuntimeError, r"2 recipient\(s\) failed"):
            runtime.make_task_runner(task, state)(context)
        summary = runtime.delivery_summary(task)
        self.assertIsNotNone(summary)
        self.assertTrue(summary.continuation_safe)
        self.assertEqual(summary.failed_recipients, ("a@example.com", "b@example.com"))
        self.assertEqual((summary.processed, summary.success, summary.failed), (2, 0, 2))
        self.assertEqual(context.progress_events[-1][:3], (2, 0, 2))
        task.status = "Failed"
        task.processed, task.success, task.failed = 2, 0, 2
        self.assertIsNotNone(runtime.make_task_runner(task, state, retry_failed=True))

    def test_full_start_is_rejected_for_non_pristine_or_terminal_task(self):
        state, task = self._stripe_state(["a@example.com"])
        runtime = ProviderRuntime(transport=lambda *_args: {})
        task.status = "Completed"
        task.processed = 1
        task.success = 1
        with self.assertRaisesRegex(ProviderRuntimeError, "pristine Ready Task"):
            runtime.make_task_runner(task, state)

    def test_duplicate_full_runner_creation_is_blocked_before_network(self):
        state, task = self._stripe_state(["a@example.com"])
        calls: list[object] = []
        runtime = ProviderRuntime(transport=lambda *args: calls.append(args) or {})
        runtime.make_task_runner(task, state)
        with self.assertRaisesRegex(ProviderRuntimeError, "duplicate full Start"):
            runtime.make_task_runner(task, state)
        self.assertEqual(calls, [])
