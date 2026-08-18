from __future__ import annotations

import sqlite3
from contextlib import closing
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from src.accounts.models import Account
from src.core.state import AppState, StateError
from src.core.storage import (
    CredentialStore,
    CredentialStoreError,
    DomainStore,
    DomainStoreError,
    DomainStoreCorruptionError,
    DomainStoreMigrationError,
)
from src.customers.models import CustomerList, CustomerRecord
from src.tasks.models import TASK_SNAPSHOT_LEGACY_UNAVAILABLE, Task, TaskExecutionSnapshot, TaskSendingControls
from src.core.storage.schema import (
    MIGRATION_V1_TO_V2, MIGRATION_V2_TO_V3, MIGRATION_V3_TO_V4, MIGRATION_V4_TO_V5, SCHEMA_V1
)


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
        self.assertEqual(version, 6)
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
        state.set_task_status(task_id, "Running", "Running for restart test")
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

    def test_populated_schema_v1_account_migrates_without_losing_metadata(self):
        legacy = self.root / "populated_v1.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            connection.executescript(SCHEMA_V1)
            connection.execute(
                "INSERT INTO accounts (id, provider_id, provider_name, name, mode, status, credential_ref) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("acct_legacy", "stripe", "Stripe", "Legacy", "Test", "Verified", "account:acct_legacy"),
            )
            connection.execute("PRAGMA user_version = 1")
            connection.commit()
        backend = FakeKeyring()
        credentials = CredentialStore(backend)
        credentials.set_credentials("acct_legacy", {"secret_key": "sk_test_LEGACY"})
        store = DomainStore(legacy)
        loaded = store.load(credentials)
        account = loaded.accounts["acct_legacy"]
        self.assertEqual(account.name, "Legacy")
        self.assertEqual(account.status, "Verified")
        self.assertEqual(account.last_verification_at, "")
        self.assertEqual(account.verification_error_summary, "")

    def test_schema_v1_migrates_to_v2_with_backup_and_verification_columns(self):
        legacy = self.root / "legacy_v1.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            connection.executescript(SCHEMA_V1)
            connection.execute("PRAGMA user_version = 1")
            connection.commit()
        DomainStore(legacy)
        backup = legacy.with_name("legacy_v1.sqlite3.pre_migration_v1.bak")
        self.assertTrue(backup.exists())
        with closing(sqlite3.connect(legacy)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 6)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(accounts)").fetchall()}
        self.assertIn("last_verification_at", columns)
        self.assertIn("verification_error_summary", columns)

    def test_migration_backup_closes_destination_before_atomic_replace(self):
        legacy = self.root / "windows_lock_v1.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            connection.executescript(SCHEMA_V1)
            connection.execute("PRAGMA user_version = 1")
            connection.commit()

        source = sqlite3.connect(legacy)
        store = object.__new__(DomainStore)
        store.path = legacy
        real_connect = sqlite3.connect
        tracked: dict[str, object] = {}

        class TrackingConnection(sqlite3.Connection):
            explicitly_closed = False

            def close(self):
                self.explicitly_closed = True
                return super().close()

        def connect_tracking(database, *args, **kwargs):
            if Path(database).name.endswith(".tmp"):
                connection = real_connect(database, *args, factory=TrackingConnection, **kwargs)
                tracked["destination"] = connection
                return connection
            return real_connect(database, *args, **kwargs)

        real_replace = Path.replace

        def replace_only_after_close(path_self, target):
            destination = tracked.get("destination")
            self.assertIsNotNone(destination)
            self.assertTrue(
                getattr(destination, "explicitly_closed", False),
                "Migration backup destination must be closed before atomic replacement on Windows.",
            )
            return real_replace(path_self, target)

        try:
            with mock.patch("src.core.storage.domain_store.sqlite3.connect", side_effect=connect_tracking), \
                 mock.patch.object(Path, "replace", new=replace_only_after_close):
                store._create_migration_backup(1, source)
        finally:
            source.close()

        backup = legacy.with_name("windows_lock_v1.sqlite3.pre_migration_v1.bak")
        self.assertTrue(backup.exists())

    def test_schema_v1_backup_includes_committed_wal_state(self):
        legacy = self.root / "legacy_v1_wal.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            connection.executescript(SCHEMA_V1)
            connection.execute("PRAGMA user_version = 1")
            connection.commit()

        writer = sqlite3.connect(legacy)
        try:
            writer.execute("PRAGMA journal_mode = WAL")
            writer.execute("PRAGMA wal_autocheckpoint = 0")
            writer.execute(
                "INSERT INTO accounts (id, provider_id, provider_name, name, mode, status, credential_ref) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("acct_wal", "stripe", "Stripe", "WAL Account", "Test", "Verified", "account:acct_wal"),
            )
            writer.commit()
            self.assertTrue(Path(f"{legacy}-wal").exists())

            DomainStore(legacy)
        finally:
            writer.close()

        backup = legacy.with_name("legacy_v1_wal.sqlite3.pre_migration_v1.bak")
        with closing(sqlite3.connect(backup)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM accounts WHERE id='acct_wal'").fetchone()[0],
                1,
            )

    def test_verification_health_round_trip_survives_restart(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_HEALTH"},
            status="Verified", last_verification_at="2026-08-09T02:00:00+00:00"
        )
        state.record_account_verification(
            account.id, verified=False, last_verification_at="2026-08-09T02:10:00+00:00", error_summary="Permission denied."
        )
        loaded = self.store.load(self.credentials)
        restored = loaded.accounts[account.id]
        self.assertEqual(restored.status, "Not Verified")
        self.assertEqual(restored.last_verification_at, "2026-08-09T02:10:00+00:00")
        self.assertEqual(restored.verification_error_summary, "Permission denied.")

    def test_missing_protected_credentials_preserve_last_api_timestamp_and_mark_unverified(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_HEALTH_MISSING"},
            status="Verified", last_verification_at="2026-08-09T02:20:00+00:00"
        )
        self.backend.values.clear()
        loaded = self.store.load(self.credentials)
        restored = loaded.accounts[account.id]
        self.assertEqual(restored.status, "Not Verified")
        self.assertEqual(restored.last_verification_at, "2026-08-09T02:20:00+00:00")
        self.assertEqual(restored.verification_error_summary, "Protected credentials are unavailable.")

    def test_missing_protected_credentials_persist_fail_closed_verification_state(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_HEALTH_RESTORE"},
            status="Verified", last_verification_at="2026-08-09T02:21:00+00:00"
        )
        protected = dict(self.backend.values)
        self.backend.values.clear()

        first_load = self.store.load(self.credentials)
        self.assertEqual(first_load.accounts[account.id].status, "Not Verified")
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute(
                "SELECT status, last_verification_at, verification_error_summary FROM accounts WHERE id=?",
                (account.id,),
            ).fetchone()
        self.assertEqual(row[0], "Not Verified")
        self.assertEqual(row[1], "2026-08-09T02:21:00+00:00")
        self.assertEqual(row[2], "Protected credentials are unavailable.")

        self.backend.values.update(protected)
        second_load = self.store.load(self.credentials)
        self.assertEqual(second_load.accounts[account.id].status, "Not Verified")
        self.assertEqual(second_load.accounts[account.id].credentials["secret_key"], "sk_test_HEALTH_RESTORE")

    def test_account_update_database_failure_restores_old_protected_credentials(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_OLD"}, status="Verified"
        )
        original = self.store.update_account

        def fail_update(*_args, **_kwargs):
            from src.core.storage import DomainStoreError
            raise DomainStoreError("forced account update failure")

        self.store.update_account = fail_update  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(StateError, "forced account update failure"):
                state.update_account(
                    account.id, name="Changed", mode="Test", credentials={"secret_key": "sk_test_NEW"},
                    status="Verified", last_verification_at="2026-08-09T02:30:00+00:00"
                )
        finally:
            self.store.update_account = original  # type: ignore[method-assign]
        self.assertEqual(state.accounts[account.id].name, "Primary")
        self.assertEqual(self.credentials.get_credentials(f"account:{account.id}"), {"secret_key": "sk_test_OLD"})

    def test_account_update_final_database_failure_restores_old_durable_state(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_OLD_FINAL"}, status="Verified"
        )
        original = self.store.update_account

        def fail_candidate(candidate):
            from src.core.storage import DomainStoreError
            if candidate.name == "Changed" and candidate.status == "Verified":
                raise DomainStoreError("forced final account update failure")
            return original(candidate)

        self.store.update_account = fail_candidate  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(StateError, "forced final account update failure"):
                state.update_account(
                    account.id, name="Changed", mode="Live", credentials={"secret_key": "sk_live_NEW_FINAL"},
                    status="Verified", last_verification_at="2026-08-09T02:31:00+00:00"
                )
        finally:
            self.store.update_account = original  # type: ignore[method-assign]

        self.assertEqual(state.accounts[account.id].name, "Primary")
        self.assertEqual(state.accounts[account.id].status, "Verified")
        self.assertEqual(self.credentials.get_credentials(f"account:{account.id}"), {"secret_key": "sk_test_OLD_FINAL"})
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute("SELECT name, mode, status FROM accounts WHERE id=?", (account.id,)).fetchone()
        self.assertEqual(tuple(row), ("Primary", "Test", "Verified"))

    def test_account_update_rollback_failure_remains_fail_closed(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_OLD_ROLLBACK"}, status="Verified"
        )
        original_update = self.store.update_account
        original_set = self.credentials.set_credentials

        def fail_candidate(candidate):
            from src.core.storage import DomainStoreError
            if candidate.name == "Changed" and candidate.status == "Verified":
                raise DomainStoreError("forced final account update failure")
            return original_update(candidate)

        set_calls = 0

        def fail_credential_rollback(account_id, credentials):
            nonlocal set_calls
            from src.core.storage import CredentialStoreError
            set_calls += 1
            if set_calls == 2:
                raise CredentialStoreError("forced protected rollback failure")
            return original_set(account_id, credentials)

        self.store.update_account = fail_candidate  # type: ignore[method-assign]
        self.credentials.set_credentials = fail_credential_rollback  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(StateError, "account remains Not Verified"):
                state.update_account(
                    account.id, name="Changed", mode="Live", credentials={"secret_key": "sk_live_NEW_ROLLBACK"},
                    status="Verified", last_verification_at="2026-08-09T02:32:00+00:00"
                )
        finally:
            self.store.update_account = original_update  # type: ignore[method-assign]
            self.credentials.set_credentials = original_set  # type: ignore[method-assign]

        self.assertEqual(state.accounts[account.id].status, "Not Verified")
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute("SELECT status, verification_error_summary FROM accounts WHERE id=?", (account.id,)).fetchone()
        self.assertEqual(row[0], "Not Verified")
        self.assertIn("Account update did not complete", row[1])

    def test_failed_retest_persistence_failure_still_fails_closed_in_memory(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_RETEST_FAIL"}, status="Verified"
        )
        original = self.store.update_account_verification

        def fail_verification_update(*_args, **_kwargs):
            from src.core.storage import DomainStoreError
            raise DomainStoreError("forced verification persistence failure")

        self.store.update_account_verification = fail_verification_update  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(StateError, "forced verification persistence failure"):
                state.record_account_verification(
                    account.id, verified=False, last_verification_at="2026-08-09T02:25:00+00:00",
                    error_summary="Credential rejected."
                )
        finally:
            self.store.update_account_verification = original  # type: ignore[method-assign]
        self.assertEqual(state.accounts[account.id].status, "Not Verified")
        self.assertEqual(state.accounts[account.id].last_verification_at, "2026-08-09T02:25:00+00:00")
        self.assertEqual(state.accounts[account.id].verification_error_summary, "Credential rejected.")

    def test_successful_retest_persistence_failure_does_not_elevate_unverified_account(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_RETEST_SUCCESS"}, status="Not Verified"
        )
        original = self.store.update_account_verification

        def fail_verification_update(*_args, **_kwargs):
            from src.core.storage import DomainStoreError
            raise DomainStoreError("forced verification persistence failure")

        self.store.update_account_verification = fail_verification_update  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(StateError, "forced verification persistence failure"):
                state.record_account_verification(
                    account.id, verified=True, last_verification_at="2026-08-09T02:26:00+00:00"
                )
        finally:
            self.store.update_account_verification = original  # type: ignore[method-assign]
        self.assertEqual(state.accounts[account.id].status, "Not Verified")

    def test_account_delete_database_failure_restores_protected_credentials(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_DELETE_OLD"}, status="Verified"
        )
        original = self.store.delete_account

        def fail_delete(*_args, **_kwargs):
            from src.core.storage import DomainStoreError
            raise DomainStoreError("forced account delete failure")

        self.store.delete_account = fail_delete  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(StateError, "forced account delete failure"):
                state.delete_account(account.id)
        finally:
            self.store.delete_account = original  # type: ignore[method-assign]
        self.assertIn(account.id, state.accounts)
        self.assertEqual(
            self.credentials.get_credentials(f"account:{account.id}"), {"secret_key": "sk_test_DELETE_OLD"}
        )

    def test_account_delete_protected_credential_failure_keeps_account_and_database(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_DELETE_BLOCK"}, status="Verified"
        )
        self.backend.fail_delete = True
        with self.assertRaises(StateError):
            state.delete_account(account.id)
        self.assertIn(account.id, state.accounts)
        with closing(sqlite3.connect(self.db_path)) as connection:
            count = connection.execute("SELECT COUNT(*) FROM accounts WHERE id=?", (account.id,)).fetchone()[0]
        self.assertEqual(count, 1)

    def test_successful_account_update_persists_new_protected_secret_and_health(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_BEFORE"}, status="Verified"
        )
        updated = state.update_account(
            account.id, name="Primary Updated", mode="Live", credentials={"secret_key": "sk_live_AFTER"},
            status="Verified", last_verification_at="2026-08-09T02:40:00+00:00"
        )
        self.assertEqual(updated.provider_id, "stripe")
        self.assertEqual(self.credentials.get_credentials(f"account:{account.id}"), {"secret_key": "sk_live_AFTER"})
        loaded = self.store.load(self.credentials).accounts[account.id]
        self.assertEqual(loaded.name, "Primary Updated")
        self.assertEqual(loaded.mode, "Live")
        self.assertEqual(loaded.last_verification_at, "2026-08-09T02:40:00+00:00")

    def test_successful_account_delete_removes_database_and_protected_secret(self):
        state = self.state()
        account = state.add_account(
            "stripe", "Stripe", "Disposable", "Test", {"secret_key": "sk_test_DELETE_OK"}, status="Verified"
        )
        reference = f"account:{account.id}"
        state.delete_account(account.id)
        self.assertNotIn(account.id, state.accounts)
        self.assertIsNone(self.credentials.get_credentials(reference))
        with closing(sqlite3.connect(self.db_path)) as connection:
            count = connection.execute("SELECT COUNT(*) FROM accounts WHERE id=?", (account.id,)).fetchone()[0]
        self.assertEqual(count, 0)

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
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 6)

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
            connection.execute(
                "INSERT INTO task_execution_snapshots (task_id, snapshot_state, provider_id, assignment_strategy) VALUES (?, ?, ?, ?)",
                ("task_conflict", "LegacyUnavailable", "stripe", "recipient_ordinal_round_robin_v1"),
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

    def test_failed_sqlite_connection_setup_closes_handle(self):
        connection = mock.MagicMock()
        connection.execute.side_effect = sqlite3.DatabaseError("corrupt")
        with mock.patch("src.core.storage.domain_store.sqlite3.connect", return_value=connection):
            with self.assertRaises(DomainStoreCorruptionError):
                DomainStore(self.root / "failed-open.sqlite3")
        connection.close.assert_called_once_with()


    def test_customer_record_round_trip_preserves_order_and_metadata(self):
        state = self.state()
        item = state.create_customer_list("Structured")
        state.add_customers(item.id, [
            CustomerRecord("one@example.com", "One", "US"),
            CustomerRecord("two@example.com", "", "BD"),
        ])
        loaded = self.store.load(self.credentials)
        restored = loaded.customer_lists[item.id]
        self.assertEqual(
            [(record.email, record.name, record.country) for record in restored.customers],
            [("one@example.com", "One", "US"), ("two@example.com", "", "BD")],
        )

    def test_schema_v2_migrates_to_v3_and_preserves_email_rows_with_blank_metadata(self):
        legacy = self.root / "legacy_v2.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            connection.executescript(SCHEMA_V1)
            connection.executescript(MIGRATION_V1_TO_V2)
            connection.execute("INSERT INTO customer_lists (id, name) VALUES ('list_old', 'Old')")
            connection.execute(
                "INSERT INTO customer_emails (list_id, ordinal, email) VALUES ('list_old', 0, 'old@example.com')"
            )
            connection.execute("PRAGMA user_version = 2")
            connection.commit()
        DomainStore(legacy)
        backup = legacy.with_name("legacy_v2.sqlite3.pre_migration_v2.bak")
        self.assertTrue(backup.exists())
        with closing(sqlite3.connect(legacy)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 6)
            row = connection.execute(
                "SELECT email, name, country FROM customer_emails WHERE list_id='list_old'"
            ).fetchone()
        self.assertEqual(row, ("old@example.com", "", ""))
        with closing(sqlite3.connect(backup)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 2)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(customer_emails)").fetchall()}
        self.assertNotIn("name", columns)
        self.assertNotIn("country", columns)

    def test_customer_record_persistence_failure_keeps_prior_list_unchanged(self):
        state = self.state()
        item = state.create_customer_list("Atomic")
        state.add_customers(item.id, [CustomerRecord("one@example.com", "One", "US")])
        original = self.store.replace_customer_records

        def fail(*_args, **_kwargs):
            from src.core.storage import DomainStoreError
            raise DomainStoreError("forced customer write failure")

        self.store.replace_customer_records = fail  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(StateError, "forced customer write failure"):
                state.add_customers(item.id, [CustomerRecord("two@example.com", "Two", "GB")])
        finally:
            self.store.replace_customer_records = original  # type: ignore[method-assign]
        self.assertEqual([(r.email, r.name, r.country) for r in item.customers], [("one@example.com", "One", "US")])
        loaded = self.store.load(self.credentials)
        self.assertEqual(loaded.customer_lists[item.id].emails, ["one@example.com"])


    def test_schema_v2_backup_includes_committed_wal_customer_state(self):
        legacy = self.root / "legacy_v2_wal.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            connection.executescript(SCHEMA_V1)
            connection.executescript(MIGRATION_V1_TO_V2)
            connection.execute("PRAGMA user_version = 2")
            connection.commit()

        writer = sqlite3.connect(legacy)
        try:
            writer.execute("PRAGMA journal_mode = WAL")
            writer.execute("PRAGMA wal_autocheckpoint = 0")
            writer.execute("INSERT INTO customer_lists (id, name) VALUES ('list_wal', 'WAL Customers')")
            writer.execute(
                "INSERT INTO customer_emails (list_id, ordinal, email) VALUES ('list_wal', 0, 'wal@example.com')"
            )
            writer.commit()
            self.assertTrue(Path(f"{legacy}-wal").exists())
            DomainStore(legacy)
        finally:
            writer.close()

        backup = legacy.with_name("legacy_v2_wal.sqlite3.pre_migration_v2.bak")
        with closing(sqlite3.connect(backup)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual(
                connection.execute("SELECT email FROM customer_emails WHERE list_id='list_wal'").fetchone()[0],
                "wal@example.com",
            )


class Phase3SendingControlStorageTests(unittest.TestCase):
    def test_schema_v5_migrates_to_v6_with_baseline_safe_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "domain.sqlite3"
            with sqlite3.connect(db_path) as connection:
                connection.executescript(SCHEMA_V1)
                connection.executescript(MIGRATION_V1_TO_V2)
                connection.executescript(MIGRATION_V2_TO_V3)
                connection.executescript(MIGRATION_V3_TO_V4)
                connection.executescript(MIGRATION_V4_TO_V5)
                connection.execute("PRAGMA user_version = 5")
                connection.commit()
            DomainStore(db_path)
            with sqlite3.connect(db_path) as connection:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 6)
                columns = {row[1] for row in connection.execute("PRAGMA table_info(task_execution_snapshots)")}
            self.assertTrue({
                "network_timeout_seconds", "max_automatic_attempts",
                "additional_recipient_delay_seconds", "rate_limit_per_account"
            }.issubset(columns))

    def test_phase3_task_controls_survive_restart(self):
        with tempfile.TemporaryDirectory() as td:
            backend = FakeKeyring()
            credentials = CredentialStore(backend)
            store = DomainStore(Path(td) / "domain.sqlite3")
            state = AppState(domain_store=store, credential_store=credentials, loaded=store.load(credentials))
            account = state.add_account(
                "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_x"}, status="Verified"
            )
            customer_list = state.create_customer_list("Customers")
            state.add_emails(customer_list.id, ["a@example.com"])
            template = state.save_invoice_template(
                template_id=None, name="Default", currency="USD", days_until_due=30, memo="", footer="",
                automatic_tax=False, reuse_customer=True, items=[("Service", "1", "10.00")],
            )
            controls = TaskSendingControls(60.0, 2, 2.5, 8.0)
            task = state.create_task(
                "stripe", "Stripe", [account.id], customer_list.id, template.id, sending_controls=controls
            )
            restored = AppState(domain_store=store, credential_store=credentials, loaded=store.load(credentials))
            self.assertEqual(restored.tasks[task.id].execution_snapshot.sending_controls, controls)


