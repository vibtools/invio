from __future__ import annotations

import base64
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from src.core.provider_runtime import ProviderRuntime, ProviderRuntimeError
from src.core.state import AppState
from src.core.storage import CredentialStore, DomainStore, DomainStoreCorruptionError, DomainStoreError
from src.core.storage.schema import (
    MIGRATION_V1_TO_V2,
    MIGRATION_V2_TO_V3,
    MIGRATION_V3_TO_V4,
    SCHEMA_V1,
)
from src.tasks.delivery_ledger import (
    DELIVERY_OPERATION_FAILED,
    DELIVERY_OPERATION_STARTED,
    DELIVERY_OPERATION_SUCCEEDED,
    DELIVERY_OPERATION_UNCERTAIN,
    DELIVERY_RESULT_FAILED,
    DELIVERY_RESULT_PENDING,
    DELIVERY_RESULT_UNCERTAIN,
    DELIVERY_RUN_INTERRUPTED,
)
from src.tasks.state_machine import TaskExecutionMode


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

    def progress(self, processed: int, success: int, failed: int, message: str) -> None:
        self.progress_events.append((processed, success, failed, message))

    def log(self, message: str) -> None:
        self.logs.append(message)


class P10DeliveryLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db_path = self.root / "domain.sqlite3"
        self.credentials = CredentialStore(_Keyring())
        self.store = DomainStore(self.db_path)

    def state(self) -> AppState:
        return AppState(
            domain_store=self.store,
            credential_store=self.credentials,
            loaded=self.store.load(self.credentials),
        )

    def task_state(self, emails: list[str], *, account_count: int = 1):
        state = self.state()
        accounts = []
        for index in range(account_count):
            account = state.add_account(
                "stripe",
                "Stripe",
                f"Account {index + 1}",
                "Test",
                {"secret_key": f"sk_test_P10_SECRET_{index + 1}"},
                status="Verified",
            )
            accounts.append(account)
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, emails)
        template = state.save_invoice_template(
            template_id=None,
            name="P10 Template",
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
            [account.id for account in accounts],
            customer_list.id,
            template.id,
        )
        return state, task, accounts

    @staticmethod
    def successful_transport(*, on_send=None):
        customer_by_id: dict[str, str] = {}
        current_email = {"value": ""}

        def transport(method, url, headers, body, timeout):
            del timeout
            path = urlparse(url).path
            form = parse_qs((body or b"").decode("utf-8"))
            if method == "GET" and path.endswith("/customers"):
                return {"data": []}
            if method == "POST" and path.endswith("/customers"):
                email = form["email"][0]
                customer_id = f"cus_{len(customer_by_id) + 1}"
                customer_by_id[customer_id] = email
                current_email["value"] = email
                return {"id": customer_id}
            if method == "POST" and path.endswith("/invoices"):
                current_email["value"] = customer_by_id[form["customer"][0]]
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/invoiceitems"):
                return {"id": "ii_1"}
            if method == "POST" and path.endswith("/finalize"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/send"):
                if on_send is not None:
                    return on_send(current_email["value"], headers)
                return {"id": "in_1", "status": "open"}
            raise AssertionError(f"Unexpected request: {method} {url}")

        return transport

    def test_schema_v5_adds_exactly_three_delivery_tables(self):
        with closing(sqlite3.connect(self.db_path)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 6)
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'task_delivery_%'"
                ).fetchall()
            }
        self.assertEqual(
            tables,
            {"task_delivery_runs", "task_delivery_recipients", "task_delivery_operations"},
        )

    def test_schema_v4_migrates_with_backup_without_fabricating_delivery_history(self):
        legacy = self.root / "legacy_v4.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            connection.executescript(SCHEMA_V1)
            connection.executescript(MIGRATION_V1_TO_V2)
            connection.executescript(MIGRATION_V2_TO_V3)
            connection.executescript(MIGRATION_V3_TO_V4)
            connection.execute("PRAGMA user_version = 4")
            connection.commit()
        DomainStore(legacy)
        self.assertTrue(legacy.with_name(f"{legacy.name}.pre_migration_v4.bak").exists())
        with closing(sqlite3.connect(legacy)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 6)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM task_delivery_runs").fetchone()[0], 0)

    def test_run_id_is_distinct_from_task_id_and_run_number_increments(self):
        _state, task, _accounts = self.task_state(["a@example.com"])
        first = self.store.begin_delivery_run(
            task,
            execution_mode=TaskExecutionMode.FIRST_RUN.value,
            recipients=("a@example.com",),
        )
        self.assertNotEqual(first.run_id, task.id)
        self.assertEqual(first.run_number, 1)
        self.store.finish_delivery_run(first.run_id, status="Stopped")
        second = self.store.begin_delivery_run(
            task,
            execution_mode=TaskExecutionMode.RESUME_REMAINING.value,
            recipients=("a@example.com",),
        )
        self.assertNotEqual(second.run_id, first.run_id)
        self.assertEqual(second.run_number, 2)

    def test_write_ahead_started_operation_exists_before_transport(self):
        state, task, _accounts = self.task_state(["a@example.com"])
        observed: list[str] = []

        def transport(method, url, headers, body, timeout):
            del method, headers, body, timeout
            with closing(sqlite3.connect(self.db_path)) as connection:
                rows = connection.execute(
                    "SELECT stage, status FROM task_delivery_operations ORDER BY rowid"
                ).fetchall()
            self.assertTrue(rows)
            self.assertEqual(rows[-1][1], DELIVERY_OPERATION_STARTED)
            observed.append(rows[-1][0])
            path = urlparse(url).path
            if path.endswith("/customers") and "?" in url:
                return {"data": []}
            if path.endswith("/customers"):
                return {"id": "cus_1"}
            if path.endswith("/invoices"):
                return {"id": "in_1"}
            if path.endswith("/invoiceitems"):
                return {"id": "ii_1"}
            if path.endswith("/finalize") or path.endswith("/send"):
                return {"id": "in_1"}
            raise AssertionError(path)

        runtime = ProviderRuntime(transport=transport, domain_store=self.store)
        runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(
            observed,
            ["customer_lookup", "customer_create", "invoice_create", "invoice_item:0", "invoice_finalize", "invoice_send"],
        )

    def test_started_commit_failure_prevents_transport(self):
        state, task, _accounts = self.task_state(["a@example.com"])
        calls: list[str] = []
        runtime = ProviderRuntime(transport=lambda *args: calls.append(str(args[1])) or {}, domain_store=self.store)
        with patch.object(self.store, "begin_delivery_operation", side_effect=DomainStoreError("ledger unavailable")):
            with self.assertRaisesRegex(ProviderRuntimeError, "Started operation could not be committed"):
                runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(calls, [])

    def test_success_persists_ids_idempotency_and_no_secrets(self):
        state, task, _accounts = self.task_state(["a@example.com"])
        runtime = ProviderRuntime(transport=self.successful_transport(), domain_store=self.store)
        runtime.make_task_runner(task, state)(_Context(task))
        with closing(sqlite3.connect(self.db_path)) as connection:
            run_id, task_id = connection.execute("SELECT run_id, task_id FROM task_delivery_runs").fetchone()
            recipient = connection.execute(
                "SELECT provider_customer_id, provider_invoice_id, final_result FROM task_delivery_recipients"
            ).fetchone()
            operations = connection.execute(
                "SELECT stage, attempt_number, idempotency_key, provider_reference FROM task_delivery_operations ORDER BY rowid"
            ).fetchall()
        self.assertNotEqual(run_id, task_id)
        self.assertEqual(recipient, ("cus_1", "in_1", "Succeeded"))
        keyed = {stage: key for stage, _attempt, key, _ref in operations if key}
        self.assertIn(task.id, keyed["customer_create"])
        self.assertIn(task.id, keyed["invoice_create"])
        self.assertIn(task.id, keyed["invoice_send"])
        self.assertNotIn(run_id, keyed["invoice_send"])
        database_bytes = self.db_path.read_bytes()
        self.assertNotIn(b"sk_test_P10_SECRET_1", database_bytes)
        self.assertNotIn(b"Authorization", database_bytes)

    def test_p08_retry_attempts_are_durable_and_reuse_same_idempotency_key(self):
        state, task, _accounts = self.task_state(["a@example.com"])
        send_attempt = {"value": 0}

        def on_send(_email: str, _headers: dict[str, str]):
            send_attempt["value"] += 1
            if send_attempt["value"] < 3:
                raise ProviderRuntimeError("temporary disconnect", category="network", retryable=True)
            return {"id": "in_1"}

        runtime = ProviderRuntime(
            transport=self.successful_transport(on_send=on_send),
            domain_store=self.store,
            retry_jitter_source=lambda: 0.0,
        )
        runtime._retry_delay_seconds = lambda *_args: 0.0  # type: ignore[method-assign]
        runtime.make_task_runner(task, state)(_Context(task))
        with closing(sqlite3.connect(self.db_path)) as connection:
            sends = connection.execute(
                """SELECT attempt_number, status, idempotency_key
                   FROM task_delivery_operations WHERE stage='invoice_send' ORDER BY attempt_number"""
            ).fetchall()
        self.assertEqual([row[0] for row in sends], [1, 2, 3])
        self.assertEqual(sends[-1][1], "Succeeded")
        self.assertEqual(len({row[2] for row in sends}), 1)
        self.assertIn(task.id, sends[0][2])

    def test_restart_resume_remaining_uses_durable_pending_set(self):
        state, task, _accounts = self.task_state(["a@example.com", "b@example.com"])
        context = _Context(task)

        def on_send(email: str, _headers: dict[str, str]):
            if email == "a@example.com":
                context.stop_flag.set()
            return {"id": "in_1"}

        first = ProviderRuntime(transport=self.successful_transport(on_send=on_send), domain_store=self.store)
        first.make_task_runner(task, state)(context)

        loaded = self.store.load(self.credentials)
        restored_state = AppState(domain_store=self.store, credential_store=self.credentials, loaded=loaded)
        restored = restored_state.tasks[task.id]
        self.assertEqual(restored.status, "Stopped")
        self.assertEqual((restored.processed, restored.success, restored.failed), (1, 1, 0))

        sent: list[str] = []
        second = ProviderRuntime(
            transport=self.successful_transport(on_send=lambda email, _headers: sent.append(email) or {"id": "in_1"}),
            domain_store=self.store,
        )
        second.make_task_runner(restored, restored_state, resume_remaining=True)(_Context(restored))
        self.assertEqual(sent, ["b@example.com"])
        final = second.delivery_summary(restored)
        self.assertEqual((final.processed, final.success, final.failed, final.remaining), (2, 2, 0, 0))

    def test_restart_retry_failed_uses_durable_failed_set(self):
        state, task, _accounts = self.task_state(["good@example.com", "bad@example.com"])

        def first_send(email: str, _headers: dict[str, str]):
            if email == "bad@example.com":
                raise ProviderRuntimeError("invalid recipient", category="http", http_status=422)
            return {"id": "in_1"}

        first = ProviderRuntime(transport=self.successful_transport(on_send=first_send), domain_store=self.store)
        with self.assertRaises(ProviderRuntimeError):
            first.make_task_runner(task, state)(_Context(task))

        loaded = self.store.load(self.credentials)
        restored_state = AppState(domain_store=self.store, credential_store=self.credentials, loaded=loaded)
        restored = restored_state.tasks[task.id]
        self.assertEqual(restored.status, "Failed")
        self.assertEqual((restored.processed, restored.success, restored.failed), (2, 1, 1))

        retried: list[str] = []
        second = ProviderRuntime(
            transport=self.successful_transport(on_send=lambda email, _headers: retried.append(email) or {"id": "in_1"}),
            domain_store=self.store,
        )
        second.make_task_runner(restored, restored_state, retry_failed=True)(_Context(restored))
        self.assertEqual(retried, ["bad@example.com"])

    def test_interrupted_mutating_started_operation_recovers_uncertain(self):
        _state, task, accounts = self.task_state(["a@example.com"])
        run = self.store.begin_delivery_run(
            task,
            execution_mode=TaskExecutionMode.FIRST_RUN.value,
            recipients=("a@example.com",),
        )
        self.store.begin_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="invoice_create",
            account_id=accounts[0].id,
            account_name=accounts[0].name,
            idempotency_key=f"invio:{task.id}:digest:invoice",
        )
        loaded = self.store.load(self.credentials)
        restored = loaded.tasks[task.id]
        summary = self.store.delivery_summary(restored)
        self.assertEqual(restored.status, "Stopped")
        self.assertEqual(summary.uncertain_recipients, ("a@example.com",))
        with closing(sqlite3.connect(self.db_path)) as connection:
            self.assertEqual(
                connection.execute("SELECT status FROM task_delivery_runs WHERE run_id=?", (run.run_id,)).fetchone()[0],
                DELIVERY_RUN_INTERRUPTED,
            )
            self.assertEqual(
                connection.execute("SELECT status FROM task_delivery_operations WHERE run_id=?", (run.run_id,)).fetchone()[0],
                DELIVERY_OPERATION_UNCERTAIN,
            )

    def test_interrupted_read_only_started_operation_remains_pending(self):
        _state, task, accounts = self.task_state(["a@example.com"])
        run = self.store.begin_delivery_run(
            task,
            execution_mode=TaskExecutionMode.FIRST_RUN.value,
            recipients=("a@example.com",),
        )
        self.store.begin_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="customer_lookup",
            account_id=accounts[0].id,
            account_name=accounts[0].name,
            idempotency_key="",
        )
        restored = self.store.load(self.credentials).tasks[task.id]
        summary = self.store.delivery_summary(restored)
        self.assertEqual(summary.pending_recipients, ("a@example.com",))
        self.assertEqual(summary.uncertain_recipients, ())

    def test_p09_fallback_account_binding_survives_restart(self):
        state, task, accounts = self.task_state(["a@example.com"], account_count=2)
        runtime = ProviderRuntime(transport=self.successful_transport(on_send=lambda _e, _h: (_ for _ in ()).throw(
            ProviderRuntimeError("deterministic failure", category="http", http_status=422)
        )), domain_store=self.store)
        runtime._account_health[("stripe", accounts[0].id)] = type(runtime._account_health.setdefault(("stripe", accounts[0].id), None)) if False else None
        from src.core.provider_runtime.runtime import _SchedulerHealthState
        import time
        runtime._account_health[("stripe", accounts[0].id)] = _SchedulerHealthState(
            consecutive_incidents=1,
            cooldown_until=time.monotonic() + 30.0,
        )
        with self.assertRaises(ProviderRuntimeError):
            runtime.make_task_runner(task, state)(_Context(task))
        with closing(sqlite3.connect(self.db_path)) as connection:
            assigned = connection.execute(
                "SELECT assigned_account_id FROM task_delivery_recipients"
            ).fetchone()[0]
        self.assertEqual(assigned, accounts[1].id)

        loaded = self.store.load(self.credentials)
        restored_state = AppState(domain_store=self.store, credential_store=self.credentials, loaded=loaded)
        restored = restored_state.tasks[task.id]
        used_auth: list[str] = []

        def success_after_restart(email: str, headers: dict[str, str]):
            del email
            used_auth.append(headers.get("Authorization", ""))
            return {"id": "in_1"}

        restarted = ProviderRuntime(
            transport=self.successful_transport(on_send=success_after_restart),
            domain_store=self.store,
        )
        restarted.make_task_runner(restored, restored_state, retry_failed=True)(_Context(restored))
        expected = "Basic " + base64.b64encode(b"sk_test_P10_SECRET_2:").decode("ascii")
        self.assertEqual(used_auth, [expected])

    def test_task_counters_ahead_of_ledger_fail_closed_on_restart(self):
        state, task, _accounts = self.task_state(["a@example.com", "b@example.com"])
        context = _Context(task)

        def on_send(email: str, _headers: dict[str, str]):
            if email == "a@example.com":
                context.stop_flag.set()
            return {"id": "in_1"}

        ProviderRuntime(transport=self.successful_transport(on_send=on_send), domain_store=self.store).make_task_runner(
            task, state
        )(context)
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("UPDATE tasks SET processed=2, success=2, failed=0 WHERE id=?", (task.id,))
            connection.commit()
        with self.assertRaisesRegex(DomainStoreCorruptionError, "ahead of its durable delivery evidence"):
            self.store.load(self.credentials)

    def test_later_same_key_success_reconciles_prior_uncertainty_before_definitive_failure(self):
        _state, task, accounts = self.task_state(["a@example.com"])
        run = self.store.begin_delivery_run(
            task,
            execution_mode=TaskExecutionMode.FIRST_RUN.value,
            recipients=("a@example.com",),
        )
        invoice_key = f"invio:{task.id}:digest:invoice"
        self.store.begin_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="invoice_create",
            account_id=accounts[0].id,
            account_name=accounts[0].name,
            idempotency_key=invoice_key,
        )
        self.store.finish_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="invoice_create",
            status=DELIVERY_OPERATION_UNCERTAIN,
            error_class="ProviderRuntimeError",
            error_code="network",
            error_message="ambiguous response",
        )
        self.store.begin_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=2,
            stage="invoice_create",
            account_id=accounts[0].id,
            account_name=accounts[0].name,
            idempotency_key=invoice_key,
        )
        self.store.finish_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=2,
            stage="invoice_create",
            status=DELIVERY_OPERATION_SUCCEEDED,
            provider_reference="in_1",
        )
        self.store.begin_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=2,
            stage="invoice_send",
            account_id=accounts[0].id,
            account_name=accounts[0].name,
            idempotency_key=f"invio:{task.id}:digest:send",
        )
        self.store.finish_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=2,
            stage="invoice_send",
            status=DELIVERY_OPERATION_FAILED,
            error_class="ProviderRuntimeError",
            error_code="HTTP_422",
            error_message="deterministic rejection",
        )
        self.store.finish_delivery_recipient(
            run_id=run.run_id,
            recipient_ordinal=0,
            final_result=DELIVERY_RESULT_FAILED,
            stage="invoice_send",
            attempt_number=2,
            error_class="ProviderRuntimeError",
            error_code="HTTP_422",
            error_message="deterministic rejection",
        )
        self.store.finish_delivery_run(run.run_id, status="Failed")

        summary = self.store.delivery_summary(task)
        self.assertEqual(summary.failed_recipients, ("a@example.com",))
        self.assertEqual(summary.uncertain_recipients, ())
        self.assertFalse(
            self.store.recipient_has_uncertain_mutation(run_id=run.run_id, recipient_ordinal=0)
        )

    def test_unresolved_prior_run_uncertainty_survives_later_unrelated_failure(self):
        _state, task, accounts = self.task_state(["a@example.com"])
        invoice_key = f"invio:{task.id}:digest:invoice"
        first = self.store.begin_delivery_run(
            task,
            execution_mode=TaskExecutionMode.FIRST_RUN.value,
            recipients=("a@example.com",),
        )
        self.store.begin_delivery_operation(
            run_id=first.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="invoice_create",
            account_id=accounts[0].id,
            account_name=accounts[0].name,
            idempotency_key=invoice_key,
        )
        self.store.finish_delivery_operation(
            run_id=first.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="invoice_create",
            status=DELIVERY_OPERATION_UNCERTAIN,
            error_class="ProviderRuntimeError",
            error_code="network",
            error_message="ambiguous response",
        )
        self.store.finish_delivery_recipient(
            run_id=first.run_id,
            recipient_ordinal=0,
            final_result=DELIVERY_RESULT_UNCERTAIN,
            stage="invoice_create",
            attempt_number=1,
            error_class="ProviderRuntimeError",
            error_code="network",
            error_message="ambiguous response",
        )
        self.store.finish_delivery_run(first.run_id, status="Failed")

        second = self.store.begin_delivery_run(
            task,
            execution_mode=TaskExecutionMode.RESUME_REMAINING.value,
            recipients=("a@example.com",),
        )
        customer_key = f"invio:{task.id}:digest:customer"
        self.store.begin_delivery_operation(
            run_id=second.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="customer_create",
            account_id=accounts[0].id,
            account_name=accounts[0].name,
            idempotency_key=customer_key,
        )
        self.store.finish_delivery_operation(
            run_id=second.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="customer_create",
            status=DELIVERY_OPERATION_FAILED,
            error_class="ProviderRuntimeError",
            error_code="HTTP_422",
            error_message="deterministic rejection",
        )
        self.store.finish_delivery_recipient(
            run_id=second.run_id,
            recipient_ordinal=0,
            final_result=DELIVERY_RESULT_FAILED,
            stage="customer_create",
            attempt_number=1,
            error_class="ProviderRuntimeError",
            error_code="HTTP_422",
            error_message="deterministic rejection",
        )
        self.store.finish_delivery_run(second.run_id, status="Failed")

        summary = self.store.delivery_summary(task)
        self.assertEqual(summary.failed_recipients, ())
        self.assertEqual(summary.uncertain_recipients, ("a@example.com",))
        self.assertTrue(
            self.store.recipient_has_uncertain_mutation(run_id=second.run_id, recipient_ordinal=0)
        )

    def test_close_task_retains_historical_delivery_ledger(self):
        state, task, _accounts = self.task_state(["a@example.com"])
        runtime = ProviderRuntime(transport=self.successful_transport(), domain_store=self.store)
        runtime.make_task_runner(task, state)(_Context(task))
        summary = runtime.delivery_summary(task)
        state.set_task_progress(task.id, processed=summary.processed, success=summary.success, failed=summary.failed)
        state.set_task_status(task.id, "Running", "finishing")
        state.set_task_status(task.id, "Completed", "done")
        state.close_task(task.id)
        with closing(sqlite3.connect(self.db_path)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM tasks WHERE id=?", (task.id,)).fetchone()[0], 0)
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM task_delivery_runs WHERE task_id=?", (task.id,)).fetchone()[0],
                1,
            )

    def test_operation_result_persistence_failure_stops_before_next_recipient(self):
        state, task, _accounts = self.task_state(["a@example.com", "b@example.com"])
        transport_calls: list[str] = []

        def transport(method, url, headers, body, timeout):
            transport_calls.append(url)
            return self.successful_transport()(method, url, headers, body, timeout)

        runtime = ProviderRuntime(transport=transport, domain_store=self.store)
        original = self.store.finish_delivery_operation
        calls = {"count": 0}

        def fail_first(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise DomainStoreError("simulated post-request ledger failure")
            return original(*args, **kwargs)

        with patch.object(self.store, "finish_delivery_operation", side_effect=fail_first):
            with self.assertRaisesRegex(ProviderRuntimeError, "durable operation result could not be saved"):
                runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(len(transport_calls), 1)
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute("SELECT status FROM task_delivery_operations").fetchone()
        self.assertEqual(row[0], DELIVERY_OPERATION_STARTED)


if __name__ == "__main__":
    unittest.main()
