from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Write SHA256SUMS for Invio release payloads.")
    parser.add_argument("release_dir", type=Path)
    args = parser.parse_args()
    root = args.release_dir.resolve()
    payloads = sorted(
        (path for path in root.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt"),
        key=lambda path: path.name.casefold(),
    )
    if not payloads:
        raise SystemExit("No release payloads were found.")
    lines = [f"{digest(path)}  {path.name}" for path in payloads]
    (root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Release checksums written for {len(payloads)} payload(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
