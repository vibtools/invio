from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from ...accounts.models import Account
from ...customers.models import CustomerList, CustomerRecord
from ...invoices.templates import InvoiceItemTemplate, InvoiceTemplate
from ...tasks.models import Task
from .credential_store import CredentialStore, CredentialStoreError
from .schema import DOMAIN_SCHEMA_VERSION, MIGRATION_V1_TO_V2, MIGRATION_V2_TO_V3, SCHEMA_V1


class DomainStoreError(RuntimeError):
    """Raised when durable operational state cannot be loaded or committed safely."""


class DomainStoreCorruptionError(DomainStoreError):
    """Raised when the operational database is corrupt or internally inconsistent."""


class DomainStoreMigrationError(DomainStoreError):
    """Raised when a schema migration cannot be completed safely."""


@dataclass(slots=True)
class LoadedDomain:
    accounts: dict[str, Account] = field(default_factory=dict)
    customer_lists: dict[str, CustomerList] = field(default_factory=dict)
    invoice_templates: dict[str, InvoiceTemplate] = field(default_factory=dict)
    tasks: dict[str, Task] = field(default_factory=dict)
    account_reservations: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class DomainStore:
    """SQLite-backed durable store for non-sensitive Invio operational state."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DomainStoreError(f"Operational storage directory could not be created: {exc}") from exc
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(self.path, timeout=10.0)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA synchronous = FULL")
            return connection
        except sqlite3.OperationalError as exc:
            raise DomainStoreError(f"Operational storage could not be opened: {exc}") from exc
        except sqlite3.DatabaseError as exc:
            raise DomainStoreCorruptionError(f"Operational storage is unreadable and was not overwritten: {exc}") from exc
        except sqlite3.Error as exc:
            raise DomainStoreError(f"Operational storage could not be opened: {exc}") from exc

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        existed = self.path.exists()
        try:
            with self._connection() as connection:
                if existed:
                    result = connection.execute("PRAGMA quick_check").fetchone()
                    if result is None or str(result[0]).casefold() != "ok":
                        raise DomainStoreCorruptionError("Operational storage failed its integrity check and was not overwritten.")

                version = int(connection.execute("PRAGMA user_version").fetchone()[0])
                if version > DOMAIN_SCHEMA_VERSION:
                    raise DomainStoreMigrationError(
                        f"Operational storage schema {version} is newer than this Invio release supports ({DOMAIN_SCHEMA_VERSION})."
                    )
                if version < DOMAIN_SCHEMA_VERSION:
                    self._migrate(connection, version, backup_required=existed)
                journal_mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).casefold()
                if journal_mode != "wal":
                    raise DomainStoreError("Operational storage could not enable the required WAL journal mode.")
        except DomainStoreError:
            raise
        except sqlite3.DatabaseError as exc:
            raise DomainStoreCorruptionError(f"Operational storage is unreadable and was not overwritten: {exc}") from exc
        except OSError as exc:
            raise DomainStoreError(f"Operational storage could not be initialized: {exc}") from exc

    def _migrate(self, connection: sqlite3.Connection, version: int, *, backup_required: bool) -> None:
        if version not in {0, 1, 2}:
            raise DomainStoreMigrationError(f"No migration path exists from schema {version} to {DOMAIN_SCHEMA_VERSION}.")

        if version == 0:
            existing_tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            }
            if existing_tables:
                raise DomainStoreMigrationError(
                    "Operational storage has an unversioned schema and cannot be migrated automatically."
                )

        if backup_required and self.path.exists():
            self._create_migration_backup(version, connection)

        scripts: list[str] = []
        if version == 0:
            scripts.append(SCHEMA_V1)
            scripts.append(MIGRATION_V1_TO_V2)
            scripts.append(MIGRATION_V2_TO_V3)
        elif version == 1:
            scripts.append(MIGRATION_V1_TO_V2)
            scripts.append(MIGRATION_V2_TO_V3)
        elif version == 2:
            scripts.append(MIGRATION_V2_TO_V3)

        script = f"BEGIN IMMEDIATE;\n{'\n'.join(scripts)}\nPRAGMA user_version = {DOMAIN_SCHEMA_VERSION};\nCOMMIT;"
        try:
            connection.executescript(script)
        except sqlite3.Error as exc:
            if connection.in_transaction:
                connection.rollback()
            raise DomainStoreMigrationError(
                f"Operational storage migration failed; prior data was preserved: {exc}"
            ) from exc

    def _create_migration_backup(self, version: int, source: sqlite3.Connection) -> None:
        backup = self.path.with_name(f"{self.path.name}.pre_migration_v{version}.bak")
        temporary = backup.with_name(f"{backup.name}.tmp")
        try:
            if temporary.exists():
                temporary.unlink()
            destination = sqlite3.connect(temporary)
            try:
                source.backup(destination)
            finally:
                # sqlite3.Connection's context-manager protocol commits or
                # rolls back but does not close the connection. On Windows, an
                # open destination handle prevents replacing the temporary
                # backup file (WinError 32). Close it explicitly before the
                # atomic rename.
                destination.close()
            temporary.replace(backup)
        except (OSError, sqlite3.Error) as exc:
            raise DomainStoreMigrationError(f"Could not create the pre-migration backup: {exc}") from exc
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def _transaction(self, callback) -> None:
        try:
            with self._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    callback(connection)
                    connection.commit()
                except Exception:
                    if connection.in_transaction:
                        connection.rollback()
                    raise
        except DomainStoreError:
            raise
        except sqlite3.Error as exc:
            raise DomainStoreError(f"Operational state could not be saved; the prior valid transaction was retained: {exc}") from exc
        except Exception as exc:
            raise DomainStoreError(f"Operational state could not be saved; the prior valid transaction was retained: {exc}") from exc

    def load(self, credential_store: CredentialStore) -> LoadedDomain:
        loaded = LoadedDomain()
        verification_recovery_updates: list[tuple[str, str, str, str]] = []
        recovery_updates: list[tuple[str, str, str]] = []
        try:
            with self._connection() as connection:
                account_rows = connection.execute(
                    "SELECT id, provider_id, provider_name, name, mode, status, credential_ref, last_verification_at, verification_error_summary FROM accounts ORDER BY rowid"
                ).fetchall()
                for row in account_rows:
                    status = str(row["status"])
                    last_verification_at = str(row["last_verification_at"])
                    verification_error_summary = str(row["verification_error_summary"])
                    credentials: dict[str, str] = {}
                    try:
                        restored = credential_store.get_credentials(str(row["credential_ref"]))
                    except CredentialStoreError as exc:
                        status = "Not Verified"
                        verification_error_summary = "Protected credentials are unavailable."
                        verification_recovery_updates.append(
                            (status, last_verification_at, verification_error_summary, str(row["id"]))
                        )
                        loaded.warnings.append(f"Account '{row['name']}' credentials are unavailable; the account was restored as Not Verified. ({exc})")
                    else:
                        if restored is None:
                            status = "Not Verified"
                            verification_error_summary = "Protected credentials are unavailable."
                            verification_recovery_updates.append(
                                (status, last_verification_at, verification_error_summary, str(row["id"]))
                            )
                            loaded.warnings.append(
                                f"Account '{row['name']}' has no protected credential entry; the account was restored as Not Verified."
                            )
                        else:
                            credentials = restored
                    account = Account(
                        id=str(row["id"]),
                        provider_id=str(row["provider_id"]),
                        provider_name=str(row["provider_name"]),
                        name=str(row["name"]),
                        mode=str(row["mode"]),
                        status=status,
                        credentials=credentials,
                        last_verification_at=last_verification_at,
                        verification_error_summary=verification_error_summary,
                    )
                    loaded.accounts[account.id] = account

                for row in connection.execute("SELECT id, name FROM customer_lists ORDER BY rowid").fetchall():
                    item = CustomerList(id=str(row["id"]), name=str(row["name"]))
                    customer_rows = connection.execute(
                        "SELECT email, name, country FROM customer_emails WHERE list_id=? ORDER BY ordinal",
                        (item.id,),
                    ).fetchall()
                    item.customers = [
                        CustomerRecord(
                            email=str(customer_row["email"]),
                            name=str(customer_row["name"]),
                            country=str(customer_row["country"]),
                        )
                        for customer_row in customer_rows
                    ]
                    loaded.customer_lists[item.id] = item

                for row in connection.execute("SELECT * FROM invoice_templates ORDER BY rowid").fetchall():
                    template_id = str(row["id"])
                    item_rows = connection.execute(
                        "SELECT description, quantity, unit_amount, tax_rate FROM invoice_template_items WHERE template_id=? ORDER BY ordinal",
                        (template_id,),
                    ).fetchall()
                    term_rows = connection.execute(
                        "SELECT term FROM invoice_template_terms WHERE template_id=? ORDER BY ordinal",
                        (template_id,),
                    ).fetchall()
                    template = InvoiceTemplate(
                        id=template_id,
                        name=str(row["name"]),
                        currency=str(row["currency"]),
                        days_until_due=int(row["days_until_due"]),
                        memo=str(row["memo"]),
                        footer=str(row["footer"]),
                        automatic_tax=bool(row["automatic_tax"]),
                        reuse_customer=bool(row["reuse_customer"]),
                        items=[
                            InvoiceItemTemplate(
                                description=str(item_row["description"]),
                                quantity=Decimal(str(item_row["quantity"])),
                                unit_amount=Decimal(str(item_row["unit_amount"])),
                                tax_rate=Decimal(str(item_row["tax_rate"])),
                            )
                            for item_row in item_rows
                        ],
                        invoice_title=str(row["invoice_title"]),
                        invoice_subtitle=str(row["invoice_subtitle"]),
                        invoice_type=str(row["invoice_type"]),
                        customer_note=str(row["customer_note"]),
                        terms=[str(term_row["term"]) for term_row in term_rows],
                    )
                    loaded.invoice_templates[template.id] = template

                for row in connection.execute("SELECT * FROM tasks ORDER BY rowid").fetchall():
                    task_id = str(row["id"])
                    account_rows_for_task = connection.execute(
                        "SELECT account_id, account_name FROM task_accounts WHERE task_id=? ORDER BY ordinal",
                        (task_id,),
                    ).fetchall()
                    status = str(row["status"])
                    last_message = str(row["last_message"])
                    if status in {"Running", "Paused", "Stopping"}:
                        status = "Stopped"
                        last_message = "Recovered after application restart; task was not automatically resumed."
                        recovery_updates.append((status, last_message, task_id))
                        loaded.warnings.append(f"{row['name']} was active when Invio last stopped and was recovered as Stopped.")
                    task = Task(
                        id=task_id,
                        name=str(row["name"]),
                        provider_id=str(row["provider_id"]),
                        provider_name=str(row["provider_name"]),
                        account_ids=[str(account_row["account_id"]) for account_row in account_rows_for_task],
                        account_names=[str(account_row["account_name"]) for account_row in account_rows_for_task],
                        customer_list_id=str(row["customer_list_id"]),
                        customer_list_name=str(row["customer_list_name"]),
                        invoice_template_id=str(row["invoice_template_id"]),
                        invoice_template_name=str(row["invoice_template_name"]),
                        status=status,
                        total=int(row["total"]),
                        success=int(row["success"]),
                        failed=int(row["failed"]),
                        processed=int(row["processed"]),
                        last_message=last_message,
                    )
                    loaded.tasks[task.id] = task

                reservation_rows = connection.execute(
                    "SELECT account_id, task_id FROM account_reservations ORDER BY account_id"
                ).fetchall()
                loaded.account_reservations = {
                    str(row["account_id"]): str(row["task_id"])
                    for row in reservation_rows
                }
                self._validate_loaded(loaded)
        except DomainStoreError:
            raise
        except (sqlite3.Error, ValueError, ArithmeticError, TypeError, KeyError) as exc:
            raise DomainStoreCorruptionError(f"Operational storage contains invalid data: {exc}") from exc

        if verification_recovery_updates or recovery_updates:
            def persist_recovery(connection: sqlite3.Connection) -> None:
                if verification_recovery_updates:
                    connection.executemany(
                        """UPDATE accounts
                           SET status=?, last_verification_at=?, verification_error_summary=?
                           WHERE id=?""",
                        verification_recovery_updates,
                    )
                connection.executemany(
                    "UPDATE tasks SET status=?, last_message=? WHERE id=?",
                    recovery_updates,
                )

            self._transaction(persist_recovery)
        return loaded

    @staticmethod
    def _validate_loaded(loaded: LoadedDomain) -> None:
        expected_reservations: dict[str, str] = {}
        for task in loaded.tasks.values():
            if task.customer_list_id not in loaded.customer_lists:
                raise DomainStoreCorruptionError(f"Task '{task.name}' references a missing customer list.")
            if task.invoice_template_id not in loaded.invoice_templates:
                raise DomainStoreCorruptionError(f"Task '{task.name}' references a missing invoice template.")
            for account_id in task.account_ids:
                if account_id not in loaded.accounts:
                    raise DomainStoreCorruptionError(f"Task '{task.name}' references a missing account.")
                reserved_by = expected_reservations.get(account_id)
                if reserved_by is not None and reserved_by != task.id:
                    raise DomainStoreCorruptionError(
                        "An account is selected by more than one persisted task, so reservation exclusivity cannot be restored safely."
                    )
                expected_reservations[account_id] = task.id

        for account_id, task_id in loaded.account_reservations.items():
            if account_id not in loaded.accounts or task_id not in loaded.tasks:
                raise DomainStoreCorruptionError("An account reservation references missing operational state.")
            if account_id not in loaded.tasks[task_id].account_ids:
                raise DomainStoreCorruptionError("An account reservation does not match its task account selection.")

        if loaded.account_reservations != expected_reservations:
            raise DomainStoreCorruptionError(
                "Persisted task-account selections and account reservations do not match exactly; operational storage was not loaded."
            )

    def save_account(self, account: Account, credential_ref: str) -> None:
        def write(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO accounts (
                       id, provider_id, provider_name, name, mode, status, credential_ref,
                       last_verification_at, verification_error_summary
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    account.id, account.provider_id, account.provider_name, account.name, account.mode,
                    account.status, credential_ref, account.last_verification_at, account.verification_error_summary,
                ),
            )
        self._transaction(write)

    def update_account(self, account: Account) -> None:
        def write(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """UPDATE accounts
                   SET name=?, mode=?, status=?, last_verification_at=?, verification_error_summary=?
                   WHERE id=?""",
                (
                    account.name, account.mode, account.status, account.last_verification_at,
                    account.verification_error_summary, account.id,
                ),
            )
            if cursor.rowcount != 1:
                raise sqlite3.IntegrityError("Account row is missing.")
        self._transaction(write)

    def update_account_verification(
        self,
        account_id: str,
        *,
        status: str,
        last_verification_at: str,
        verification_error_summary: str,
    ) -> None:
        def write(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """UPDATE accounts
                   SET status=?, last_verification_at=?, verification_error_summary=?
                   WHERE id=?""",
                (status, last_verification_at, verification_error_summary, account_id),
            )
            if cursor.rowcount != 1:
                raise sqlite3.IntegrityError("Account row is missing.")
        self._transaction(write)

    def delete_account(self, account_id: str) -> None:
        def write(connection: sqlite3.Connection) -> None:
            cursor = connection.execute("DELETE FROM accounts WHERE id=?", (account_id,))
            if cursor.rowcount != 1:
                raise sqlite3.IntegrityError("Account row is missing.")
        self._transaction(write)

    def create_customer_list(self, item: CustomerList) -> None:
        self._transaction(lambda connection: connection.execute("INSERT INTO customer_lists (id, name) VALUES (?, ?)", (item.id, item.name)))

    def replace_customer_records(self, item: CustomerList) -> None:
        def write(connection: sqlite3.Connection) -> None:
            connection.execute("DELETE FROM customer_emails WHERE list_id=?", (item.id,))
            connection.executemany(
                "INSERT INTO customer_emails (list_id, ordinal, email, name, country) VALUES (?, ?, ?, ?, ?)",
                [
                    (item.id, ordinal, customer.email, customer.name, customer.country)
                    for ordinal, customer in enumerate(item.customers)
                ],
            )
        self._transaction(write)

    def replace_customer_emails(self, item: CustomerList) -> None:
        """Backward-compatible email-only persistence wrapper."""
        self.replace_customer_records(item)

    def delete_customer_list(self, list_id: str) -> None:
        self._transaction(lambda connection: connection.execute("DELETE FROM customer_lists WHERE id=?", (list_id,)))

    def save_invoice_template(self, template: InvoiceTemplate) -> None:
        def write(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO invoice_templates (
                       id, name, currency, days_until_due, memo, footer, automatic_tax, reuse_customer,
                       invoice_title, invoice_subtitle, invoice_type, customer_note
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       name=excluded.name,
                       currency=excluded.currency,
                       days_until_due=excluded.days_until_due,
                       memo=excluded.memo,
                       footer=excluded.footer,
                       automatic_tax=excluded.automatic_tax,
                       reuse_customer=excluded.reuse_customer,
                       invoice_title=excluded.invoice_title,
                       invoice_subtitle=excluded.invoice_subtitle,
                       invoice_type=excluded.invoice_type,
                       customer_note=excluded.customer_note""",
                (
                    template.id, template.name, template.currency, template.days_until_due, template.memo, template.footer,
                    int(template.automatic_tax), int(template.reuse_customer), template.invoice_title,
                    template.invoice_subtitle, template.invoice_type, template.customer_note,
                ),
            )
            connection.execute("DELETE FROM invoice_template_items WHERE template_id=?", (template.id,))
            connection.executemany(
                "INSERT INTO invoice_template_items (template_id, ordinal, description, quantity, unit_amount, tax_rate) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (template.id, ordinal, item.description, str(item.quantity), str(item.unit_amount), str(item.tax_rate))
                    for ordinal, item in enumerate(template.items)
                ],
            )
            connection.execute("DELETE FROM invoice_template_terms WHERE template_id=?", (template.id,))
            connection.executemany(
                "INSERT INTO invoice_template_terms (template_id, ordinal, term) VALUES (?, ?, ?)",
                [(template.id, ordinal, term) for ordinal, term in enumerate(template.terms)],
            )
        self._transaction(write)

    def delete_invoice_template(self, template_id: str) -> None:
        self._transaction(lambda connection: connection.execute("DELETE FROM invoice_templates WHERE id=?", (template_id,)))

    def create_task_with_reservations(self, task: Task) -> None:
        def write(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO tasks (
                       id, name, provider_id, provider_name, customer_list_id, customer_list_name,
                       invoice_template_id, invoice_template_name, status, total, success, failed, processed, last_message
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.id, task.name, task.provider_id, task.provider_name, task.customer_list_id, task.customer_list_name,
                    task.invoice_template_id, task.invoice_template_name, task.status, task.total, task.success,
                    task.failed, task.processed, task.last_message,
                ),
            )
            connection.executemany(
                "INSERT INTO task_accounts (task_id, ordinal, account_id, account_name) VALUES (?, ?, ?, ?)",
                [
                    (task.id, ordinal, account_id, task.account_names[ordinal])
                    for ordinal, account_id in enumerate(task.account_ids)
                ],
            )
            connection.executemany(
                "INSERT INTO account_reservations (account_id, task_id) VALUES (?, ?)",
                [(account_id, task.id) for account_id in task.account_ids],
            )
        self._transaction(write)

    def delete_task_and_release(self, task_id: str) -> None:
        def write(connection: sqlite3.Connection) -> None:
            connection.execute("DELETE FROM account_reservations WHERE task_id=?", (task_id,))
            connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self._transaction(write)

    def update_task(self, task: Task) -> None:
        def write(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """UPDATE tasks SET status=?, total=?, success=?, failed=?, processed=?, last_message=? WHERE id=?""",
                (task.status, task.total, task.success, task.failed, task.processed, task.last_message, task.id),
            )
            if cursor.rowcount != 1:
                raise sqlite3.IntegrityError("Task row is missing.")
        self._transaction(write)
