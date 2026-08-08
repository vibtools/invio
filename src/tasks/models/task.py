from __future__ import annotations

from dataclasses import dataclass, field


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

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.processed)
