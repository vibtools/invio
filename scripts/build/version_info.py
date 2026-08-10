from __future__ import annotations

import argparse
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?$")
ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ReleaseVersion:
    application: str
    pe_file_version: str
    msi_version: str
    tag: str


def parse_release_version(value: str) -> ReleaseVersion:
    match = VERSION_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError("Invio release version must contain five numeric components, with an optional sixth hotfix component.")
    major, minor, _patch, train, revision, hotfix = (
        int(part) if part is not None else None for part in match.groups()
    )
    assert hotfix is None or isinstance(hotfix, int)
    native_revision = revision
    if hotfix is not None:
        if revision > 655 or hotfix > 99:
            raise ValueError("Invio six-part hotfix mapping requires revision <= 655 and hotfix <= 99.")
        native_revision = revision * 100 + hotfix
    if major > 65535 or minor > 65535 or train > 65535 or native_revision > 65535:
        raise ValueError("Invio release version components exceed Windows executable version limits.")
    if major > 255 or train > 255:
        raise ValueError("Invio major/train components exceed MSI version limits (255).")

    application = value.strip()
    return ReleaseVersion(
        application=application,
        # PE file/product versions permit four numeric fields. Preserve the
        # public Invio identity externally and fold an optional two-digit
        # hotfix component into the native revision (40.1 -> 4001).
        pe_file_version=f"{major}.{minor}.{train}.{native_revision}",
        # Windows Installer ProductVersion is three fields and uses the same
        # folded native revision for six-part hotfix identities. Five-part
        # releases retain the historical mapping byte-for-byte.
        msi_version=f"{major}.{train}.{native_revision}",
        tag=f"v{application}",
    )


def current_release_version(root: Path = ROOT) -> ReleaseVersion:
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return parse_release_version(str(config["project"]["version"]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve Invio Windows/release version mappings.")
    parser.add_argument("--field", choices=("application", "pe", "msi", "tag"), default="application")
    parser.add_argument("--expect-tag", default="")
    args = parser.parse_args()

    release = current_release_version()
    if args.expect_tag and args.expect_tag != release.tag:
        raise SystemExit(
            f"Release tag mismatch: expected {release.tag} for application version {release.application}, "
            f"got {args.expect_tag}."
        )

    values = {
        "application": release.application,
        "pe": release.pe_file_version,
        "msi": release.msi_version,
        "tag": release.tag,
    }
    print(values[args.field])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
