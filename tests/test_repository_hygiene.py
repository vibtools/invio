from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.test.repository_hygiene import (
    RepositoryHygieneError,
    assert_repository_source_hygiene,
    committed_source_files,
    create_source_archive,
    repository_candidate_files,
)


ROOT = Path(__file__).resolve().parents[1]


class RepositoryHygieneTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return completed.stdout.strip()

    def _repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        holder = tempfile.TemporaryDirectory()
        root = Path(holder.name)
        self._git(root, "init")
        self._git(root, "config", "user.name", "Invio Hygiene Test")
        self._git(root, "config", "user.email", "hygiene@example.invalid")
        (root / ".gitignore").write_text(
            "__pycache__/\n*.py[cod]\nbuild/\ndist/\ndata/runtime/\ndata/exports/\n"
            "providers/registry/*\n!providers/registry/.gitkeep\n/project/\n",
            encoding="utf-8",
        )
        (root / "tracked.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "providers" / "registry").mkdir(parents=True)
        (root / "providers" / "registry" / ".gitkeep").write_text("", encoding="utf-8")
        self._git(root, "add", ".")
        self._git(root, "commit", "-m", "baseline")
        return holder, root

    def test_root_transient_sha256sums_is_absent_from_public_source(self):
        self.assertFalse((ROOT / "SHA256SUMS.txt").exists())
        self.assertNotIn("SHA256SUMS.txt", repository_candidate_files(ROOT))

    def test_private_project_boundary_remains_ignored_and_fails_if_force_tracked(self):
        holder, root = self._repo()
        try:
            private = root / "project" / "research" / "secret.md"
            private.parent.mkdir(parents=True)
            private.write_text("private\n", encoding="utf-8")
            self.assertNotIn("project/research/secret.md", repository_candidate_files(root))
            self._git(root, "add", "-f", "project/research/secret.md")
            with self.assertRaisesRegex(RepositoryHygieneError, "project/research/secret.md"):
                assert_repository_source_hygiene(root)
        finally:
            holder.cleanup()

    def test_cache_build_and_runtime_boundaries_fail_if_force_tracked(self):
        holder, root = self._repo()
        try:
            forbidden = (
                "__pycache__/tracked.cpython-312.pyc",
                "build/output.bin",
                "data/runtime/state.json",
                "providers/registry/runtime.json",
            )
            for relative in forbidden:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"generated")
                self._git(root, "add", "-f", relative)
            with self.assertRaises(RepositoryHygieneError) as caught:
                assert_repository_source_hygiene(root)
            message = str(caught.exception)
            for relative in forbidden:
                self.assertIn(relative, message)
        finally:
            holder.cleanup()

    def test_canonical_source_inventory_comes_from_exact_git_commit_tree(self):
        holder, root = self._repo()
        try:
            first = self._git(root, "rev-parse", "HEAD")
            (root / "tracked.py").write_text("VALUE = 2\n", encoding="utf-8")
            (root / "new.py").write_text("NEW = True\n", encoding="utf-8")
            self.assertIn("new.py", repository_candidate_files(root))
            committed = committed_source_files(root, first)
            self.assertIn("tracked.py", committed)
            self.assertNotIn("new.py", committed)
        finally:
            holder.cleanup()

    def test_source_archive_excludes_ignored_private_cache_and_runtime_files(self):
        holder, root = self._repo()
        try:
            ignored = (
                "project/research/private.md",
                "__pycache__/tracked.cpython-312.pyc",
                "build/output.bin",
                "data/runtime/state.json",
                "providers/registry/runtime.json",
            )
            for relative in ignored:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"workspace-only")
            archive = Path(holder.name) / "source.zip"
            create_source_archive(root, archive, "HEAD")
            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())
            self.assertIn("tracked.py", names)
            for relative in ignored:
                self.assertNotIn(relative, names)
        finally:
            holder.cleanup()

    def test_source_archive_is_immutable_against_untracked_workspace_files(self):
        holder, root = self._repo()
        try:
            first = Path(holder.name) / "first.zip"
            second = Path(holder.name) / "second.zip"
            create_source_archive(root, first, "HEAD")
            (root / "untracked.txt").write_text("not committed\n", encoding="utf-8")
            create_source_archive(root, second, "HEAD")
            first_digest = hashlib.sha256(first.read_bytes()).hexdigest()
            second_digest = hashlib.sha256(second.read_bytes()).hexdigest()
            self.assertEqual(first_digest, second_digest)
            with zipfile.ZipFile(second) as bundle:
                self.assertNotIn("untracked.txt", bundle.namelist())
        finally:
            holder.cleanup()

    def test_release_checksum_pipeline_is_separate_from_repository_root_hygiene(self):
        helper = (ROOT / "scripts" / "build" / "finalize_release_checksums.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn('root / "SHA256SUMS.txt"', helper)
        self.assertIn("python scripts/build/finalize_release_checksums.py dist\\release", workflow)
        self.assertIn("windows-build:\n    if: startsWith(github.ref, 'refs/tags/v')", workflow)
        self.assertNotIn("SHA256SUMS.txt", repository_candidate_files(ROOT))


if __name__ == "__main__":
    unittest.main()
