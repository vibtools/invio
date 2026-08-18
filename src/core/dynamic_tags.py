from __future__ import annotations

import copy
import hashlib
from calendar import month_name
from dataclasses import dataclass
from datetime import datetime, timezone

SUPPORTED_DYNAMIC_TAGS: tuple[str, ...] = (
    "#NAME#",
    "#EMAIL#",
    "#R5#",
    "#R11#",
    "#DATE#",
    "#DATE-NAME#",
    "#YAAR#",
)

DYNAMIC_TAGS_VERSION = 1


class DynamicTagError(ValueError):
    """Raised when a captured Dynamic Tags V1 execution context is invalid."""


@dataclass(frozen=True, slots=True)
class DynamicTagContext:
    task_id: str
    recipient_email: str
    reference_utc: str

    def __post_init__(self) -> None:
        task_id = str(self.task_id).strip()
        email = str(self.recipient_email).strip().lower()
        reference = str(self.reference_utc).strip()
        if not task_id:
            raise DynamicTagError("Dynamic tag context requires a Task id.")
        if not email or "@" not in email:
            raise DynamicTagError("Dynamic tag context requires a recipient email.")
        _parse_utc_reference(reference)
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "recipient_email", email)
        object.__setattr__(self, "reference_utc", reference)


def utc_reference_now() -> str:
    """Return the Task-creation UTC reference in a durable ISO-8601 form."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def contains_supported_dynamic_tag(value: str) -> bool:
    text = str(value)
    return any(tag in text for tag in SUPPORTED_DYNAMIC_TAGS)


def _parse_utc_reference(value: str) -> datetime:
    text = str(value).strip()
    if not text:
        raise DynamicTagError("Dynamic tag Task-creation UTC reference is missing.")
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise DynamicTagError("Dynamic tag Task-creation UTC reference is invalid.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise DynamicTagError("Dynamic tag Task-creation reference must be UTC.")
    return parsed.astimezone(timezone.utc)


def _deterministic_numeric_value(context: DynamicTagContext, tag: str, *, digits: int) -> str:
    if digits not in {5, 11}:
        raise DynamicTagError("Unsupported deterministic numeric tag width.")
    namespace = "\x00".join(
        ("invio-dynamic-tags-v1", context.task_id, context.recipient_email, tag)
    ).encode("utf-8")
    number = int.from_bytes(hashlib.sha256(namespace).digest(), "big")
    minimum = 10 ** (digits - 1)
    span = 9 * minimum
    return str(minimum + (number % span))


def resolved_values(context: DynamicTagContext) -> dict[str, str]:
    reference = _parse_utc_reference(context.reference_utc)
    local_part = context.recipient_email.split("@", 1)[0]
    return {
        "#NAME#": local_part,
        "#EMAIL#": context.recipient_email,
        "#R5#": _deterministic_numeric_value(context, "#R5#", digits=5),
        "#R11#": _deterministic_numeric_value(context, "#R11#", digits=11),
        "#DATE#": f"{month_name[reference.month]} {reference.day}, {reference.year}",
        "#DATE-NAME#": reference.strftime("%A"),
        "#YAAR#": f"{reference.year:04d}",
    }


def render_dynamic_text(value: str, context: DynamicTagContext) -> str:
    """Resolve only supported exact tags; unknown tag-like text remains literal."""

    rendered = str(value)
    for tag, replacement in resolved_values(context).items():
        rendered = rendered.replace(tag, replacement)
    return rendered


def render_invoice_template(template, context: DynamicTagContext):
    """Return a recipient-specific copy with only approved Phase-4 fields rendered."""

    rendered = copy.deepcopy(template)
    rendered.memo = render_dynamic_text(rendered.memo, context)
    rendered.footer = render_dynamic_text(rendered.footer, context)
    rendered.customer_note = render_dynamic_text(rendered.customer_note, context)
    rendered.terms = [render_dynamic_text(term, context) for term in rendered.terms]
    for item in rendered.items:
        item.description = render_dynamic_text(item.description, context)
    return rendered
