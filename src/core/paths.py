from __future__ import annotations

from pathlib import Path


class RuntimeResourceError(RuntimeError):
    """Raised when required packaged Invio runtime resources are unavailable."""


def application_root() -> Path:
    """Return the source-checkout or installed-wheel application resource root.

    P14 packages the existing top-level ``providers`` and ``assets`` trees next
    to the installed ``src`` package. The same relative layout already exists
    in a source checkout, so one deterministic root preserves both workflows.
    """

    return Path(__file__).resolve().parents[2]


def packaged_providers_root() -> Path:
    return application_root() / "providers" / "packages"


def asset_path(*parts: str) -> Path:
    return application_root() / "assets" / Path(*parts)


def required_runtime_resources() -> tuple[Path, ...]:
    root = application_root()
    return (
        root / "assets" / "icons" / "checkmark.svg",
        root / "providers" / "packages" / "stripe" / "provider.json",
        root / "providers" / "packages" / "refrens" / "provider.json",
        root / "providers" / "packages" / "agiled" / "provider.json",
    )


def validate_runtime_resources() -> None:
    missing = [path for path in required_runtime_resources() if not path.is_file()]
    if missing:
        rendered = ", ".join(path.as_posix() for path in missing)
        raise RuntimeResourceError(f"Invio runtime resources are missing: {rendered}")
