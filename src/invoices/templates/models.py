from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(slots=True)
class InvoiceItemTemplate:
    description: str
    quantity: Decimal
    unit_amount: Decimal


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
