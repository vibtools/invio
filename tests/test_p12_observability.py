from __future__ import annotations

import base64
import csv
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from src.core.observability import (
    StructuredLogEvent,
    atomic_write_csv,
    mask_email,
    redact_sensitive_text,
    spreadsheet_safe_text,
)
from src.core.provider_runtime import ProviderRuntime
from src.core.state import AppState
from src.core.storage import CredentialStore, DomainStore


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
        self.progress_events: list[tuple[int, int, int, str]] = []
        self.logs: list[str] = []
        self.structured: list[tuple[str, str, str]] = []

    def progress(self, processed: int, success: int, failed: int, message: str) -> None:
        self.progress_events.append((processed, success, failed, message))

    def log(self, message: str) -> None:
        self.logs.append(message)

    def structured_log(self, severity: str, category: str, message: str) -> None:
        self.structured.append((severity, category, message))


class P12ObservabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db_path = self.root / "domain.sqlite3"
        self.credentials = CredentialStore(_Keyring())
        self.store = DomainStore(self.db_path)

    def _state(self) -> AppState:
        return AppState(
            domain_store=self.store,
            credential_store=self.credentials,
            loaded=self.store.load(self.credentials),
        )

    def _stripe_task(self, emails: list[str]):
        state = self._state()
        account = state.add_account(
            "stripe",
            "Stripe",
            "Support Account",
            "Test",
            {"secret_key": "sk_test_P12_SUPER_SECRET"},
            status="Verified",
        )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, emails)
        template = state.save_invoice_template(
            template_id=None,
            name="Support Template",
            currency="USD",
            days_until_due=30,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "1", "10", "0")],
        )
        task = state.create_task(
            "stripe",
            "Stripe",
            [account.id],
            customer_list.id,
            template.id,
        )
        return state, task, account

    @staticmethod
    def _success_transport(method, url, headers, body, timeout):
        del timeout
        path = urlparse(url).path
        form = parse_qs((body or b"").decode("utf-8"))
        if method == "GET" and path.endswith("/customers"):
            return {"data": []}
        if method == "POST" and path.endswith("/customers"):
            return {"id": "cus_support"}
        if method == "POST" and path.endswith("/invoices"):
            self_customer = form.get("customer", [""])[0]
            if self_customer:
                return {"id": "in_support"}
        if method == "POST" and path.endswith("/invoiceitems"):
            return {"id": "ii_support"}
        if method == "POST" and (path.endswith("/finalize") or path.endswith("/send")):
            return {"id": "in_support"}
        raise AssertionError(f"Unexpected request: {method} {url}")

    def test_central_redactor_masks_provider_secrets_auth_tokens_and_log_email(self):
        text = (
            "send user.name@example.com secret sk_test_ABC123 app_secret=REFRENS_SECRET "
            "Authorization: Bearer abc.def.ghi api_key='AGILED_KEY' Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="
        )
        safe = redact_sensitive_text(
            text,
            secret_values=("REFRENS_SECRET", "AGILED_KEY"),
            mask_emails=True,
        )
        self.assertIn("u***@example.com", safe)
        self.assertNotIn("sk_test_ABC123", safe)
        self.assertNotIn("REFRENS_SECRET", safe)
        self.assertNotIn("AGILED_KEY", safe)
        self.assertNotIn("abc.def.ghi", safe)
        self.assertNotIn("QWxhZGRpbjpvcGVuIHNlc2FtZQ==", safe)
        self.assertIn("***REDACTED***", safe)
        self.assertEqual(mask_email("a@example.com"), "a***@example.com")

    def test_structured_log_contract_accepts_only_approved_severity_and_category(self):
        event = StructuredLogEvent("warning", "provider", "retry", "task_1")
        self.assertEqual((event.severity, event.category), ("WARNING", "PROVIDER"))
        with self.assertRaises(ValueError):
            StructuredLogEvent("DEBUG", "PROVIDER", "x")
        with self.assertRaises(ValueError):
            StructuredLogEvent("INFO", "NETWORK", "x")

    def test_formula_injection_is_neutralized_for_csv_text(self):
        for value in ("=1+1", "+SUM(A1:A2)", "-2+3", "@cmd", "\t=1", "\r=1", "\n=1", "  =1"):
            self.assertTrue(spreadsheet_safe_text(value).startswith("'"), value)
        self.assertEqual(spreadsheet_safe_text("normal@example.com"), "normal@example.com")

        target = self.root / "safe.csv"
        atomic_write_csv(target, [["Recipient", "Attempts"], ["=HYPERLINK(\"x\")", 2]])
        with target.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(rows[1][0], "'=HYPERLINK(\"x\")")
        self.assertEqual(rows[1][1], "2")

    def test_recipient_report_is_ledger_backed_and_distinguishes_provider_acceptance_from_delivery(self):
        state, task, account = self._stripe_task(["person@example.com"])
        runtime = ProviderRuntime(transport=self._success_transport, domain_store=self.store)
        context = _Context(task)
        runtime.make_task_runner(task, state)(context)

        records = self.store.recipient_delivery_report()
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.task_id, task.id)
        self.assertEqual(record.recipient_email, "person@example.com")
        self.assertEqual(record.provider_id, "stripe")
        self.assertEqual(record.safe_status, "Provider Accepted")
        self.assertEqual(record.attempts, 1)
        self.assertIn(account.id, record.account_reference)
        self.assertEqual(record.provider_invoice_reference, "in_support")
        self.assertEqual(record.last_stage, "invoice_send")
        self.assertEqual(record.provider_send_acceptance, "Accepted")
        self.assertEqual(record.email_delivery, "Not independently confirmed")
        self.assertTrue(any(category == "PROVIDER" for _severity, category, _message in context.structured))

    def test_pending_report_uses_planned_primary_account_reference(self):
        state, task, account = self._stripe_task(["pending@example.com"])
        run = self.store.begin_delivery_run(task, execution_mode="First Run", recipients=("pending@example.com",))
        self.store.finish_delivery_run(run.run_id, status="Stopped")
        record = self.store.recipient_delivery_report()[0]
        self.assertEqual(record.safe_status, "Pending")
        self.assertEqual(record.attempts, 0)
        self.assertIn(account.id, record.account_reference)
        self.assertIn("[planned]", record.account_reference)
        self.assertEqual(record.provider_send_acceptance, "Not Reached")

    def test_clear_delivery_history_deletes_only_closed_task_ledger(self):
        state1, task1, _account1 = self._stripe_task(["closed@example.com"])
        runtime = ProviderRuntime(transport=self._success_transport, domain_store=self.store)
        runtime.make_task_runner(task1, state1)(_Context(task1))
        summary = runtime.delivery_summary(task1)
        state1.set_task_progress(task1.id, processed=summary.processed, success=summary.success, failed=summary.failed)
        state1.set_task_status(task1.id, "Running", "finishing")
        state1.set_task_status(task1.id, "Completed", "done")
        state1.close_task(task1.id)

        state2, task2, _account2 = self._stripe_task(["active@example.com"])
        run2 = self.store.begin_delivery_run(task2, execution_mode="First Run", recipients=("active@example.com",))
        self.store.finish_delivery_run(run2.run_id, status="Stopped")

        tasks_cleared, runs_cleared = self.store.clear_closed_delivery_history()
        self.assertEqual(tasks_cleared, 1)
        self.assertEqual(runs_cleared, 1)
        remaining = self.store.recipient_delivery_report()
        self.assertEqual({row.task_id for row in remaining}, {task2.id})
        with closing(sqlite3.connect(self.db_path)) as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM task_delivery_runs WHERE task_id=?", (task1.id,)).fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM task_delivery_runs WHERE task_id=?", (task2.id,)).fetchone()[0],
                1,
            )

    def test_uncertain_send_is_reported_without_claiming_email_delivery(self):
        state, task, account = self._stripe_task(["uncertain@example.com"])
        run = self.store.begin_delivery_run(task, execution_mode="First Run", recipients=("uncertain@example.com",))
        self.store.begin_delivery_operation(
            run_id=run.run_id, recipient_ordinal=0, attempt_number=1, stage="invoice_send",
            account_id=account.id, account_name=account.name, idempotency_key="invio:task:send",
        )
        self.store.finish_delivery_operation(
            run_id=run.run_id, recipient_ordinal=0, attempt_number=1, stage="invoice_send",
            status="Uncertain", error_class="TimeoutError", error_code="timeout", error_message="timed out",
        )
        self.store.finish_delivery_recipient(
            run_id=run.run_id, recipient_ordinal=0, final_result="Uncertain", stage="invoice_send",
            attempt_number=1, error_class="TimeoutError", error_code="timeout", error_message="timed out",
        )
        self.store.finish_delivery_run(run.run_id, status="Failed")
        record = self.store.recipient_delivery_report()[0]
        self.assertEqual(record.safe_status, "Uncertain")
        self.assertEqual(record.provider_send_acceptance, "Uncertain")
        self.assertEqual(record.email_delivery, "Not independently confirmed")
        self.assertEqual(record.error_code, "timeout")

    def test_failed_send_is_not_reported_as_provider_accepted(self):
        state, task, account = self._stripe_task(["failed@example.com"])
        run = self.store.begin_delivery_run(task, execution_mode="First Run", recipients=("failed@example.com",))
        self.store.begin_delivery_operation(
            run_id=run.run_id, recipient_ordinal=0, attempt_number=1, stage="invoice_send",
            account_id=account.id, account_name=account.name, idempotency_key="invio:task:send",
        )
        self.store.finish_delivery_operation(
            run_id=run.run_id, recipient_ordinal=0, attempt_number=1, stage="invoice_send",
            status="Failed", error_class="ProviderRuntimeError", error_code="HTTP_422", error_message="invalid",
        )
        self.store.finish_delivery_recipient(
            run_id=run.run_id, recipient_ordinal=0, final_result="Failed", stage="invoice_send",
            attempt_number=1, error_class="ProviderRuntimeError", error_code="HTTP_422", error_message="invalid",
        )
        self.store.finish_delivery_run(run.run_id, status="Failed")
        record = self.store.recipient_delivery_report()[0]
        self.assertEqual(record.safe_status, "Failed")
        self.assertEqual(record.provider_send_acceptance, "Failed")
        self.assertEqual(record.email_delivery, "Not confirmed")

    def test_atomic_csv_failure_preserves_existing_target_and_removes_temp_file(self):
        target = self.root / "existing.csv"
        target.write_text("original", encoding="utf-8")
        with patch("src.core.observability.os.replace", side_effect=OSError("denied")):
            with self.assertRaises(OSError):
                atomic_write_csv(target, [["=formula"]])
        self.assertEqual(target.read_text(encoding="utf-8"), "original")
        self.assertFalse(any(path.name.endswith(".tmp") for path in self.root.iterdir()))

    def test_durable_error_sanitization_uses_central_redactor(self):
        state, task, account = self._stripe_task(["person@example.com"])

        def failing_transport(method, url, headers, body, timeout):
            del method, url, headers, body, timeout
            raise RuntimeError(
                f"Authorization: Bearer abc.def secret={account.credentials['secret_key']} person@example.com"
            )

        runtime = ProviderRuntime(transport=failing_transport, domain_store=self.store)
        with self.assertRaises(Exception):
            runtime.make_task_runner(task, state)(_Context(task))
        with closing(sqlite3.connect(self.db_path)) as connection:
            messages = "\n".join(
                str(row[0]) for row in connection.execute("SELECT error_message FROM task_delivery_operations").fetchall()
            )
        self.assertNotIn(account.credentials["secret_key"], messages)
        self.assertNotIn("abc.def", messages)
        # Durable support evidence keeps recipient identity; email masking is a Live Logs policy.
        self.assertIn("person@example.com", messages)

    def test_ui_source_keeps_existing_pages_and_adds_only_p12_controls(self):
        reports = Path("src/ui/pages/reports_page.py").read_text(encoding="utf-8")
        logs = Path("src/ui/pages/logs_page.py").read_text(encoding="utf-8")
        main = Path("src/ui/main_window.py").read_text(encoding="utf-8")
        worker = Path("src/core/worker_manager/manager.py").read_text(encoding="utf-8")
        self.assertIn('"Recipient Delivery History"', reports)
        self.assertIn('button("Export Task CSV")', reports)
        self.assertIn('button("Export Recipient CSV")', reports)
        self.assertIn('button("Clear Delivery History", "danger")', reports)
        self.assertIn("append_event", logs)
        self.assertIn("structured_log_message", worker)
        self.assertIn("atomic_write_csv", main)
        self.assertIn("except (PermissionError, OSError, UnicodeError, csv.Error)", main)
        self.assertIn("_export_failure", main)
        self.assertIn("clear_closed_delivery_history", main)
        self.assertNotIn("schema v6", main.casefold())


if __name__ == "__main__":
    unittest.main()
