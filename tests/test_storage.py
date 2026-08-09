from __future__ import annotations

import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from src.accounts.models import Account
from src.core.state import AppState, StateError
from src.core.storage import (
    CredentialStore,
    CredentialStoreError,
    DomainStore,
    DomainStoreCorruptionError,
    DomainStoreMigrationError,
)
from src.customers.models import CustomerList
from src.tasks.models import Task


class FakeKeyring:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}
        self.fail_set = False
        self.fail_get = False
        self.fail_delete = False

    def set_password(self, service_name: str, username: str, password: str) -> None:
        if self.fail_set:
            raise RuntimeError("keyring unavailable")
        self.values[(service_name, username)] = password

    def get_password(self, service_name: str, username: str) -> str | None:
        if self.fail_get:
            raise RuntimeError("keyring unavailable")
        return self.values.get((service_name, username))

    def delete_password(self, service_name: str, username: str) -> None:
        if self.fail_delete:
            raise RuntimeError("keyring unavailable")
        key = (service_name, username)
        self.values.pop(key, None)


class P02StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db_path = self.root / "domain.sqlite3"
        self.backend = FakeKeyring()
        self.credentials = CredentialStore(self.backend)
        self.store = DomainStore(self.db_path)

    def state(self) -> AppState:
        loaded = self.store.load(self.credentials)
        return AppState(domain_store=self.store, credential_store=self.credentials, loaded=loaded)

    def populate(self) -> tuple[AppState, str, str, str, str]:
        state = self.state()
        account = state.add_account(
            "stripe",
            "Stripe",
            "Primary",
            "Test",
            {"secret_key": "sk_test_STORAGE_SENTINEL"},
            status="Verified",
        )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, ["one@example.com", "two@example.com"])
        template = state.save_invoice_template(
            template_id=None,
            name="Default",
            currency="usd",
            days_until_due=30,
            memo="Memo",
            footer="Footer",
            automatic_tax=False,
            reuse_customer=True,
            invoice_title="Invoice",
            invoice_subtitle="Subtitle",
            invoice_type="INVOICE",
            customer_note="Thanks",
            terms=["Net 30", "Term 2"],
            items=[("Service", "2.50", "10.25", "7.5")],
        )
        task = state.create_task("stripe", "Stripe", [account.id], customer_list.id, template.id)
        return state, account.id, customer_list.id, template.id, task.id

    def test_empty_first_run_creates_schema_v1(self):
        with closing(sqlite3.connect(self.db_path)) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(version, 1)
        self.assertIn("accounts", tables)
        self.assertIn("tasks", tables)
        self.assertIn("account_reservations", tables)

    def test_required_sqlite_durability_pragmas_are_active(self):
        with closing(sqlite3.connect(self.db_path)) as connection:
            journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).casefold()
            connection.execute("PRAGMA synchronous = FULL")
            synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
        self.assertEqual(journal_mode, "wal")
        self.assertEqual(synchronous, 2)

    def test_restart_round_trip_restores_operational_state_exactly(self):
        state, account_id, list_id, template_id, task_id = self.populate()
        state.set_task_progress(task_id, processed=1, success=1, failed=0)
        state.set_task_status(task_id, "Paused", "Paused for restart test")

        loaded = self.store.load(self.credentials)
        restored = AppState(domain_store=self.store, credential_store=self.credentials, loaded=loaded)

        self.assertEqual(restored.accounts[account_id].status, "Verified")
        self.assertEqual(restored.accounts[account_id].credentials["secret_key"], "sk_test_STORAGE_SENTINEL")
        self.assertEqual(restored.customer_lists[list_id].emails, ["one@example.com", "two@example.com"])
        template = restored.invoice_templates[template_id]
        self.assertEqual(str(template.items[0].quantity), "2.50")
        self.assertEqual(str(template.items[0].unit_amount), "10.25")
        self.assertEqual(str(template.items[0].tax_rate), "7.5")
        self.assertEqual(template.terms, ["Net 30", "Term 2"])
        task = restored.tasks[task_id]
        self.assertEqual(task.account_ids, [account_id])
        self.assertEqual(task.account_names, ["Primary"])
        self.assertEqual(task.processed, 1)
        self.assertEqual(task.success, 1)
        self.assertEqual(task.status, "Stopped")
        self.assertIn("Recovered after application restart", task.last_message)
        self.assertEqual(restored.account_reservations[account_id], task_id)

    def test_task_account_selection_order_survives_restart(self):
        state = self.state()
        first = state.add_account(
            "stripe", "Stripe", "First", "Test", {"secret_key": "sk_test_FIRST"}, status="Verified"
        )
        second = state.add_account(
            "stripe", "Stripe", "Second", "Test", {"secret_key": "sk_test_SECOND"}, status="Verified"
        )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, ["one@example.com"])
        template = state.save_invoice_template(
            template_id=None,
            name="Default",
            currency="USD",
            days_until_due=30,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "1", "10", "0")],
        )
        task = state.create_task("stripe", "Stripe", [second.id, first.id], customer_list.id, template.id)
        restored = self.store.load(self.credentials)
        self.assertEqual(restored.tasks[task.id].account_ids, [second.id, first.id])
        self.assertEqual(restored.tasks[task.id].account_names, ["Second", "First"])

    def test_secret_is_absent_from_sqlite_and_only_credential_reference_is_stored(self):
        _, account_id, *_ = self.populate()
        database_bytes = self.db_path.read_bytes()
        self.assertNotIn(b"sk_test_STORAGE_SENTINEL", database_bytes)
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute("SELECT credential_ref FROM accounts WHERE id=?", (account_id,)).fetchone()
        self.assertEqual(row[0], f"account:{account_id}")

    def test_missing_or_unreadable_credentials_restore_account_not_verified(self):
        _, account_id, *_ = self.populate()
        self.backend.values.clear()
        loaded = self.store.load(self.credentials)
        self.assertEqual(loaded.accounts[account_id].status, "Not Verified")
        self.assertEqual(loaded.accounts[account_id].credentials, {})
        self.assertTrue(loaded.warnings)

        state = AppState(domain_store=self.store, credential_store=self.credentials, loaded=loaded)
        task = next(iter(state.tasks.values()))
        with self.assertRaisesRegex(StateError, "not verified"):
            # Direct P01 creation gate remains authoritative after credential loss.
            state.close_task(task.id)
            state.create_task(
                "stripe",
                "Stripe",
                [account_id],
                next(iter(state.customer_lists)),
                next(iter(state.invoice_templates)),
            )

    def test_credential_store_failure_has_no_plaintext_fallback(self):
        self.backend.fail_set = True
        state = self.state()
        with self.assertRaises(StateError):
            state.add_account(
                "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_NO_FALLBACK"}, status="Verified"
            )
        self.assertEqual(state.accounts, {})
        self.assertNotIn(b"sk_test_NO_FALLBACK", self.db_path.read_bytes())


    def test_account_database_failure_compensates_protected_secret(self):
        state = self.state()
        original = self.store.save_account

        def fail_save(*_args, **_kwargs):
            from src.core.storage import DomainStoreError
            raise DomainStoreError("forced database failure")

        self.store.save_account = fail_save  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(StateError, "forced database failure"):
                state.add_account(
                    "stripe",
                    "Stripe",
                    "Rollback",
                    "Test",
                    {"secret_key": "sk_test_ROLLBACK_SENTINEL"},
                    status="Verified",
                )
        finally:
            self.store.save_account = original  # type: ignore[method-assign]
        self.assertEqual(state.accounts, {})
        self.assertEqual(self.backend.values, {})

    def test_account_database_failure_reports_failed_protected_cleanup(self):
        state = self.state()
        original = self.store.save_account

        def fail_save(*_args, **_kwargs):
            from src.core.storage import DomainStoreError
            raise DomainStoreError("forced database failure")

        self.store.save_account = fail_save  # type: ignore[method-assign]
        self.backend.fail_delete = True
        try:
            with self.assertRaisesRegex(StateError, "Protected credential cleanup also failed"):
                state.add_account(
                    "stripe",
                    "Stripe",
                    "Rollback",
                    "Test",
                    {"secret_key": "sk_test_CLEANUP_SENTINEL"},
                    status="Verified",
                )
        finally:
            self.store.save_account = original  # type: ignore[method-assign]
        self.assertEqual(state.accounts, {})
        self.assertNotIn(b"sk_test_CLEANUP_SENTINEL", self.db_path.read_bytes())

    def test_credential_backend_policy_rejects_non_os_third_party_backend(self):
        class PlaintextBackend:
            pass

        PlaintextBackend.__module__ = "keyrings.alt.file"
        self.assertFalse(CredentialStore._is_approved_os_backend(PlaintextBackend()))

    def test_customer_email_transaction_rolls_back_on_constraint_failure(self):
        state = self.state()
        item = state.create_customer_list("Customers")
        state.add_emails(item.id, ["one@example.com", "two@example.com"])
        invalid = CustomerList(id=item.id, name=item.name, emails=["changed@example.com", "changed@example.com"])
        with self.assertRaises(Exception):
            self.store.replace_customer_emails(invalid)
        loaded = self.store.load(self.credentials)
        self.assertEqual(loaded.customer_lists[item.id].emails, ["one@example.com", "two@example.com"])

    def test_task_and_reservation_transaction_rolls_back_together(self):
        state, account_id, list_id, template_id, first_task_id = self.populate()
        duplicate = Task(
            id="task_duplicate",
            name="Task duplicate",
            provider_id="stripe",
            provider_name="Stripe",
            account_ids=[account_id],
            account_names=["Primary"],
            customer_list_id=list_id,
            customer_list_name=state.customer_lists[list_id].name,
            invoice_template_id=template_id,
            invoice_template_name=state.invoice_templates[template_id].name,
            total=2,
        )
        with self.assertRaises(Exception):
            self.store.create_task_with_reservations(duplicate)
        with closing(sqlite3.connect(self.db_path)) as connection:
            duplicate_count = connection.execute("SELECT COUNT(*) FROM tasks WHERE id='task_duplicate'").fetchone()[0]
            reservation = connection.execute("SELECT task_id FROM account_reservations WHERE account_id=?", (account_id,)).fetchone()[0]
        self.assertEqual(duplicate_count, 0)
        self.assertEqual(reservation, first_task_id)

    def test_future_schema_is_rejected_without_downgrade(self):
        future_path = self.root / "future.sqlite3"
        with closing(sqlite3.connect(future_path)) as connection:
            connection.execute("PRAGMA user_version = 99")
        with self.assertRaises(DomainStoreMigrationError):
            DomainStore(future_path)
        with closing(sqlite3.connect(future_path)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 99)

    def test_existing_empty_v0_database_migrates_and_is_backed_up(self):
        legacy = self.root / "legacy.sqlite3"
        with closing(sqlite3.connect(legacy)):
            pass
        DomainStore(legacy)
        backup = legacy.with_name("legacy.sqlite3.pre_migration_v0.bak")
        self.assertTrue(backup.exists())
        with closing(sqlite3.connect(legacy)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_unversioned_unknown_schema_is_rejected_without_replacement(self):
        legacy = self.root / "unknown.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            connection.execute("CREATE TABLE mystery (value TEXT)")
            connection.execute("INSERT INTO mystery VALUES ('preserve-me')")
            connection.commit()
        with self.assertRaises(DomainStoreMigrationError):
            DomainStore(legacy)
        with closing(sqlite3.connect(legacy)) as connection:
            self.assertEqual(connection.execute("SELECT value FROM mystery").fetchone()[0], "preserve-me")



    def test_account_selected_by_multiple_persisted_tasks_is_rejected(self):
        state, account_id, list_id, template_id, _task_id = self.populate()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """INSERT INTO tasks (
                       id, name, provider_id, provider_name, customer_list_id, customer_list_name,
                       invoice_template_id, invoice_template_name, status, total, success, failed, processed, last_message
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "task_conflict", "Task conflict", "stripe", "Stripe", list_id, state.customer_lists[list_id].name,
                    template_id, state.invoice_templates[template_id].name, "Ready", 2, 0, 0, 0, "",
                ),
            )
            connection.execute(
                "INSERT INTO task_accounts (task_id, ordinal, account_id, account_name) VALUES (?, ?, ?, ?)",
                ("task_conflict", 0, account_id, "Primary"),
            )
            connection.commit()
        with self.assertRaisesRegex(DomainStoreCorruptionError, "more than one persisted task"):
            self.store.load(self.credentials)

    def test_missing_persisted_reservation_is_rejected_as_inconsistent_state(self):
        _state, account_id, _list_id, _template_id, _task_id = self.populate()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("DELETE FROM account_reservations WHERE account_id=?", (account_id,))
            connection.commit()
        with self.assertRaisesRegex(DomainStoreCorruptionError, "task-account selections and account reservations"):
            self.store.load(self.credentials)

    def test_corrupt_database_is_not_overwritten(self):
        corrupt = self.root / "corrupt.sqlite3"
        original = b"not-a-sqlite-database\x00\x01\x02"
        corrupt.write_bytes(original)
        with self.assertRaises(DomainStoreCorruptionError):
            DomainStore(corrupt)
        self.assertEqual(corrupt.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
