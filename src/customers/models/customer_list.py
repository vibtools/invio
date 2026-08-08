from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CustomerList:
    id: str
    name: str
    emails: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.emails)