if __name__ == "__main__":
    unittest.main()


    def test_p07_failed_task_restart_preserves_status_but_disables_identity_based_retry(self):
        state, _account_id, _list_id, _template_id, task_id = self.populate()
        state.set_task_status(task_id, "Running", "Running")
        task = state.tasks[task_id]
        state.set_task_progress(task_id, processed=task.total, success=task.total - 1, failed=1)
        state.set_task_status(task_id, "Failed", "One recipient failed")

        loaded = self.store.load(self.credentials)
        restored = loaded.tasks[task_id]
        self.assertEqual(restored.status, "Failed")
        self.assertIn("exact failed recipient set is unavailable", restored.last_message)
        self.assertIn("Retry Failed is disabled", restored.last_message)

    def test_p07_stopped_task_restart_disables_identity_based_resume(self):
        state, _account_id, _list_id, _template_id, task_id = self.populate()
        state.set_task_status(task_id, "Running", "Running")
        state.set_task_progress(task_id, processed=1, success=1, failed=0)
        state.set_task_status(task_id, "Stopping", "Stop requested")
        state.set_task_status(task_id, "Stopped", "Stopped")

        loaded = self.store.load(self.credentials)
        restored = loaded.tasks[task_id]
        self.assertEqual(restored.status, "Stopped")
        self.assertIn("exact continuation recipient set is unavailable", restored.last_message)
        self.assertIn("Resume Remaining is disabled", restored.last_message)

    def test_p07_active_task_restart_recovers_as_stopped_without_fabricating_continuation(self):
        state, _account_id, _list_id, _template_id, task_id = self.populate()
        state.set_task_status(task_id, "Running", "Running")
        state.set_task_progress(task_id, processed=1, success=1, failed=0)

        loaded = self.store.load(self.credentials)
        restored = loaded.tasks[task_id]
        self.assertEqual(restored.status, "Stopped")
        self.assertIn("exact continuation recipient set is unavailable", restored.last_message)
        self.assertTrue(any("recovered as Stopped" in warning for warning in loaded.warnings))

    def test_p07_unknown_persisted_task_status_is_corruption(self):
        _state, _account_id, _list_id, _template_id, task_id = self.populate()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("UPDATE tasks SET status='Resending' WHERE id=?", (task_id,))
            connection.commit()
        with self.assertRaisesRegex(DomainStoreCorruptionError, "unsupported persisted status"):
            self.store.load(self.credentials)


