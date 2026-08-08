from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Account:
    """Provider account held in memory for the current application session.

    Credentials deliberately remain runtime-only under the current storage
    contract.
    """

    id: str
    provider_id: str
    provider_name: str
    name: str
    mode: str
    status: str = "Ready"
    credentials: dict[str, str] = field(default_factory=dict, repr=False)
