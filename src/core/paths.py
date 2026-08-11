from __future__ import annotations

import sys
from pathlib import Path


class RuntimeResourceError(RuntimeError):
    """Raised when required packaged Invio runtime resources are unavailable."""


def _looks_like_application_root(root: Path) -> bool:
    return (
        (root / "providers" / "packages" / "stripe" / "provider.json").is_file()
        and (root / "providers" / "packages" / "refrens" / "provider.json").is_file()
        and (root / "providers" / "packages" / "agiled" / "provider.json").is_file()
        and (root / "assets" / "icons" / "checkmark.svg").is_file()
    )


def application_root() -> Path:
    """Return the source, wheel, or Nuitka-OneDir application resource root.

    Source checkouts and wheels keep ``src`` beside the packaged ``providers``
    and ``assets`` trees, so the historic module-relative root remains first.
    Nuitka may report compiled module locations differently; in that case the
    executable directory is the only approved fallback and is accepted only
    when the exact frozen runtime-resource contract is present there.
    """

    module_root = Path(__file__).resolve().parents[2]
    if _looks_like_application_root(module_root):
        return module_root

    executable_root = Path(sys.executable).resolve().parent
    if _looks_like_application_root(executable_root):
        return executable_root

    # Preserve the historical diagnostic root so validate_runtime_resources()
    # reports concrete missing paths instead of silently guessing elsewhere.
    return module_root


def packaged_providers_root() -> Path:
    return application_root() / "providers" / "packages"


def asset_path(*parts: str) -> Path:
    return application_root() / "assets" / Path(*parts)


def required_runtime_resources() -> tuple[Path, ...]:
    root = application_root()
    return (
        root / 'assets' / 'icons' / 'checkmark.svg',
        root / 'assets' / 'icons' / 'search.svg',
        root / 'assets' / 'icons' / 'chevron-down.svg',
        root / 'assets' / 'icons' / 'chevron-up.svg',
        root / 'assets' / 'icons' / 'nav' / 'dashboard.svg',
        root / 'assets' / 'icons' / 'nav' / 'accounts.svg',
        root / 'assets' / 'icons' / 'nav' / 'invoice.svg',
        root / 'assets' / 'icons' / 'nav' / 'customers.svg',
        root / 'assets' / 'icons' / 'nav' / 'tasks.svg',
        root / 'assets' / 'icons' / 'nav' / 'providers.svg',
        root / 'assets' / 'icons' / 'nav' / 'reports.svg',
        root / 'assets' / 'icons' / 'nav' / 'logs.svg',
        root / 'assets' / 'icons' / 'nav' / 'settings.svg',
        root / 'assets' / 'icons' / 'window' / 'minimize.svg',
        root / 'assets' / 'icons' / 'window' / 'maximize.svg',
        root / 'assets' / 'icons' / 'window' / 'restore.svg',
        root / 'assets' / 'icons' / 'window' / 'close.svg',
        root / 'providers' / 'packages' / 'stripe' / 'provider.json',
        root / 'providers' / 'packages' / 'refrens' / 'provider.json',
        root / 'providers' / 'packages' / 'agiled' / 'provider.json',
    )

def validate_runtime_resources() -> None:
    missing = [path for path in required_runtime_resources() if not path.is_file()]
    if missing:
        rendered = ", ".join(path.as_posix() for path in missing)
        raise RuntimeResourceError(f"Invio runtime resources are missing: {rendered}")
