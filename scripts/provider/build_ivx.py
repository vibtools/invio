from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.provider_manager import ProviderManager, ProviderManifestError, inspect_ivx  # noqa: E402
from src.core.provider_manager.ivx import (  # noqa: E402
    IVX_ADAPTER_FILENAME,
    IVX_CHECKSUM_FILENAME,
    IVX_MARKER_FILENAME,
)

_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
_EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}


def _safe_display_name(value: str) -> str:
    rendered = re.sub(r"[^A-Za-z0-9]+", "", value)
    return rendered or "Provider"


def _archive_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if any(part in _EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix.casefold() in {".pyc", ".pyo", ".ivx"}:
            continue
        if relative.as_posix() in {IVX_CHECKSUM_FILENAME, IVX_MARKER_FILENAME}:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(source).as_posix().casefold())


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=_FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_ivx(source_folder: Path, output_dir: Path) -> Path:
    source = source_folder.resolve()
    if not source.is_dir():
        raise ValueError(f"Provider source folder does not exist: {source}")
    manifest_path = source / "provider.json"
    if not manifest_path.is_file():
        raise ValueError("Provider source folder must contain root-level provider.json.")

    manager = ProviderManager(ROOT)
    try:
        manifest = manager.inspect_manifest(manifest_path)
    except ProviderManifestError as exc:
        raise ValueError(str(exc)) from exc
    if manifest.runtime_adapter is not None and not (source / IVX_ADAPTER_FILENAME).is_file():
        raise ValueError("Executable provider source is missing root-level adapter.py.")

    files = _archive_files(source)
    payloads: list[tuple[str, bytes]] = []
    for path in files:
        relative = path.relative_to(source).as_posix()
        payloads.append((relative, path.read_bytes()))

    checksum_text = "".join(f"{_sha256_bytes(data)}  {name}\n" for name, data in payloads)
    payloads.append((IVX_CHECKSUM_FILENAME, checksum_text.encode("utf-8")))
    payloads.sort(key=lambda item: item[0].casefold())

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"Invio_{_safe_display_name(manifest.name)}_Provider_v{manifest.version}.ivx"
    output = output_dir / filename
    temporary = output.with_name(output.stem + ".tmp.ivx")
    temporary.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for name, data in payloads:
                zf.writestr(_zip_info(name), data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        # Never publish a final .ivx until the exact temporary archive passes
        # the same host-side validation used for imported provider packages.
        inspect_ivx(temporary)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic Invio Provider Extension (.ivx) package.")
    parser.add_argument("source_folder", type=Path, help="Provider folder containing root-level provider.json")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (default: provider folder parent)")
    args = parser.parse_args()
    source = args.source_folder
    output_dir = args.output_dir or source.resolve().parent
    try:
        output = build_ivx(source, output_dir)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