class P05SnapshotStorageTests(unittest.TestCase):
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

    def populate(self, *, two_accounts: bool = False):
        state = self.state()
        first = state.add_account(
            "stripe", "Stripe", "First", "Test", {"secret_key": "sk_test_P05_FIRST"}, status="Verified"
        )
        accounts = [first]
        if two_accounts:
            accounts.append(
                state.add_account(
                    "stripe", "Stripe", "Second", "Test", {"secret_key": "sk_test_P05_SECOND"}, status="Verified"
                )
            )
        customer_list = state.create_customer_list("P05 Customers")
        state.add_customers(
            customer_list.id,
            [
                CustomerRecord("one@example.com", "One", "US"),
                CustomerRecord("two@example.com", "Two", "BD"),
            ],
        )
        template = state.save_invoice_template(
            template_id=None,
            name="P05 Template",
            currency="USD",
            days_until_due=30,
            memo="Original memo",
            footer="Original footer",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "2.50", "10.25", "7.5")],
            invoice_title="Original title",
            invoice_subtitle="Original subtitle",
            invoice_type="INVOICE",
            customer_note="Original note",
            terms=["Original term", "Second term"],
        )
        task = state.create_task(
            "stripe", "Stripe", [account.id for account in reversed(accounts)], customer_list.id, template.id
        )
        return state, accounts, customer_list, template, task

    def test_schema_v4_snapshot_tables_exist(self):
        with closing(sqlite3.connect(self.db_path)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 6)
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue(
            {
                "task_execution_snapshots",
                "task_snapshot_customers",
                "task_snapshot_template",
                "task_snapshot_template_items",
                "task_snapshot_template_terms",
            }.issubset(tables)
        )

    def test_captured_snapshot_round_trip_preserves_recipients_template_decimals_and_account_order(self):
        _state, accounts, _customer_list, _template, task = self.populate(two_accounts=True)
        loaded = self.store.load(self.credentials)
        restored = loaded.tasks[task.id]
        snapshot = restored.execution_snapshot
        self.assertTrue(restored.has_immutable_execution_snapshot)
        self.assertEqual(snapshot.account_ids, tuple(account.id for account in reversed(accounts)))
        self.assertEqual(
            [(record.email, record.name, record.country) for record in snapshot.customers],
            [("one@example.com", "One", "US"), ("two@example.com", "Two", "BD")],
        )
        self.assertEqual(restored.total, 2)
        self.assertEqual(snapshot.template.name, "P05 Template")
        self.assertEqual(snapshot.template.memo, "Original memo")
        self.assertEqual(str(snapshot.template.items[0].quantity), "2.50")
        self.assertEqual(str(snapshot.template.items[0].unit_amount), "10.25")
        self.assertEqual(str(snapshot.template.items[0].tax_rate), "7.5")
        self.assertEqual(snapshot.template.terms, ("Original term", "Second term"))

    def test_restart_uses_original_snapshot_after_source_list_and_template_change(self):
        state, _accounts, customer_list, template, task = self.populate()
        state.add_customers(customer_list.id, [CustomerRecord("three@example.com", "Three", "GB")])
        state.save_invoice_template(
            template_id=template.id,
            name=template.name,
            currency="EUR",
            days_until_due=14,
            memo="Edited memo",
            footer="Edited footer",
            automatic_tax=True,
            reuse_customer=False,
            items=[("Edited", "1", "99.00", "0")],
            invoice_title="Edited title",
            invoice_subtitle="Edited subtitle",
            invoice_type="BOS",
            customer_note="Edited note",
            terms=["Edited term"],
        )
        restored = self.store.load(self.credentials).tasks[task.id]
        snapshot = restored.execution_snapshot
        self.assertEqual(restored.total, 2)
        self.assertEqual([record.email for record in snapshot.customers], ["one@example.com", "two@example.com"])
        self.assertEqual(snapshot.template.currency, "USD")
        self.assertEqual(snapshot.template.memo, "Original memo")
        self.assertEqual(snapshot.template.items[0].description, "Service")
        self.assertEqual(snapshot.template.terms, ("Original term", "Second term"))

    def test_task_close_deletes_snapshot_rows_atomically(self):
        state, _accounts, _customer_list, _template, task = self.populate()
        state.close_task(task.id)
        with closing(sqlite3.connect(self.db_path)) as connection:
            for table in (
                "task_execution_snapshots",
                "task_snapshot_customers",
                "task_snapshot_template",
                "task_snapshot_template_items",
                "task_snapshot_template_terms",
            ):
                count = connection.execute(f"SELECT COUNT(*) FROM {table} WHERE task_id=?", (task.id,)).fetchone()[0]
                self.assertEqual(count, 0, table)

    def test_snapshot_total_mismatch_is_rejected_fail_closed(self):
        _state, _accounts, _customer_list, _template, task = self.populate()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("UPDATE tasks SET total=999 WHERE id=?", (task.id,))
            connection.commit()
        with self.assertRaisesRegex(DomainStoreCorruptionError, "total does not match"):
            self.store.load(self.credentials)

    def test_snapshot_provider_mismatch_is_rejected_fail_closed(self):
        _state, _accounts, _customer_list, _template, task = self.populate()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("UPDATE task_execution_snapshots SET provider_id='refrens' WHERE task_id=?", (task.id,))
            connection.commit()
        with self.assertRaisesRegex(DomainStoreCorruptionError, "provider does not match"):
            self.store.load(self.credentials)

    def test_partial_captured_snapshot_missing_template_is_rejected_fail_closed(self):
        _state, _accounts, _customer_list, _template, task = self.populate()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("DELETE FROM task_snapshot_template WHERE task_id=?", (task.id,))
            connection.commit()
        with self.assertRaisesRegex(DomainStoreCorruptionError, "exactly one invoice template"):
            self.store.load(self.credentials)

    def test_post_p05_task_without_captured_snapshot_is_rejected_instead_of_becoming_legacy(self):
        state, accounts, customer_list, template, existing = self.populate()
        state.close_task(existing.id)
        task = Task(
            id="task_missing_snapshot",
            name="Missing Snapshot",
            provider_id="stripe",
            provider_name="Stripe",
            account_ids=[accounts[0].id],
            account_names=[accounts[0].name],
            customer_list_id=customer_list.id,
            customer_list_name=customer_list.name,
            invoice_template_id=template.id,
            invoice_template_name=template.name,
            total=len(customer_list.customers),
        )
        with self.assertRaisesRegex(DomainStoreError, "captured immutable execution snapshot"):
            self.store.create_task_with_reservations(task)
        with closing(sqlite3.connect(self.db_path)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM tasks WHERE id=?", (task.id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM task_execution_snapshots WHERE task_id=?", (task.id,)).fetchone()[0], 0)

    def test_post_p05_legacy_snapshot_is_rejected_by_normal_task_creation_path(self):
        state, accounts, customer_list, template, existing = self.populate()
        state.close_task(existing.id)
        task = Task(
            id="task_false_legacy",
            name="False Legacy",
            provider_id="stripe",
            provider_name="Stripe",
            account_ids=[accounts[0].id],
            account_names=[accounts[0].name],
            customer_list_id=customer_list.id,
            customer_list_name=customer_list.name,
            invoice_template_id=template.id,
            invoice_template_name=template.name,
            total=len(customer_list.customers),
            execution_snapshot=TaskExecutionSnapshot.legacy_unavailable(
                provider_id="stripe",
                account_ids=[accounts[0].id],
            ),
        )
        with self.assertRaisesRegex(DomainStoreError, "LegacyUnavailable is reserved"):
            self.store.create_task_with_reservations(task)
        with closing(sqlite3.connect(self.db_path)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM tasks WHERE id=?", (task.id,)).fetchone()[0], 0)

    def test_captured_snapshot_load_rejects_progress_counter_drift(self):
        _state, _accounts, _customer_list, _template, task = self.populate()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                "UPDATE tasks SET processed=1, success=2, failed=0 WHERE id=?",
                (task.id,),
            )
            connection.commit()
        with self.assertRaisesRegex(DomainStoreCorruptionError, "success/failed progress"):
            self.store.load(self.credentials)

    def test_captured_snapshot_load_rejects_processed_count_beyond_recipient_total(self):
        _state, _accounts, _customer_list, _template, task = self.populate()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                "UPDATE tasks SET processed=999, success=999, failed=0 WHERE id=?",
                (task.id,),
            )
            connection.commit()
        with self.assertRaisesRegex(DomainStoreCorruptionError, "processed count is outside"):
            self.store.load(self.credentials)

    def test_task_status_update_does_not_persist_mutated_snapshot_total(self):
        state, _accounts, _customer_list, _template, task = self.populate()
        original_total = task.total
        task.total = original_total + 1
        with self.assertRaisesRegex(StateError, "Task total no longer matches"):
            state.set_task_status(task.id, "Ready", "Should not persist drift")
        with closing(sqlite3.connect(self.db_path)) as connection:
            stored_total = connection.execute("SELECT total FROM tasks WHERE id=?", (task.id,)).fetchone()[0]
        self.assertEqual(stored_total, original_total)

    def test_task_creation_snapshot_failure_rolls_back_task_accounts_and_reservations(self):
        state, accounts, customer_list, template, existing = self.populate()
        state.close_task(existing.id)
        bad_snapshot = TaskExecutionSnapshot.capture(
            provider_id="refrens",
            account_ids=[accounts[0].id],
            customers=customer_list.customers,
            template=template,
        )
        bad_task = Task(
            id="task_bad_snapshot",
            name="Bad Snapshot",
            provider_id="stripe",
            provider_name="Stripe",
            account_ids=[accounts[0].id],
            account_names=[accounts[0].name],
            customer_list_id=customer_list.id,
            customer_list_name=customer_list.name,
            invoice_template_id=template.id,
            invoice_template_name=template.name,
            total=len(customer_list.customers),
            execution_snapshot=bad_snapshot,
        )
        with self.assertRaisesRegex(DomainStoreError, "snapshot provider"):
            self.store.create_task_with_reservations(bad_task)
        with closing(sqlite3.connect(self.db_path)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM tasks WHERE id=?", (bad_task.id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM task_accounts WHERE task_id=?", (bad_task.id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM account_reservations WHERE task_id=?", (bad_task.id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM task_execution_snapshots WHERE task_id=?", (bad_task.id,)).fetchone()[0], 0)

    def _create_v3_database_with_task(self, path: Path) -> tuple[str, str]:
        account_id = "acct_legacy_p05"
        task_id = "task_legacy_p05"
        credential_ref = self.credentials.set_credentials(account_id, {"secret_key": "sk_test_LEGACY_P05"})
        with closing(sqlite3.connect(path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(SCHEMA_V1)
            connection.executescript(MIGRATION_V1_TO_V2)
            connection.executescript(MIGRATION_V2_TO_V3)
            connection.execute(
                """INSERT INTO accounts (
                       id, provider_id, provider_name, name, mode, status, credential_ref,
                       last_verification_at, verification_error_summary
                   ) VALUES (?, 'stripe', 'Stripe', 'Legacy Account', 'Test', 'Verified', ?, '', '')""",
                (account_id, credential_ref),
            )
            connection.execute("INSERT INTO customer_lists (id, name) VALUES ('list_legacy_p05', 'Legacy List')")
            connection.execute(
                "INSERT INTO customer_emails (list_id, ordinal, email, name, country) VALUES ('list_legacy_p05', 0, 'legacy@example.com', 'Legacy', 'US')"
            )
            connection.execute(
                """INSERT INTO invoice_templates (
                       id, name, currency, days_until_due, memo, footer, automatic_tax, reuse_customer,
                       invoice_title, invoice_subtitle, invoice_type, customer_note
                   ) VALUES ('tpl_legacy_p05', 'Legacy Template', 'USD', 30, 'Memo', 'Footer', 0, 1, 'Invoice', '', 'INVOICE', '')"""
            )
            connection.execute(
                "INSERT INTO invoice_template_items (template_id, ordinal, description, quantity, unit_amount, tax_rate) VALUES ('tpl_legacy_p05', 0, 'Service', '1', '10', '0')"
            )
            connection.execute(
                """INSERT INTO tasks (
                       id, name, provider_id, provider_name, customer_list_id, customer_list_name,
                       invoice_template_id, invoice_template_name, status, total, success, failed, processed, last_message
                   ) VALUES (?, 'Legacy Task', 'stripe', 'Stripe', 'list_legacy_p05', 'Legacy List',
                             'tpl_legacy_p05', 'Legacy Template', 'Ready', 1, 0, 0, 0, 'Ready')""",
                (task_id,),
            )
            connection.execute(
                "INSERT INTO task_accounts (task_id, ordinal, account_id, account_name) VALUES (?, 0, ?, 'Legacy Account')",
                (task_id, account_id),
            )
            connection.execute(
                "INSERT INTO account_reservations (account_id, task_id) VALUES (?, ?)",
                (account_id, task_id),
            )
            connection.execute("PRAGMA user_version = 3")
            connection.commit()
        return account_id, task_id

    def test_schema_v3_migration_preserves_task_as_legacy_without_fabricating_snapshot(self):
        legacy = self.root / "legacy_v3.sqlite3"
        account_id, task_id = self._create_v3_database_with_task(legacy)
        migrated = DomainStore(legacy)
        loaded = migrated.load(self.credentials)
        task = loaded.tasks[task_id]
        self.assertEqual(task.execution_snapshot.state, TASK_SNAPSHOT_LEGACY_UNAVAILABLE)
        self.assertFalse(task.has_immutable_execution_snapshot)
        self.assertEqual(task.execution_snapshot.customers, ())
        self.assertIsNone(task.execution_snapshot.template)
        self.assertEqual(loaded.account_reservations[account_id], task_id)
        with closing(sqlite3.connect(legacy)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 6)
            row = connection.execute(
                "SELECT snapshot_state, provider_id, assignment_strategy FROM task_execution_snapshots WHERE task_id=?",
                (task_id,),
            ).fetchone()
            customer_count = connection.execute(
                "SELECT COUNT(*) FROM task_snapshot_customers WHERE task_id=?", (task_id,)
            ).fetchone()[0]
            template_count = connection.execute(
                "SELECT COUNT(*) FROM task_snapshot_template WHERE task_id=?", (task_id,)
            ).fetchone()[0]
        self.assertEqual(row, ("LegacyUnavailable", "stripe", "recipient_ordinal_round_robin_v1"))
        self.assertEqual(customer_count, 0)
        self.assertEqual(template_count, 0)

        backup = legacy.with_name("legacy_v3.sqlite3.pre_migration_v3.bak")
        self.assertTrue(backup.exists())
        with closing(sqlite3.connect(backup)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 3)
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertNotIn("task_execution_snapshots", tables)
