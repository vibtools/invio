from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT_DOCS = (
    ROOT / "README.md",
    ROOT / "ROADMAP.md",
    ROOT / "docs" / "index.md",
    ROOT / "docs" / "developer" / "ACTUAL_IMPLEMENTATION_STATUS.md",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def _schema_version() -> int:
    match = re.search(
        r"^DOMAIN_SCHEMA_VERSION\s*=\s*(\d+)\s*$",
        _text(ROOT / "src" / "core" / "storage" / "schema.py"),
        re.MULTILINE,
    )
    if match is None:
        raise AssertionError("DOMAIN_SCHEMA_VERSION source-of-truth is missing")
    return int(match.group(1))


class DocumentationTruthTests(unittest.TestCase):
    def test_current_release_lifecycle_is_truthful(self) -> None:
        version = _version()
        note = _text(ROOT / "docs" / "release-notes" / f"{version}.md")
        self.assertIn(f"Tag `v{version}`", note)
        self.assertIn("published on 2026-09-08", note)
        self.assertIn("Windows x64 MSI", note)
        lowered = note.lower()
        self.assertNotIn("tag is not created", lowered)
        self.assertNotIn("before owner tag/release publication", lowered)

    def test_current_release_changelog_has_no_future_tag_claim(self) -> None:
        version = _version()
        changelog = _text(ROOT / "CHANGELOG.md")
        marker = f"## v{version}"
        start = changelog.index(marker)
        next_heading = changelog.find("\n## ", start + len(marker))
        section = changelog[start:] if next_heading < 0 else changelog[start:next_heading]
        self.assertIn(f"tag `v{version}`", section)
        self.assertIn("published on 2026-09-08", section)
        self.assertNotIn("future tag", section.lower())

    def test_current_facing_docs_have_one_authoritative_current_state(self) -> None:
        version = _version()
        banned_heading = re.compile(
            r"^#{1,4}\s+Current\s+.*v1\.0\.0\.1\.(?!52(?:\s|$))",
            re.MULTILINE | re.IGNORECASE,
        )
        for path in CURRENT_DOCS:
            content = _text(path)
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual(content.lower().count("current authoritative"), 1)
                self.assertIn(version, content.splitlines()[0:20].__str__())
                self.assertIsNone(banned_heading.search(content))

    def test_current_docs_match_version_and_schema_source_of_truth(self) -> None:
        version = _version()
        schema = _schema_version()
        status = _text(ROOT / "docs" / "developer" / "ACTUAL_IMPLEMENTATION_STATUS.md")
        readme = _text(ROOT / "README.md")
        self.assertIn(f"Application/wheel version: `{version}`", status)
        self.assertIn(f"Operational SQLite schema: **v{schema}**", status)
        self.assertIn(f"schema **v{schema}**", readme)
        summary_start = status.index("## Current Summary")
        next_section = status.index("\n## ", summary_start + len("## Current Summary"))
        current_summary = status[summary_start:next_section]
        self.assertNotIn("Current SQLite schema v5", current_summary)
        self.assertIn(f"Current SQLite schema v{schema}", current_summary)

    def test_security_policy_matches_current_implemented_boundaries(self) -> None:
        security = _text(ROOT / ".github" / "SECURITY.md")
        for required in (
            "There is no plaintext-file fallback",
            "native Windows trust store",
            "structured privacy redaction",
            "explicit trust boundary",
            "Signing Option C",
            "Unknown Publisher",
        ):
            with self.subTest(required=required):
                self.assertIn(required, security)
        self.assertNotIn("later production roadmap phases and are not claimed", security)


if __name__ == "__main__":
    unittest.main()
