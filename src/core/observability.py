from __future__ import annotations

import csv
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

LOG_SEVERITIES = frozenset({"INFO", "WARNING", "ERROR"})
LOG_CATEGORIES = frozenset({"APPLICATION", "TASK", "PROVIDER", "STORAGE", "EXPORT", "RECOVERY", "PRIVACY"})

_EMAIL_RE = re.compile(r"(?<![A-Za-z0-9._%+\-])([A-Za-z0-9._%+\-]+)@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})(?![A-Za-z0-9._%+\-])")
_STRIPE_KEY_RE = re.compile(r"\b(?:sk|rk)_(?:test|live)_[A-Za-z0-9_\-]+\b", re.I)
_AUTH_HEADER_RE = re.compile(r"(?i)(\bauthorization\s*[:=]\s*)(?:bearer|basic)\s+[^\s,;]+")
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=\-]+")
_BASIC_RE = re.compile(r"(?i)\bbasic\s+[A-Za-z0-9+/=]+")
_NAMED_SECRET_RE = re.compile(
    r"(?i)((?:[\"']?)(?:app[_ -]?secret|api[_ -]?key|secret[_ -]?key|access[_ -]?token|accessToken|authorization|token)(?:[\"']?)\s*[:=]\s*)"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s,;}\]]+)"
)


@dataclass(frozen=True, slots=True)
class StructuredLogEvent:
    severity: str
    category: str
    message: str
    task_id: str = ""

    def __post_init__(self) -> None:
        severity = str(self.severity).strip().upper() or "INFO"
        category = str(self.category).strip().upper() or "APPLICATION"
        if severity not in LOG_SEVERITIES:
            raise ValueError(f"Unsupported log severity '{severity}'.")
        if category not in LOG_CATEGORIES:
            raise ValueError(f"Unsupported log category '{category}'.")
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "message", str(self.message))
        object.__setattr__(self, "task_id", str(self.task_id).strip())


def mask_email(value: str) -> str:
    text = str(value)

    def replace(match: re.Match[str]) -> str:
        local = match.group(1)
        domain = match.group(2)
        visible = local[:1] if local else "*"
        return f"{visible}***@{domain}"

    return _EMAIL_RE.sub(replace, text)


def redact_sensitive_text(
    value: object,
    *,
    secret_values: Iterable[object] = (),
    mask_emails: bool = False,
) -> str:
    """Return diagnostic text with provider secrets removed.

    Explicit runtime/account secrets are replaced first, followed by provider-
    neutral token/auth patterns. Historical durable rows are never rewritten;
    callers use this before displaying or persisting new diagnostic text.
    """

    text = str(value)
    secrets = sorted(
        {str(item) for item in secret_values if str(item)},
        key=len,
        reverse=True,
    )
    for secret in secrets:
        text = text.replace(secret, "***REDACTED***")
    text = _STRIPE_KEY_RE.sub("***REDACTED***", text)
    text = _AUTH_HEADER_RE.sub(lambda match: f"{match.group(1)}***REDACTED***", text)
    text = _BEARER_RE.sub("Bearer ***REDACTED***", text)
    text = _BASIC_RE.sub("Basic ***REDACTED***", text)
    text = _NAMED_SECRET_RE.sub(lambda match: f"{match.group(1)}***REDACTED***", text)
    if mask_emails:
        text = mask_email(text)
    return text


def spreadsheet_safe_text(value: object) -> str:
    """Neutralize spreadsheet formula interpretation while preserving text."""

    text = str(value)
    if not text:
        return text
    probe = text.lstrip(" ")
    if probe[:1] in {"=", "+", "-", "@", "\t", "\r", "\n"}:
        return "'" + text
    return text


def _temporary_sibling(path: Path) -> Path:
    return path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")


def atomic_write_text(path: str | Path, text: str, *, encoding: str = "utf-8") -> None:
    target = Path(path)
    temporary = _temporary_sibling(target)
    try:
        with temporary.open("w", encoding=encoding, newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def atomic_write_csv(
    path: str | Path,
    rows: Iterable[Sequence[object]],
    *,
    text_columns: set[int] | None = None,
    encoding: str = "utf-8-sig",
) -> None:
    """Write CSV atomically and neutralize formula-capable text columns."""

    target = Path(path)
    temporary = _temporary_sibling(target)
    try:
        with temporary.open("w", encoding=encoding, newline="") as handle:
            writer = csv.writer(handle)
            for row in rows:
                values = list(row)
                if text_columns is None:
                    safe = [spreadsheet_safe_text(value) if isinstance(value, str) else value for value in values]
                else:
                    safe = [
                        spreadsheet_safe_text(value) if index in text_columns else value
                        for index, value in enumerate(values)
                    ]
                writer.writerow(safe)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise
