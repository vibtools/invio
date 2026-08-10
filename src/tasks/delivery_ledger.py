from __future__ import annotations

from dataclasses import dataclass

DELIVERY_RESULT_PENDING = "Pending"
DELIVERY_RESULT_SUCCEEDED = "Succeeded"
DELIVERY_RESULT_FAILED = "Failed"
DELIVERY_RESULT_UNCERTAIN = "Uncertain"

DELIVERY_OPERATION_STARTED = "Started"
DELIVERY_OPERATION_SUCCEEDED = "Succeeded"
DELIVERY_OPERATION_FAILED = "Failed"
DELIVERY_OPERATION_UNCERTAIN = "Uncertain"

DELIVERY_RUN_RUNNING = "Running"
DELIVERY_RUN_COMPLETED = "Completed"
DELIVERY_RUN_STOPPED = "Stopped"
DELIVERY_RUN_FAILED = "Failed"
DELIVERY_RUN_INTERRUPTED = "Interrupted"

MUTATING_DELIVERY_STAGES = frozenset(
    {
        "customer_create",
        "invoice_create",
        "invoice_finalize",
        "invoice_send",
        "refrens_invoice_create_email",
    }
)


def is_mutating_delivery_stage(stage: str) -> bool:
    clean = str(stage).strip()
    return clean in MUTATING_DELIVERY_STAGES or clean.startswith("invoice_item:")


@dataclass(frozen=True, slots=True)
class DeliveryRunRecord:
    run_id: str
    task_id: str
    task_name: str
    run_number: int
    provider_id: str
    execution_mode: str
    status: str
    started_at: str
    finished_at: str = ""




@dataclass(frozen=True, slots=True)
class RecipientDeliveryReportRecord:
    task_id: str
    task_name: str
    recipient_email: str
    provider_id: str
    safe_status: str
    attempts: int
    account_reference: str
    provider_invoice_reference: str
    last_stage: str
    error_code: str
    provider_send_acceptance: str
    email_delivery: str

@dataclass(frozen=True, slots=True)
class DeliveryLedgerSummary:
    task_id: str
    has_history: bool
    continuation_safe: bool
    succeeded_recipients: tuple[str, ...]
    failed_recipients: tuple[str, ...]
    pending_recipients: tuple[str, ...]
    uncertain_recipients: tuple[str, ...]
    assigned_account_ids: tuple[tuple[str, str], ...]
    processed: int
    success: int
    failed: int
    remaining: int

    @property
    def retry_failed_available(self) -> bool:
        return (
            self.continuation_safe
            and bool(self.failed_recipients)
            and not self.pending_recipients
            and not self.uncertain_recipients
        )

    @property
    def resume_remaining_available(self) -> bool:
        return self.continuation_safe and bool(
            self.failed_recipients or self.pending_recipients or self.uncertain_recipients
        )
