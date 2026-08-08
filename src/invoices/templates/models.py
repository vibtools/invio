from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(slots=True)
class InvoiceItemTemplate:
    description: str
    quantity: Decimal
    unit_amount: Decimal
    tax_rate: Decimal = Decimal("0")


@dataclass(slots=True)
class InvoiceTemplate:
    id: str
    name: str
    currency: str
    days_until_due: int
    memo: str = ""
    footer: str = ""
    automatic_tax: bool = False
    reuse_customer: bool = True
    items: list[InvoiceItemTemplate] = field(default_factory=list)
    invoice_title: str = "Invoice"
    invoice_subtitle: str = ""
    invoice_type: str = "INVOICE"
    customer_note: str = ""
    terms: list[str] = field(default_factory=list)
