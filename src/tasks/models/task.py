from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from ...customers.models import CustomerRecord
from ...invoices.templates import InvoiceItemTemplate, InvoiceTemplate

TASK_SNAPSHOT_CAPTURED = "Captured"
TASK_SNAPSHOT_LEGACY_UNAVAILABLE = "LegacyUnavailable"
TASK_ASSIGNMENT_STRATEGY = "recipient_ordinal_round_robin_v1"
LEGACY_SNAPSHOT_MESSAGE = (
    "This task predates immutable execution snapshots. Close it and create a new Task before executing current data."
)


@dataclass(frozen=True, slots=True)
class TaskInvoiceItemSnapshot:
    description: str
    quantity: Decimal
    unit_amount: Decimal
    tax_rate: Decimal = Decimal("0")

    @classmethod
    def from_item(cls, item: InvoiceItemTemplate) -> "TaskInvoiceItemSnapshot":
        return cls(
            description=item.description,
            quantity=Decimal(item.quantity),
            unit_amount=Decimal(item.unit_amount),
            tax_rate=Decimal(item.tax_rate),
        )

    def to_item(self) -> InvoiceItemTemplate:
        return InvoiceItemTemplate(
            description=self.description,
            quantity=Decimal(self.quantity),
            unit_amount=Decimal(self.unit_amount),
            tax_rate=Decimal(self.tax_rate),
        )


@dataclass(frozen=True, slots=True)
class TaskInvoiceTemplateSnapshot:
    id: str
    name: str
    currency: str
    days_until_due: int
    memo: str = ""
    footer: str = ""
    automatic_tax: bool = False
    reuse_customer: bool = True
    items: tuple[TaskInvoiceItemSnapshot, ...] = ()
    invoice_title: str = "Invoice"
    invoice_subtitle: str = ""
    invoice_type: str = "INVOICE"
    customer_note: str = ""
    terms: tuple[str, ...] = ()

    @classmethod
    def from_template(cls, template: InvoiceTemplate) -> "TaskInvoiceTemplateSnapshot":
        return cls(
            id=template.id,
            name=template.name,
            currency=template.currency,
            days_until_due=template.days_until_due,
            memo=template.memo,
            footer=template.footer,
            automatic_tax=template.automatic_tax,
            reuse_customer=template.reuse_customer,
            items=tuple(TaskInvoiceItemSnapshot.from_item(item) for item in template.items),
            invoice_title=template.invoice_title,
            invoice_subtitle=template.invoice_subtitle,
            invoice_type=template.invoice_type,
            customer_note=template.customer_note,
            terms=tuple(template.terms),
        )

    def to_template(self) -> InvoiceTemplate:
        return InvoiceTemplate(
            id=self.id,
            name=self.name,
            currency=self.currency,
            days_until_due=self.days_until_due,
            memo=self.memo,
            footer=self.footer,
            automatic_tax=self.automatic_tax,
            reuse_customer=self.reuse_customer,
            items=[item.to_item() for item in self.items],
            invoice_title=self.invoice_title,
            invoice_subtitle=self.invoice_subtitle,
            invoice_type=self.invoice_type,
            customer_note=self.customer_note,
            terms=list(self.terms),
        )


@dataclass(frozen=True, slots=True)
class TaskExecutionSnapshot:
    state: str
    provider_id: str
    account_ids: tuple[str, ...]
    assignment_strategy: str
    customers: tuple[CustomerRecord, ...] = ()
    template: TaskInvoiceTemplateSnapshot | None = None

    @classmethod
    def capture(
        cls,
        *,
        provider_id: str,
        account_ids: list[str] | tuple[str, ...],
        customers: list[CustomerRecord] | tuple[CustomerRecord, ...],
        template: InvoiceTemplate,
    ) -> "TaskExecutionSnapshot":
        return cls(
            state=TASK_SNAPSHOT_CAPTURED,
            provider_id=provider_id,
            account_ids=tuple(account_ids),
            assignment_strategy=TASK_ASSIGNMENT_STRATEGY,
            customers=tuple(customers),
            template=TaskInvoiceTemplateSnapshot.from_template(template),
        )

    @classmethod
    def legacy_unavailable(
        cls,
        *,
        provider_id: str,
        account_ids: list[str] | tuple[str, ...],
    ) -> "TaskExecutionSnapshot":
        return cls(
            state=TASK_SNAPSHOT_LEGACY_UNAVAILABLE,
            provider_id=provider_id,
            account_ids=tuple(account_ids),
            assignment_strategy=TASK_ASSIGNMENT_STRATEGY,
            customers=(),
            template=None,
        )

    @property
    def is_captured(self) -> bool:
        return self.state == TASK_SNAPSHOT_CAPTURED


@dataclass(slots=True)
class Task:
    id: str
    name: str
    provider_id: str
    provider_name: str
    account_ids: list[str]
    customer_list_id: str
    customer_list_name: str
    status: str = "Ready"
    total: int = 0
    success: int = 0
    failed: int = 0
    processed: int = 0
    last_message: str = "Ready"
    account_names: list[str] = field(default_factory=list)
    invoice_template_id: str = ""
    invoice_template_name: str = ""
    execution_snapshot: TaskExecutionSnapshot | None = None

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.processed)

    @property
    def has_immutable_execution_snapshot(self) -> bool:
        return self.execution_snapshot is not None and self.execution_snapshot.is_captured
