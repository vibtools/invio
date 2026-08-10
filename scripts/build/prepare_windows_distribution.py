from __future__ import annotations

import argparse
import hashlib
import shutil
import zipfile
from pathlib import Path

from version_info import current_release_version

REQUIRED_RELATIVE_RESOURCES = (
    Path("assets/icons/checkmark.svg"),
    Path("providers/packages/stripe/provider.json"),
    Path("providers/packages/refrens/provider.json"),
    Path("providers/packages/agiled/provider.json"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_distribution(nuitka_dist: Path, output_root: Path, release_root: Path) -> tuple[Path, Path]:
    nuitka_dist = nuitka_dist.resolve()
    output_root = output_root.resolve()
    release_root = release_root.resolve()
    if not nuitka_dist.is_dir():
        raise FileNotFoundError(f"Nuitka OneDir output does not exist: {nuitka_dist}")

    source_exe = nuitka_dist / "main.exe"
    if not source_exe.is_file():
        raise FileNotFoundError(f"Nuitka OneDir output is missing main.exe: {source_exe}")

    app_dir = output_root / "Invio"
    if app_dir.exists():
        shutil.rmtree(app_dir)
    app_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(nuitka_dist, app_dir)

    built_exe = app_dir / "main.exe"
    final_exe = app_dir / "Invio.exe"
    built_exe.replace(final_exe)

    for relative in REQUIRED_RELATIVE_RESOURCES:
        path = app_dir / relative
        if not path.is_file():
            raise FileNotFoundError(f"Nuitka OneDir output is missing required runtime resource: {relative.as_posix()}")

    release = current_release_version()
    release_root.mkdir(parents=True, exist_ok=True)
    portable = release_root / f"Invio_v{release.application}_windows_x64_portable.zip"
    if portable.exists():
        portable.unlink()
    with zipfile.ZipFile(portable, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(app_dir.rglob("*")):
            if path.is_file():
                archive.write(path, (Path("Invio") / path.relative_to(app_dir)).as_posix())
    with zipfile.ZipFile(portable) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"Portable ZIP integrity failed at {bad}")
        names = set(archive.namelist())
        if "Invio/Invio.exe" not in names:
            raise RuntimeError("Portable ZIP is missing Invio/Invio.exe")

    checksum_path = release_root / "SHA256SUMS.txt"
    # MSI and wheel are appended later by the workflow. Start with the portable
    # checksum so every generated end-user payload has a common checksum file.
    checksum_path.write_text(f"{_sha256(portable)}  {portable.name}\n", encoding="utf-8")
    return app_dir, portable


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare the versioned Invio Windows OneDir portable payload.")
    parser.add_argument("--nuitka-dist", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--release-root", type=Path, required=True)
    args = parser.parse_args()
    app_dir, portable = prepare_distribution(args.nuitka_dist, args.output_root, args.release_root)
    print(f"Prepared OneDir: {app_dir}")
    print(f"Prepared portable ZIP: {portable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
