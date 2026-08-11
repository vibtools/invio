from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

REQUIRED_PORTABLE = {
    "Invio/Invio.exe",
    "Invio/assets/icons/checkmark.svg",
    "Invio/assets/icons/providers/stripe.png",
    "Invio/assets/icons/providers/refrens.png",
    "Invio/assets/icons/providers/agiled.png",
    "Invio/assets/icons/providers/odoo.png",
    "Invio/assets/icons/app.png",
    "Invio/assets/icons/app.ico",
    "Invio/providers/packages/stripe/provider.json",
    "Invio/providers/packages/refrens/provider.json",
    "Invio/providers/packages/agiled/provider.json",
}


def canonical_python_wheel_version(version: str) -> str:
    """Return the canonical numeric wheel version for Invio's dot-separated application identity."""
    parts = version.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        raise ValueError(f"Unsupported Invio application version for wheel canonicalization: {version}")
    return ".".join(str(int(part)) for part in parts)


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit generated Invio Windows portable/MSI/wheel release payloads.")
    parser.add_argument("--release-dir", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    root = args.release_dir.resolve()
    wheel_version = canonical_python_wheel_version(args.version)
    expected = {
        f"Invio_v{args.version}_windows_x64_portable.zip",
        f"Invio_v{args.version}_windows_x64_setup.msi",
        f"invio-{wheel_version}-py3-none-any.whl",
        "SHA256SUMS.txt",
    }
    missing = sorted(name for name in expected if not (root / name).is_file())
    if missing:
        raise SystemExit("Missing release payloads: " + ", ".join(missing))
    for name in expected - {"SHA256SUMS.txt"}:
        if (root / name).stat().st_size <= 0:
            raise SystemExit(f"Release payload is empty: {name}")

    portable = root / f"Invio_v{args.version}_windows_x64_portable.zip"
    with zipfile.ZipFile(portable) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"Portable ZIP integrity failed at {bad}")
        names = set(archive.namelist())
        missing_portable = sorted(REQUIRED_PORTABLE - names)
        if missing_portable:
            raise SystemExit("Portable ZIP missing runtime files: " + ", ".join(missing_portable))

    declared: dict[str, str] = {}
    for raw in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        checksum, name = raw.split(None, 1)
        declared[name.strip()] = checksum.strip().lower()
    payload_names = expected - {"SHA256SUMS.txt"}
    if set(declared) != payload_names:
        raise SystemExit(f"SHA256SUMS entries do not match payloads: {sorted(declared)}")
    for name in sorted(payload_names):
        if declared[name] != sha256(root / name):
            raise SystemExit(f"SHA256 mismatch for {name}")

    print("P14 Windows release payload audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
