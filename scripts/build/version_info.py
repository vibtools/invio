from __future__ import annotations

import argparse
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)$")
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
        raise ValueError("Invio release version must contain exactly five numeric components.")
    major, minor, _patch, train, revision = (int(part) for part in match.groups())
    if major > 65535 or minor > 65535 or train > 65535 or revision > 65535:
        raise ValueError("Invio release version components exceed Windows executable version limits.")
    if major > 255 or train > 255:
        raise ValueError("Invio major/train components exceed MSI version limits (255).")

    application = value.strip()
    return ReleaseVersion(
        application=application,
        # PE file/product versions permit four numeric fields. Preserve the
        # long Invio release identity externally while mapping its active
        # train/revision into the last two PE fields.
        pe_file_version=f"{major}.{minor}.{train}.{revision}",
        # Windows Installer ProductVersion is three fields. Invio's current
        # release train is ordered by (major, train, revision), which keeps
        # MSI MajorUpgrade ordering deterministic for this frozen versioning
        # family without changing the public five-part application version.
        msi_version=f"{major}.{train}.{revision}",
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
