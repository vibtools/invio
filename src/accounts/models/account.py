from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Account:
    """Provider account used by the current application session.

    P02 persists non-sensitive account metadata in SQLite while credentials
    are restored from the approved protected credential store into memory.
    """

    id: str
    provider_id: str
    provider_name: str
    name: str
    mode: str
    status: str = "Ready"
    credentials: dict[str, str] = field(default_factory=dict, repr=False)
    last_verification_at: str = ""
    verification_error_summary: str = ""
