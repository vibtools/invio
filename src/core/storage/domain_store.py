from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from ...accounts.models import Account
from ...customers.models import CustomerList, CustomerRecord
from ...invoices.templates import InvoiceItemTemplate, InvoiceTemplate
from ...tasks.delivery_ledger import (
    DELIVERY_OPERATION_FAILED,
    DELIVERY_OPERATION_STARTED,
    DELIVERY_OPERATION_SUCCEEDED,
    DELIVERY_OPERATION_UNCERTAIN,
    DELIVERY_RESULT_FAILED,
    DELIVERY_RESULT_PENDING,
    DELIVERY_RESULT_SUCCEEDED,
    DELIVERY_RESULT_UNCERTAIN,
    DELIVERY_RUN_COMPLETED,
    DELIVERY_RUN_FAILED,
    DELIVERY_RUN_INTERRUPTED,
    DELIVERY_RUN_RUNNING,
    DELIVERY_RUN_STOPPED,
    DeliveryLedgerSummary,
    DeliveryRunRecord,
    RecipientDeliveryReportRecord,
    is_mutating_delivery_stage,
)
from ...tasks.models import (
    TASK_ASSIGNMENT_STRATEGY,
    TASK_SNAPSHOT_CAPTURED,
    TASK_SNAPSHOT_LEGACY_UNAVAILABLE,
    Task,
    TaskExecutionSnapshot,
    TaskInvoiceItemSnapshot,
    TaskInvoiceTemplateSnapshot,
)
from ...tasks.state_machine import TASK_STATUSES
from .credential_store import CredentialStore, CredentialStoreError
from .schema import (
    DOMAIN_SCHEMA_VERSION,
    MIGRATION_V1_TO_V2,
    MIGRATION_V2_TO_V3,
    MIGRATION_V3_TO_V4,
    MIGRATION_V4_TO_V5,
    SCHEMA_V1,
)


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
        if version not in {0, 1, 2, 3, 4}:
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
            scripts.append(MIGRATION_V3_TO_V4)
            scripts.append(MIGRATION_V4_TO_V5)
        elif version == 1:
            scripts.append(MIGRATION_V1_TO_V2)
            scripts.append(MIGRATION_V2_TO_V3)
            scripts.append(MIGRATION_V3_TO_V4)
            scripts.append(MIGRATION_V4_TO_V5)
        elif version == 2:
            scripts.append(MIGRATION_V2_TO_V3)
            scripts.append(MIGRATION_V3_TO_V4)
            scripts.append(MIGRATION_V4_TO_V5)
        elif version == 3:
            scripts.append(MIGRATION_V3_TO_V4)
            scripts.append(MIGRATION_V4_TO_V5)
        elif version == 4:
            scripts.append(MIGRATION_V4_TO_V5)

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

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _has_unresolved_mutating_uncertainty(
        connection: sqlite3.Connection,
        *,
        task_id: str,
        recipient_ordinal: int,
    ) -> bool:
        """Return whether durable history still contains an unresolved mutating ambiguity.

        A later successful operation only reconciles an earlier Started/Uncertain
        mutation when it has the exact same stage and non-empty idempotency key.
        Deterministic failures do not erase prior ambiguity.
        """
        rows = connection.execute(
            """SELECT r.run_number, o.attempt_number, o.stage, o.status, o.idempotency_key
               FROM task_delivery_operations AS o
               JOIN task_delivery_runs AS r ON r.run_id=o.run_id
               WHERE r.task_id=? AND o.recipient_ordinal=?
               ORDER BY r.run_number, o.attempt_number, o.rowid""",
            (task_id, recipient_ordinal),
        ).fetchall()
        unresolved: set[tuple[str, str]] = set()
        for row in rows:
            stage = str(row["stage"])
            if not is_mutating_delivery_stage(stage):
                continue
            status = str(row["status"])
            idempotency_key = str(row["idempotency_key"])
            identity = (stage, idempotency_key)
            if status in {DELIVERY_OPERATION_STARTED, DELIVERY_OPERATION_UNCERTAIN}:
                unresolved.add(identity)
            elif status == DELIVERY_OPERATION_SUCCEEDED and idempotency_key:
                unresolved.discard(identity)
        return bool(unresolved)

    @staticmethod
    def _delivery_summary_from_connection(
        connection: sqlite3.Connection,
        task: Task,
    ) -> DeliveryLedgerSummary | None:
        run_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM task_delivery_runs WHERE task_id=?",
                (task.id,),
            ).fetchone()[0]
        )
        if run_count == 0:
            return None

        snapshot = task.execution_snapshot
        if snapshot is None or snapshot.state != TASK_SNAPSHOT_CAPTURED:
            return DeliveryLedgerSummary(
                task_id=task.id,
                has_history=True,
                continuation_safe=False,
                succeeded_recipients=(),
                failed_recipients=(),
                pending_recipients=(),
                uncertain_recipients=(),
                assigned_account_ids=(),
                processed=task.processed,
                success=task.success,
                failed=task.failed,
                remaining=task.remaining,
            )

        expected = tuple(customer.email for customer in snapshot.customers)
        known_accounts = set(snapshot.account_ids)
        rows = connection.execute(
            """SELECT r.run_number, d.*
               FROM task_delivery_recipients AS d
               JOIN task_delivery_runs AS r ON r.run_id=d.run_id
               WHERE r.task_id=?
               ORDER BY r.run_number, d.recipient_ordinal""",
            (task.id,),
        ).fetchall()
        latest: dict[int, sqlite3.Row] = {}
        historical_bindings: dict[int, set[str]] = {}
        history_safe = True
        for row in rows:
            ordinal = int(row["recipient_ordinal"])
            latest[ordinal] = row
            if ordinal < 0 or ordinal >= len(expected):
                history_safe = False
                continue
            if str(row["recipient_email"]) != expected[ordinal] or str(row["provider_id"]) != task.provider_id:
                history_safe = False
            expected_primary = snapshot.account_ids[ordinal % len(snapshot.account_ids)]
            if str(row["primary_account_id"]) != expected_primary:
                history_safe = False
            assigned = str(row["assigned_account_id"])
            if assigned:
                historical_bindings.setdefault(ordinal, set()).add(assigned)
                if assigned not in known_accounts:
                    history_safe = False
        if any(len(values) > 1 for values in historical_bindings.values()):
            history_safe = False

        succeeded: list[str] = []
        failed: list[str] = []
        pending: list[str] = []
        uncertain: list[str] = []
        bindings: list[tuple[str, str]] = []
        safe = history_safe and len(latest) == len(expected)

        for ordinal, email in enumerate(expected):
            row = latest.get(ordinal)
            if row is None:
                safe = False
                pending.append(email)
                continue
            if str(row["recipient_email"]) != email or str(row["provider_id"]) != task.provider_id:
                safe = False
            assigned_account_id = str(row["assigned_account_id"])
            if assigned_account_id:
                if assigned_account_id not in known_accounts:
                    safe = False
                bindings.append((email, assigned_account_id))

            result = str(row["final_result"])
            if result == DELIVERY_RESULT_PENDING:
                operation_rows = connection.execute(
                    """SELECT stage, status FROM task_delivery_operations
                       WHERE run_id=? AND recipient_ordinal=?""",
                    (str(row["run_id"]), ordinal),
                ).fetchall()
                if any(
                    str(operation["stage"]) == "invoice_send"
                    and str(operation["status"]) == DELIVERY_OPERATION_SUCCEEDED
                    for operation in operation_rows
                ):
                    result = DELIVERY_RESULT_SUCCEEDED
                elif any(
                    str(operation["status"]) in {DELIVERY_OPERATION_STARTED, DELIVERY_OPERATION_UNCERTAIN}
                    and is_mutating_delivery_stage(str(operation["stage"]))
                    for operation in operation_rows
                ):
                    result = DELIVERY_RESULT_UNCERTAIN

            if result != DELIVERY_RESULT_SUCCEEDED and DomainStore._has_unresolved_mutating_uncertainty(
                connection,
                task_id=task.id,
                recipient_ordinal=ordinal,
            ):
                result = DELIVERY_RESULT_UNCERTAIN

            if result == DELIVERY_RESULT_SUCCEEDED:
                succeeded.append(email)
            elif result == DELIVERY_RESULT_FAILED:
                failed.append(email)
            elif result == DELIVERY_RESULT_UNCERTAIN:
                uncertain.append(email)
            elif result == DELIVERY_RESULT_PENDING:
                pending.append(email)
            else:
                safe = False
                pending.append(email)

        processed = len(succeeded) + len(failed)
        return DeliveryLedgerSummary(
            task_id=task.id,
            has_history=True,
            continuation_safe=safe,
            succeeded_recipients=tuple(succeeded),
            failed_recipients=tuple(failed),
            pending_recipients=tuple(pending),
            uncertain_recipients=tuple(uncertain),
            assigned_account_ids=tuple(bindings),
            processed=processed,
            success=len(succeeded),
            failed=len(failed),
            remaining=len(pending) + len(uncertain),
        )

    @staticmethod
    def _recover_interrupted_delivery_ledger(connection: sqlite3.Connection) -> list[str]:
        now = DomainStore._utc_now()
        interrupted = connection.execute(
            "SELECT run_id, task_id, task_name FROM task_delivery_runs WHERE status=?",
            (DELIVERY_RUN_RUNNING,),
        ).fetchall()
        if not interrupted:
            return []

        warnings: list[str] = []
        for run in interrupted:
            run_id = str(run["run_id"])
            started = connection.execute(
                """SELECT recipient_ordinal, stage FROM task_delivery_operations
                   WHERE run_id=? AND status=?""",
                (run_id, DELIVERY_OPERATION_STARTED),
            ).fetchall()
            for operation in started:
                ordinal = int(operation["recipient_ordinal"])
                stage = str(operation["stage"])
                connection.execute(
                    """UPDATE task_delivery_operations
                       SET status=?, finished_at=?, error_class=?, error_code=?, error_message=?
                       WHERE run_id=? AND recipient_ordinal=? AND stage=? AND status=?""",
                    (
                        DELIVERY_OPERATION_UNCERTAIN,
                        now,
                        "InterruptedOperation",
                        "process_interruption",
                        "Application exited before this provider operation outcome was durably confirmed.",
                        run_id,
                        ordinal,
                        stage,
                        DELIVERY_OPERATION_STARTED,
                    ),
                )
                if is_mutating_delivery_stage(stage):
                    connection.execute(
                        """UPDATE task_delivery_recipients
                           SET status=?, final_result=?, stage=?, updated_at=?, finished_at=?,
                               error_class=?, error_code=?, error_message=?
                           WHERE run_id=? AND recipient_ordinal=? AND final_result=?""",
                        (
                            DELIVERY_RESULT_UNCERTAIN,
                            DELIVERY_RESULT_UNCERTAIN,
                            stage,
                            now,
                            now,
                            "InterruptedOperation",
                            "process_interruption",
                            "A side-effecting provider operation was in flight when Invio stopped; the outcome is uncertain.",
                            run_id,
                            ordinal,
                            DELIVERY_RESULT_PENDING,
                        ),
                    )

            recipient_rows = connection.execute(
                """SELECT recipient_ordinal, final_result FROM task_delivery_recipients
                   WHERE run_id=?""",
                (run_id,),
            ).fetchall()
            for recipient in recipient_rows:
                ordinal = int(recipient["recipient_ordinal"])
                if str(recipient["final_result"]) != DELIVERY_RESULT_PENDING:
                    continue
                send_success = connection.execute(
                    """SELECT 1 FROM task_delivery_operations
                       WHERE run_id=? AND recipient_ordinal=? AND stage='invoice_send' AND status=? LIMIT 1""",
                    (run_id, ordinal, DELIVERY_OPERATION_SUCCEEDED),
                ).fetchone()
                if send_success is not None:
                    connection.execute(
                        """UPDATE task_delivery_recipients
                           SET status=?, final_result=?, stage='invoice_send', updated_at=?, finished_at=?
                           WHERE run_id=? AND recipient_ordinal=?""",
                        (
                            DELIVERY_RESULT_SUCCEEDED,
                            DELIVERY_RESULT_SUCCEEDED,
                            now,
                            now,
                            run_id,
                            ordinal,
                        ),
                    )
                    continue
                latest_operation = connection.execute(
                    """SELECT status, stage, error_class, error_code, error_message
                       FROM task_delivery_operations
                       WHERE run_id=? AND recipient_ordinal=?
                       ORDER BY attempt_number DESC, started_at DESC LIMIT 1""",
                    (run_id, ordinal),
                ).fetchone()
                if latest_operation is not None and str(latest_operation["status"]) == DELIVERY_OPERATION_FAILED:
                    connection.execute(
                        """UPDATE task_delivery_recipients
                           SET status=?, final_result=?, stage=?, updated_at=?, finished_at=?,
                               error_class=?, error_code=?, error_message=?
                           WHERE run_id=? AND recipient_ordinal=?""",
                        (
                            DELIVERY_RESULT_FAILED,
                            DELIVERY_RESULT_FAILED,
                            str(latest_operation["stage"]),
                            now,
                            now,
                            str(latest_operation["error_class"]),
                            str(latest_operation["error_code"]),
                            str(latest_operation["error_message"]),
                            run_id,
                            ordinal,
                        ),
                    )

            connection.execute(
                "UPDATE task_delivery_runs SET status=?, finished_at=? WHERE run_id=?",
                (DELIVERY_RUN_INTERRUPTED, now, run_id),
            )
            warnings.append(
                f"{run['task_name']} delivery run {run_id} was interrupted and recovered from its durable delivery ledger."
            )
        connection.commit()
        return warnings

    def begin_delivery_run(
        self,
        task: Task,
        *,
        execution_mode: str,
        recipients: tuple[str, ...],
    ) -> DeliveryRunRecord:
        snapshot = task.execution_snapshot
        if snapshot is None or snapshot.state != TASK_SNAPSHOT_CAPTURED:
            raise DomainStoreError("A durable delivery run requires a captured immutable Task snapshot.")
        if not recipients:
            raise DomainStoreError("A durable delivery run requires at least one recipient.")
        run_id = f"run_{uuid.uuid4().hex}"
        started_at = self._utc_now()
        result: dict[str, int] = {}

        def write(connection: sqlite3.Connection) -> None:
            running = connection.execute(
                "SELECT run_id FROM task_delivery_runs WHERE task_id=? AND status=? LIMIT 1",
                (task.id, DELIVERY_RUN_RUNNING),
            ).fetchone()
            if running is not None:
                raise sqlite3.IntegrityError(
                    "A prior durable delivery run is still marked Running; restart Invio to reconcile it before continuing."
                )
            run_number = int(
                connection.execute(
                    "SELECT COALESCE(MAX(run_number), 0) + 1 FROM task_delivery_runs WHERE task_id=?",
                    (task.id,),
                ).fetchone()[0]
            )
            result["run_number"] = run_number
            connection.execute(
                """INSERT INTO task_delivery_runs (
                       run_id, task_id, task_name, run_number, provider_id, execution_mode, status, started_at, finished_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '')""",
                (
                    run_id,
                    task.id,
                    task.name,
                    run_number,
                    task.provider_id,
                    execution_mode,
                    DELIVERY_RUN_RUNNING,
                    started_at,
                ),
            )
            email_to_ordinal = {customer.email: ordinal for ordinal, customer in enumerate(snapshot.customers)}
            account_names = {
                account_id: task.account_names[index]
                for index, account_id in enumerate(task.account_ids)
            }
            rows: list[tuple[object, ...]] = []
            for email in recipients:
                ordinal = email_to_ordinal.get(email)
                if ordinal is None:
                    raise sqlite3.IntegrityError("Delivery recipient is not present in the immutable Task snapshot.")
                primary_account_id = snapshot.account_ids[ordinal % len(snapshot.account_ids)]
                prior = connection.execute(
                    """SELECT d.assigned_account_id, d.assigned_account_name
                       FROM task_delivery_recipients AS d
                       JOIN task_delivery_runs AS r ON r.run_id=d.run_id
                       WHERE r.task_id=? AND d.recipient_ordinal=? AND d.assigned_account_id<>''
                       ORDER BY r.run_number DESC LIMIT 1""",
                    (task.id, ordinal),
                ).fetchone()
                assigned_account_id = str(prior["assigned_account_id"]) if prior is not None else ""
                assigned_account_name = str(prior["assigned_account_name"]) if prior is not None else ""
                if assigned_account_id and assigned_account_id not in snapshot.account_ids:
                    raise sqlite3.IntegrityError("Prior durable recipient account binding is outside the frozen Task account set.")
                rows.append(
                    (
                        run_id,
                        ordinal,
                        email,
                        task.provider_id,
                        primary_account_id,
                        account_names[primary_account_id],
                        assigned_account_id,
                        assigned_account_name,
                        "",
                        DELIVERY_RESULT_PENDING,
                        0,
                        "",
                        "",
                        "",
                        started_at,
                        "",
                        "",
                        "",
                        "",
                        DELIVERY_RESULT_PENDING,
                    )
                )
            connection.executemany(
                """INSERT INTO task_delivery_recipients (
                       run_id, recipient_ordinal, recipient_email, provider_id,
                       primary_account_id, primary_account_name, assigned_account_id, assigned_account_name,
                       stage, status, attempt_number, provider_customer_id, provider_invoice_id,
                       started_at, updated_at, finished_at, error_class, error_code, error_message, final_result
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )

        self._transaction(write)
        return DeliveryRunRecord(
            run_id=run_id,
            task_id=task.id,
            task_name=task.name,
            run_number=result["run_number"],
            provider_id=task.provider_id,
            execution_mode=execution_mode,
            status=DELIVERY_RUN_RUNNING,
            started_at=started_at,
        )

    def finish_delivery_run(self, run_id: str, *, status: str) -> None:
        if status not in {
            DELIVERY_RUN_COMPLETED,
            DELIVERY_RUN_STOPPED,
            DELIVERY_RUN_FAILED,
            DELIVERY_RUN_INTERRUPTED,
        }:
            raise DomainStoreError(f"Unsupported delivery-run terminal status '{status}'.")
        finished_at = self._utc_now()

        def write(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                "UPDATE task_delivery_runs SET status=?, finished_at=? WHERE run_id=?",
                (status, finished_at, run_id),
            )
            if cursor.rowcount != 1:
                raise sqlite3.IntegrityError("Delivery run row is missing.")

        self._transaction(write)

    def begin_delivery_operation(
        self,
        *,
        run_id: str,
        recipient_ordinal: int,
        attempt_number: int,
        stage: str,
        account_id: str,
        account_name: str,
        idempotency_key: str,
    ) -> None:
        started_at = self._utc_now()

        def write(connection: sqlite3.Connection) -> None:
            recipient = connection.execute(
                """SELECT assigned_account_id FROM task_delivery_recipients
                   WHERE run_id=? AND recipient_ordinal=?""",
                (run_id, recipient_ordinal),
            ).fetchone()
            if recipient is None:
                raise sqlite3.IntegrityError("Delivery recipient row is missing.")
            existing = str(recipient["assigned_account_id"])
            if existing and existing != account_id:
                raise sqlite3.IntegrityError(
                    "Durable recipient account binding cannot change after provider execution begins."
                )
            connection.execute(
                """UPDATE task_delivery_recipients
                   SET assigned_account_id=?, assigned_account_name=?, stage=?, status='Running',
                       attempt_number=?, started_at=CASE WHEN started_at='' THEN ? ELSE started_at END,
                       updated_at=?
                   WHERE run_id=? AND recipient_ordinal=?""",
                (
                    account_id,
                    account_name,
                    stage,
                    attempt_number,
                    started_at,
                    started_at,
                    run_id,
                    recipient_ordinal,
                ),
            )
            connection.execute(
                """INSERT INTO task_delivery_operations (
                       run_id, recipient_ordinal, attempt_number, stage, status, idempotency_key,
                       provider_reference, started_at, finished_at, error_class, error_code, error_message
                   ) VALUES (?, ?, ?, ?, ?, ?, '', ?, '', '', '', '')""",
                (
                    run_id,
                    recipient_ordinal,
                    attempt_number,
                    stage,
                    DELIVERY_OPERATION_STARTED,
                    idempotency_key,
                    started_at,
                ),
            )

        self._transaction(write)

    def finish_delivery_operation(
        self,
        *,
        run_id: str,
        recipient_ordinal: int,
        attempt_number: int,
        stage: str,
        status: str,
        provider_reference: str = "",
        error_class: str = "",
        error_code: str = "",
        error_message: str = "",
    ) -> None:
        if status not in {
            DELIVERY_OPERATION_SUCCEEDED,
            DELIVERY_OPERATION_FAILED,
            DELIVERY_OPERATION_UNCERTAIN,
        }:
            raise DomainStoreError(f"Unsupported delivery-operation status '{status}'.")
        finished_at = self._utc_now()

        def write(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """UPDATE task_delivery_operations
                   SET status=?, provider_reference=?, finished_at=?, error_class=?, error_code=?, error_message=?
                   WHERE run_id=? AND recipient_ordinal=? AND attempt_number=? AND stage=? AND status=?""",
                (
                    status,
                    provider_reference,
                    finished_at,
                    error_class,
                    error_code,
                    error_message,
                    run_id,
                    recipient_ordinal,
                    attempt_number,
                    stage,
                    DELIVERY_OPERATION_STARTED,
                ),
            )
            if cursor.rowcount != 1:
                raise sqlite3.IntegrityError("Started delivery operation row is missing or already finalized.")
            customer_reference = provider_reference if stage in {"customer_lookup", "customer_create"} else None
            invoice_reference = provider_reference if stage in {
                "invoice_create",
                "invoice_finalize",
                "invoice_send",
                "refrens_invoice_create_email",
            } else None
            if customer_reference is not None:
                connection.execute(
                    """UPDATE task_delivery_recipients
                       SET stage=?, attempt_number=?, updated_at=?, provider_customer_id=CASE WHEN ?<>'' THEN ? ELSE provider_customer_id END
                       WHERE run_id=? AND recipient_ordinal=?""",
                    (stage, attempt_number, finished_at, customer_reference, customer_reference, run_id, recipient_ordinal),
                )
            elif invoice_reference is not None:
                connection.execute(
                    """UPDATE task_delivery_recipients
                       SET stage=?, attempt_number=?, updated_at=?, provider_invoice_id=CASE WHEN ?<>'' THEN ? ELSE provider_invoice_id END
                       WHERE run_id=? AND recipient_ordinal=?""",
                    (stage, attempt_number, finished_at, invoice_reference, invoice_reference, run_id, recipient_ordinal),
                )
            else:
                connection.execute(
                    """UPDATE task_delivery_recipients
                       SET stage=?, attempt_number=?, updated_at=?
                       WHERE run_id=? AND recipient_ordinal=?""",
                    (stage, attempt_number, finished_at, run_id, recipient_ordinal),
                )

        self._transaction(write)

    def update_delivery_provider_ids(
        self,
        *,
        run_id: str,
        recipient_ordinal: int,
        provider_customer_id: str | None = None,
        provider_invoice_id: str | None = None,
    ) -> None:
        if provider_customer_id is None and provider_invoice_id is None:
            return
        updated_at = self._utc_now()

        def write(connection: sqlite3.Connection) -> None:
            row = connection.execute(
                "SELECT provider_customer_id, provider_invoice_id FROM task_delivery_recipients WHERE run_id=? AND recipient_ordinal=?",
                (run_id, recipient_ordinal),
            ).fetchone()
            if row is None:
                raise sqlite3.IntegrityError("Delivery recipient row is missing.")
            next_customer = str(row["provider_customer_id"]) if provider_customer_id is None else provider_customer_id
            next_invoice = str(row["provider_invoice_id"]) if provider_invoice_id is None else provider_invoice_id
            connection.execute(
                """UPDATE task_delivery_recipients
                   SET provider_customer_id=?, provider_invoice_id=?, updated_at=?
                   WHERE run_id=? AND recipient_ordinal=?""",
                (next_customer, next_invoice, updated_at, run_id, recipient_ordinal),
            )

        self._transaction(write)

    def finish_delivery_recipient(
        self,
        *,
        run_id: str,
        recipient_ordinal: int,
        final_result: str,
        stage: str,
        attempt_number: int,
        error_class: str = "",
        error_code: str = "",
        error_message: str = "",
    ) -> None:
        if final_result not in {
            DELIVERY_RESULT_SUCCEEDED,
            DELIVERY_RESULT_FAILED,
            DELIVERY_RESULT_UNCERTAIN,
        }:
            raise DomainStoreError(f"Unsupported recipient delivery result '{final_result}'.")
        finished_at = self._utc_now()

        def write(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """UPDATE task_delivery_recipients
                   SET stage=CASE WHEN ?<>'' THEN ? ELSE stage END, status=?, attempt_number=?, updated_at=?, finished_at=?,
                       error_class=?, error_code=?, error_message=?, final_result=?
                   WHERE run_id=? AND recipient_ordinal=?""",
                (
                    stage,
                    stage,
                    final_result,
                    attempt_number,
                    finished_at,
                    finished_at,
                    error_class,
                    error_code,
                    error_message,
                    final_result,
                    run_id,
                    recipient_ordinal,
                ),
            )
            if cursor.rowcount != 1:
                raise sqlite3.IntegrityError("Delivery recipient row is missing.")

        self._transaction(write)

    @staticmethod
    def _delivery_send_stage(provider_id: str) -> str:
        normalized = str(provider_id).strip().lower()
        if normalized == "stripe":
            return "invoice_send"
        if normalized == "refrens":
            return "refrens_invoice_create_email"
        return ""

    def recipient_delivery_report(self) -> tuple[RecipientDeliveryReportRecord, ...]:
        """Return privacy-bounded recipient reconciliation rows from the P10 ledger.

        The report deliberately uses only durable delivery evidence. Customer
        names/countries and credentials are not selected into this support view.
        """
        try:
            with self._connection() as connection:
                recipient_rows = connection.execute(
                    """SELECT r.task_id, r.task_name, r.run_number, r.provider_id AS run_provider_id, d.*
                       FROM task_delivery_recipients AS d
                       JOIN task_delivery_runs AS r ON r.run_id=d.run_id
                       ORDER BY r.task_id, d.recipient_ordinal, r.run_number"""
                ).fetchall()
                if not recipient_rows:
                    return ()

                operation_rows = connection.execute(
                    """SELECT r.task_id, r.run_number, o.run_id, o.recipient_ordinal, o.attempt_number,
                              o.stage, o.status, o.idempotency_key, o.provider_reference, o.error_code, o.rowid AS operation_rowid
                       FROM task_delivery_operations AS o
                       JOIN task_delivery_runs AS r ON r.run_id=o.run_id
                       ORDER BY r.task_id, o.recipient_ordinal, r.run_number, o.attempt_number, o.rowid"""
                ).fetchall()

                grouped_recipients: dict[tuple[str, int], list[sqlite3.Row]] = {}
                for row in recipient_rows:
                    key = (str(row["task_id"]), int(row["recipient_ordinal"]))
                    grouped_recipients.setdefault(key, []).append(row)

                grouped_operations: dict[tuple[str, int], list[sqlite3.Row]] = {}
                for row in operation_rows:
                    key = (str(row["task_id"]), int(row["recipient_ordinal"]))
                    grouped_operations.setdefault(key, []).append(row)

                report: list[RecipientDeliveryReportRecord] = []
                for key, history in grouped_recipients.items():
                    latest = history[-1]
                    task_id, _ordinal = key
                    email = str(latest["recipient_email"])
                    provider_id = str(latest["provider_id"])
                    if any(str(row["recipient_email"]) != email or str(row["provider_id"]) != provider_id for row in history):
                        raise sqlite3.IntegrityError(
                            "Delivery report history contains conflicting recipient/provider identity."
                        )

                    operations = grouped_operations.get(key, [])
                    attempts = {
                        (str(row["run_id"]), int(row["attempt_number"]))
                        for row in operations
                        if int(row["attempt_number"]) > 0
                    }

                    unresolved: dict[tuple[str, str], sqlite3.Row] = {}
                    for operation in operations:
                        stage = str(operation["stage"])
                        if not is_mutating_delivery_stage(stage):
                            continue
                        status = str(operation["status"])
                        idempotency_key = str(operation["idempotency_key"])
                        identity = (stage, idempotency_key)
                        if status in {DELIVERY_OPERATION_STARTED, DELIVERY_OPERATION_UNCERTAIN}:
                            unresolved[identity] = operation
                        elif status == DELIVERY_OPERATION_SUCCEEDED and idempotency_key:
                            unresolved.pop(identity, None)

                    final_result = str(latest["final_result"])
                    if final_result != DELIVERY_RESULT_SUCCEEDED and unresolved:
                        final_result = DELIVERY_RESULT_UNCERTAIN
                    safe_status = {
                        DELIVERY_RESULT_PENDING: "Pending",
                        DELIVERY_RESULT_SUCCEEDED: "Provider Accepted",
                        DELIVERY_RESULT_FAILED: "Failed",
                        DELIVERY_RESULT_UNCERTAIN: "Uncertain",
                    }.get(final_result, "Uncertain")

                    assigned = next(
                        (
                            row
                            for row in reversed(history)
                            if str(row["assigned_account_id"]).strip()
                        ),
                        None,
                    )
                    if assigned is not None:
                        account_id = str(assigned["assigned_account_id"])
                        account_name = str(assigned["assigned_account_name"])
                        account_reference = f"{account_name} ({account_id})" if account_name else account_id
                    else:
                        account_id = str(latest["primary_account_id"])
                        account_name = str(latest["primary_account_name"])
                        base = f"{account_name} ({account_id})" if account_name else account_id
                        account_reference = f"{base} [planned]"

                    provider_invoice_reference = ""
                    for row in reversed(history):
                        value = str(row["provider_invoice_id"]).strip()
                        if value:
                            provider_invoice_reference = value
                            break

                    last_stage = str(latest["stage"])
                    error_code = str(latest["error_code"])
                    if safe_status == "Uncertain" and unresolved:
                        uncertain_operation = max(
                            unresolved.values(),
                            key=lambda row: (
                                int(row["run_number"]),
                                int(row["attempt_number"]),
                                int(row["operation_rowid"]),
                            ),
                        )
                        last_stage = str(uncertain_operation["stage"])
                        error_code = str(uncertain_operation["error_code"])

                    send_stage = self._delivery_send_stage(provider_id)
                    send_operations = [row for row in operations if str(row["stage"]) == send_stage] if send_stage else []
                    send_unresolved: dict[tuple[str, str], sqlite3.Row] = {}
                    send_succeeded = False
                    send_failed = False
                    for operation in send_operations:
                        status = str(operation["status"])
                        idempotency_key = str(operation["idempotency_key"])
                        identity = (str(operation["stage"]), idempotency_key)
                        if status in {DELIVERY_OPERATION_STARTED, DELIVERY_OPERATION_UNCERTAIN}:
                            send_unresolved[identity] = operation
                        elif status == DELIVERY_OPERATION_SUCCEEDED:
                            send_succeeded = True
                            if idempotency_key:
                                send_unresolved.pop(identity, None)
                        elif status == DELIVERY_OPERATION_FAILED:
                            send_failed = True

                    if final_result == DELIVERY_RESULT_SUCCEEDED or (send_succeeded and not send_unresolved):
                        provider_send_acceptance = "Accepted"
                    elif send_unresolved:
                        provider_send_acceptance = "Uncertain"
                    elif send_failed:
                        provider_send_acceptance = "Failed"
                    else:
                        provider_send_acceptance = "Not Reached"

                    email_delivery = (
                        "Not independently confirmed"
                        if provider_send_acceptance in {"Accepted", "Uncertain"}
                        else "Not confirmed"
                    )
                    report.append(
                        RecipientDeliveryReportRecord(
                            task_id=task_id,
                            task_name=str(latest["task_name"]),
                            recipient_email=email,
                            provider_id=provider_id,
                            safe_status=safe_status,
                            attempts=len(attempts),
                            account_reference=account_reference,
                            provider_invoice_reference=provider_invoice_reference,
                            last_stage=last_stage,
                            error_code=error_code,
                            provider_send_acceptance=provider_send_acceptance,
                            email_delivery=email_delivery,
                        )
                    )
                return tuple(report)
        except DomainStoreError:
            raise
        except (sqlite3.Error, ValueError, TypeError, KeyError) as exc:
            raise DomainStoreError(f"Recipient delivery report could not be read safely: {exc}") from exc

    def clear_closed_delivery_history(self) -> tuple[int, int]:
        """Delete only ledger history whose Task no longer exists.

        Active/open Task rows remain protected because restart/recovery depends on
        them. Child recipient/operation rows are removed by the existing schema-v5
        ON DELETE CASCADE relationships.
        """
        result: dict[str, int] = {"tasks": 0, "runs": 0}

        def write(connection: sqlite3.Connection) -> None:
            row = connection.execute(
                """SELECT COUNT(DISTINCT task_id) AS task_count, COUNT(*) AS run_count
                   FROM task_delivery_runs
                   WHERE task_id NOT IN (SELECT id FROM tasks)"""
            ).fetchone()
            result["tasks"] = int(row["task_count"] if row is not None else 0)
            result["runs"] = int(row["run_count"] if row is not None else 0)
            connection.execute(
                "DELETE FROM task_delivery_runs WHERE task_id NOT IN (SELECT id FROM tasks)"
            )

        self._transaction(write)
        return result["tasks"], result["runs"]

    def delivery_summary(self, task: Task) -> DeliveryLedgerSummary | None:
        try:
            with self._connection() as connection:
                return self._delivery_summary_from_connection(connection, task)
        except DomainStoreError:
            raise
        except (sqlite3.Error, ValueError, TypeError, KeyError) as exc:
            raise DomainStoreError(f"Delivery ledger could not be read safely: {exc}") from exc

    def recipient_has_uncertain_mutation(self, *, run_id: str, recipient_ordinal: int) -> bool:
        try:
            with self._connection() as connection:
                run = connection.execute(
                    "SELECT task_id FROM task_delivery_runs WHERE run_id=?",
                    (run_id,),
                ).fetchone()
                if run is None:
                    raise sqlite3.IntegrityError("Delivery run row is missing.")
                return self._has_unresolved_mutating_uncertainty(
                    connection,
                    task_id=str(run["task_id"]),
                    recipient_ordinal=recipient_ordinal,
                )
        except sqlite3.Error as exc:
            raise DomainStoreError(f"Delivery uncertainty state could not be read safely: {exc}") from exc

    @staticmethod
    def _load_task_execution_snapshot(
        connection: sqlite3.Connection,
        *,
        task_id: str,
        task_provider_id: str,
        account_ids: list[str],
    ) -> TaskExecutionSnapshot:
        row = connection.execute(
            "SELECT snapshot_state, provider_id, assignment_strategy FROM task_execution_snapshots WHERE task_id=?",
            (task_id,),
        ).fetchone()
        if row is None:
            raise DomainStoreCorruptionError(
                f"Task '{task_id}' has no execution-snapshot metadata; operational storage was not loaded."
            )

        state = str(row["snapshot_state"])
        provider_id = str(row["provider_id"])
        assignment_strategy = str(row["assignment_strategy"])
        if provider_id != task_provider_id:
            raise DomainStoreCorruptionError(
                f"Task '{task_id}' execution snapshot provider does not match the task provider."
            )
        if assignment_strategy != TASK_ASSIGNMENT_STRATEGY:
            raise DomainStoreCorruptionError(
                f"Task '{task_id}' uses an unsupported account-assignment strategy."
            )

        customer_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM task_snapshot_customers WHERE task_id=?", (task_id,)
            ).fetchone()[0]
        )
        template_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM task_snapshot_template WHERE task_id=?", (task_id,)
            ).fetchone()[0]
        )
        item_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM task_snapshot_template_items WHERE task_id=?", (task_id,)
            ).fetchone()[0]
        )
        term_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM task_snapshot_template_terms WHERE task_id=?", (task_id,)
            ).fetchone()[0]
        )

        if state == TASK_SNAPSHOT_LEGACY_UNAVAILABLE:
            if customer_count or template_count or item_count or term_count:
                raise DomainStoreCorruptionError(
                    f"Legacy task '{task_id}' contains partial immutable snapshot data."
                )
            return TaskExecutionSnapshot.legacy_unavailable(
                provider_id=provider_id,
                account_ids=account_ids,
            )

        if state != TASK_SNAPSHOT_CAPTURED:
            raise DomainStoreCorruptionError(
                f"Task '{task_id}' has an unknown execution-snapshot state."
            )
        if customer_count <= 0:
            raise DomainStoreCorruptionError(
                f"Task '{task_id}' immutable snapshot has no recipients."
            )
        if template_count != 1:
            raise DomainStoreCorruptionError(
                f"Task '{task_id}' immutable snapshot does not contain exactly one invoice template."
            )
        if item_count <= 0:
            raise DomainStoreCorruptionError(
                f"Task '{task_id}' immutable snapshot has no invoice items."
            )

        customer_rows = connection.execute(
            "SELECT email, name, country FROM task_snapshot_customers WHERE task_id=? ORDER BY ordinal",
            (task_id,),
        ).fetchall()
        template_row = connection.execute(
            "SELECT * FROM task_snapshot_template WHERE task_id=?",
            (task_id,),
        ).fetchone()
        if template_row is None:
            raise DomainStoreCorruptionError(
                f"Task '{task_id}' immutable template snapshot is missing."
            )
        item_rows = connection.execute(
            "SELECT description, quantity, unit_amount, tax_rate FROM task_snapshot_template_items WHERE task_id=? ORDER BY ordinal",
            (task_id,),
        ).fetchall()
        term_rows = connection.execute(
            "SELECT term FROM task_snapshot_template_terms WHERE task_id=? ORDER BY ordinal",
            (task_id,),
        ).fetchall()

        template = TaskInvoiceTemplateSnapshot(
            id=str(template_row["template_id"]),
            name=str(template_row["name"]),
            currency=str(template_row["currency"]),
            days_until_due=int(template_row["days_until_due"]),
            memo=str(template_row["memo"]),
            footer=str(template_row["footer"]),
            automatic_tax=bool(template_row["automatic_tax"]),
            reuse_customer=bool(template_row["reuse_customer"]),
            items=tuple(
                TaskInvoiceItemSnapshot(
                    description=str(item_row["description"]),
                    quantity=Decimal(str(item_row["quantity"])),
                    unit_amount=Decimal(str(item_row["unit_amount"])),
                    tax_rate=Decimal(str(item_row["tax_rate"])),
                )
                for item_row in item_rows
            ),
            invoice_title=str(template_row["invoice_title"]),
            invoice_subtitle=str(template_row["invoice_subtitle"]),
            invoice_type=str(template_row["invoice_type"]),
            customer_note=str(template_row["customer_note"]),
            terms=tuple(str(term_row["term"]) for term_row in term_rows),
        )
        return TaskExecutionSnapshot(
            state=TASK_SNAPSHOT_CAPTURED,
            provider_id=provider_id,
            account_ids=tuple(account_ids),
            assignment_strategy=assignment_strategy,
            customers=tuple(
                CustomerRecord(
                    email=str(customer_row["email"]),
                    name=str(customer_row["name"]),
                    country=str(customer_row["country"]),
                )
                for customer_row in customer_rows
            ),
            template=template,
        )

    def load(self, credential_store: CredentialStore) -> LoadedDomain:
        loaded = LoadedDomain()
        verification_recovery_updates: list[tuple[str, str, str, str]] = []
        recovery_updates: list[tuple[str, str, str]] = []
        counter_recovery_updates: list[tuple[int, int, int, str]] = []
        try:
            with self._connection() as connection:
                loaded.warnings.extend(self._recover_interrupted_delivery_ledger(connection))
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
                    persisted_status = str(row["status"])
                    status = persisted_status
                    last_message = str(row["last_message"])
                    processed_value = int(row["processed"])
                    success_value = int(row["success"])
                    failed_value = int(row["failed"])
                    total_value = int(row["total"])
                    account_ids_for_task = [str(account_row["account_id"]) for account_row in account_rows_for_task]
                    execution_snapshot = self._load_task_execution_snapshot(
                        connection,
                        task_id=task_id,
                        task_provider_id=str(row["provider_id"]),
                        account_ids=account_ids_for_task,
                    )
                    task = Task(
                        id=task_id,
                        name=str(row["name"]),
                        provider_id=str(row["provider_id"]),
                        provider_name=str(row["provider_name"]),
                        account_ids=account_ids_for_task,
                        account_names=[str(account_row["account_name"]) for account_row in account_rows_for_task],
                        customer_list_id=str(row["customer_list_id"]),
                        customer_list_name=str(row["customer_list_name"]),
                        invoice_template_id=str(row["invoice_template_id"]),
                        invoice_template_name=str(row["invoice_template_name"]),
                        status=status,
                        total=total_value,
                        success=success_value,
                        failed=failed_value,
                        processed=processed_value,
                        last_message=last_message,
                        execution_snapshot=execution_snapshot,
                    )

                    ledger = self._delivery_summary_from_connection(connection, task)
                    if ledger is not None:
                        if not ledger.continuation_safe:
                            raise DomainStoreCorruptionError(
                                f"Task '{task.name}' durable delivery ledger is internally inconsistent."
                            )
                        if (
                            task.processed > ledger.processed
                            or task.success > ledger.success
                            or task.failed > ledger.failed
                        ):
                            raise DomainStoreCorruptionError(
                                f"Task '{task.name}' aggregate progress is ahead of its durable delivery evidence."
                            )
                        if (
                            task.processed != ledger.processed
                            or task.success != ledger.success
                            or task.failed != ledger.failed
                        ):
                            task.processed = ledger.processed
                            task.success = ledger.success
                            task.failed = ledger.failed
                            counter_recovery_updates.append(
                                (task.success, task.failed, task.processed, task.id)
                            )

                        if ledger.pending_recipients or ledger.uncertain_recipients:
                            status = "Stopped"
                            last_message = (
                                "Recovered durable delivery state after restart: "
                                f"{ledger.success} succeeded, {ledger.failed} failed, "
                                f"{len(ledger.pending_recipients)} pending, "
                                f"{len(ledger.uncertain_recipients)} uncertain. "
                                "Use Resume Remaining to continue only unresolved recipients."
                            )
                        elif ledger.failed_recipients:
                            status = "Failed"
                            last_message = (
                                "Recovered durable delivery state after restart: "
                                f"{ledger.success} succeeded and {ledger.failed} failed. "
                                "Use Retry Failed to retry only the durable failed recipient set."
                            )
                        elif ledger.success == task.total:
                            status = "Completed"
                            last_message = "Recovered durable delivery state: all recipients are confirmed succeeded."
                        else:
                            status = persisted_status

                        if task.status != status or task.last_message != last_message:
                            task.status = status
                            task.last_message = last_message
                            recovery_updates.append((status, last_message, task.id))
                        if persisted_status in {"Running", "Paused", "Stopping"}:
                            loaded.warnings.append(
                                f"{task.name} was active when Invio last stopped and was recovered from its durable delivery ledger."
                            )
                    else:
                        # Pre-P10 Tasks have no fabricated delivery evidence. Preserve
                        # the P07 fail-closed restart behavior for non-pristine history.
                        if status in {"Running", "Paused", "Stopping"}:
                            status = "Stopped"
                            last_message = (
                                "Recovered after application restart; this pre-P10 Task has no durable delivery ledger, "
                                "so Resume Remaining is disabled."
                            )
                            recovery_updates.append((status, last_message, task_id))
                            loaded.warnings.append(
                                f"{row['name']} was active when Invio last stopped and was recovered as Stopped without fabricated P10 history."
                            )
                        elif status == "Stopped" and (failed_value > 0 or processed_value < total_value):
                            last_message = (
                                "Recovered after application restart; this pre-P10 Task has no durable delivery ledger, "
                                "so Resume Remaining is disabled."
                            )
                            recovery_updates.append((status, last_message, task_id))
                        elif status == "Failed" and failed_value > 0:
                            last_message = (
                                "Recovered after application restart; this pre-P10 Task has no durable delivery ledger, "
                                "so Retry Failed is disabled."
                            )
                            recovery_updates.append((status, last_message, task_id))
                        task.status = status
                        task.last_message = last_message

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

        if verification_recovery_updates or recovery_updates or counter_recovery_updates:
            def persist_recovery(connection: sqlite3.Connection) -> None:
                if verification_recovery_updates:
                    connection.executemany(
                        """UPDATE accounts
                           SET status=?, last_verification_at=?, verification_error_summary=?
                           WHERE id=?""",
                        verification_recovery_updates,
                    )
                if recovery_updates:
                    connection.executemany(
                        "UPDATE tasks SET status=?, last_message=? WHERE id=?",
                        recovery_updates,
                    )
                if counter_recovery_updates:
                    connection.executemany(
                        "UPDATE tasks SET success=?, failed=?, processed=? WHERE id=?",
                        counter_recovery_updates,
                    )

            self._transaction(persist_recovery)
        return loaded

    @staticmethod
    def _validate_loaded(loaded: LoadedDomain) -> None:
        expected_reservations: dict[str, str] = {}
        for task in loaded.tasks.values():
            if task.status not in TASK_STATUSES:
                raise DomainStoreCorruptionError(
                    f"Task '{task.name}' has unsupported persisted status '{task.status}'."
                )
            if task.customer_list_id not in loaded.customer_lists:
                raise DomainStoreCorruptionError(f"Task '{task.name}' references a missing customer list.")
            if task.invoice_template_id not in loaded.invoice_templates:
                raise DomainStoreCorruptionError(f"Task '{task.name}' references a missing invoice template.")

            snapshot = task.execution_snapshot
            if snapshot is None:
                raise DomainStoreCorruptionError(f"Task '{task.name}' has no execution-snapshot state.")
            if snapshot.provider_id != task.provider_id:
                raise DomainStoreCorruptionError(f"Task '{task.name}' snapshot provider does not match the task provider.")
            if snapshot.assignment_strategy != TASK_ASSIGNMENT_STRATEGY:
                raise DomainStoreCorruptionError(f"Task '{task.name}' snapshot assignment strategy is unsupported.")
            if tuple(task.account_ids) != snapshot.account_ids:
                raise DomainStoreCorruptionError(f"Task '{task.name}' snapshot account order does not match the task account order.")
            if snapshot.state == TASK_SNAPSHOT_CAPTURED:
                if snapshot.template is None:
                    raise DomainStoreCorruptionError(f"Task '{task.name}' captured snapshot has no invoice template.")
                if snapshot.template.id != task.invoice_template_id:
                    raise DomainStoreCorruptionError(f"Task '{task.name}' captured template does not match the assigned template ID.")
                if snapshot.template.name != task.invoice_template_name:
                    raise DomainStoreCorruptionError(f"Task '{task.name}' captured template name does not match the task binding.")
                if task.total != len(snapshot.customers):
                    raise DomainStoreCorruptionError(
                        f"Task '{task.name}' total does not match its immutable recipient snapshot."
                    )
                if not snapshot.customers:
                    raise DomainStoreCorruptionError(f"Task '{task.name}' captured snapshot has no recipients.")
                if task.processed < 0 or task.processed > task.total:
                    raise DomainStoreCorruptionError(
                        f"Task '{task.name}' processed count is outside its immutable recipient snapshot."
                    )
                if task.success < 0 or task.failed < 0 or task.success + task.failed != task.processed:
                    raise DomainStoreCorruptionError(
                        f"Task '{task.name}' success/failed progress does not match its processed recipient count."
                    )
            elif snapshot.state != TASK_SNAPSHOT_LEGACY_UNAVAILABLE:
                raise DomainStoreCorruptionError(f"Task '{task.name}' has an unknown execution-snapshot state.")

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

    @staticmethod
    def _write_task_execution_snapshot(connection: sqlite3.Connection, task: Task) -> None:
        snapshot = task.execution_snapshot
        if snapshot is None or snapshot.state != TASK_SNAPSHOT_CAPTURED:
            raise ValueError(
                "New tasks must contain a captured immutable execution snapshot; "
                "LegacyUnavailable is reserved for migrated pre-P05 tasks."
            )
        if snapshot.provider_id != task.provider_id:
            raise ValueError("Task execution snapshot provider does not match the task provider.")
        if snapshot.account_ids != tuple(task.account_ids):
            raise ValueError("Task execution snapshot account order does not match the task account order.")
        if snapshot.assignment_strategy != TASK_ASSIGNMENT_STRATEGY:
            raise ValueError("Task execution snapshot uses an unsupported account-assignment strategy.")
        if not snapshot.account_ids:
            raise ValueError("Captured task execution snapshot must contain at least one account assignment.")
        if not snapshot.customers:
            raise ValueError("Captured task execution snapshot must contain at least one recipient.")

        connection.execute(
            "INSERT INTO task_execution_snapshots (task_id, snapshot_state, provider_id, assignment_strategy) VALUES (?, ?, ?, ?)",
            (task.id, snapshot.state, snapshot.provider_id, snapshot.assignment_strategy),
        )
        if task.total != len(snapshot.customers):
            raise ValueError("Task total must equal the immutable execution-snapshot recipient count.")
        if snapshot.template is None:
            raise ValueError("Captured task execution snapshot must contain an invoice template.")
        if not snapshot.template.items:
            raise ValueError("Captured task execution snapshot must contain at least one invoice item.")
        if snapshot.template.id != task.invoice_template_id:
            raise ValueError("Captured task execution snapshot template does not match the task binding.")
        if snapshot.template.name != task.invoice_template_name:
            raise ValueError("Captured task execution snapshot template name does not match the task binding.")

        connection.executemany(
            "INSERT INTO task_snapshot_customers (task_id, ordinal, email, name, country) VALUES (?, ?, ?, ?, ?)",
            [
                (task.id, ordinal, customer.email, customer.name, customer.country)
                for ordinal, customer in enumerate(snapshot.customers)
            ],
        )
        template = snapshot.template
        connection.execute(
            """INSERT INTO task_snapshot_template (
                   task_id, template_id, name, currency, days_until_due, memo, footer, automatic_tax, reuse_customer,
                   invoice_title, invoice_subtitle, invoice_type, customer_note
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.id, template.id, template.name, template.currency, template.days_until_due, template.memo,
                template.footer, int(template.automatic_tax), int(template.reuse_customer), template.invoice_title,
                template.invoice_subtitle, template.invoice_type, template.customer_note,
            ),
        )
        connection.executemany(
            "INSERT INTO task_snapshot_template_items (task_id, ordinal, description, quantity, unit_amount, tax_rate) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (task.id, ordinal, item.description, str(item.quantity), str(item.unit_amount), str(item.tax_rate))
                for ordinal, item in enumerate(template.items)
            ],
        )
        connection.executemany(
            "INSERT INTO task_snapshot_template_terms (task_id, ordinal, term) VALUES (?, ?, ?)",
            [(task.id, ordinal, term) for ordinal, term in enumerate(template.terms)],
        )

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
            self._write_task_execution_snapshot(connection, task)
        self._transaction(write)

    def delete_task_and_release(self, task_id: str) -> None:
        def write(connection: sqlite3.Connection) -> None:
            connection.execute("DELETE FROM account_reservations WHERE task_id=?", (task_id,))
            connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self._transaction(write)

    def update_task(self, task: Task) -> None:
        def write(connection: sqlite3.Connection) -> None:
            snapshot = task.execution_snapshot
            if snapshot is not None and snapshot.state == TASK_SNAPSHOT_CAPTURED:
                snapshot_total = len(snapshot.customers)
                if task.total != snapshot_total:
                    raise ValueError("Task total no longer matches its immutable recipient snapshot.")
                if task.processed < 0 or task.processed > snapshot_total:
                    raise ValueError("Task processed count is outside its immutable recipient snapshot.")
                if task.success < 0 or task.failed < 0 or task.success + task.failed != task.processed:
                    raise ValueError("Task success/failed progress does not match its processed recipient count.")
            cursor = connection.execute(
                """UPDATE tasks SET status=?, success=?, failed=?, processed=?, last_message=? WHERE id=?""",
                (task.status, task.success, task.failed, task.processed, task.last_message, task.id),
            )
            if cursor.rowcount != 1:
                raise sqlite3.IntegrityError("Task row is missing.")
        self._transaction(write)
