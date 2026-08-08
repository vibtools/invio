from __future__ import annotations

import json
import threading
import unittest
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from src.core.provider_runtime import ProviderRuntime, ProviderRuntimeError
from src.core.state import AppState


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
    def _stripe_state(self, emails: list[str] | None = None):
        state = AppState()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_contractkey"}
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
        with self.assertRaisesRegex(ProviderRuntimeError, r"billedTo\.country"):
            runtime.make_task_runner(task, state)
        self.assertEqual(called, [])


if __name__ == "__main__":
    unittest.main()
