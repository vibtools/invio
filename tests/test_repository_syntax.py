from __future__ import annotations

import os
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.test.repository_syntax import (
    RepositorySyntaxError,
    assert_repository_python_syntax,
    repository_python_files,
)


ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class RepositorySyntaxAuditTests(unittest.TestCase):
    def _repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        _git(Path(temp.name), "init", "-q")
        return temp

    def test_accidental_ooudit_artifact_is_absent(self):
        self.assertFalse((ROOT / "ooudit.py").exists())
        audited = {path.relative_to(ROOT).as_posix() for path in repository_python_files(ROOT)}
        self.assertNotIn("ooudit.py", audited)

    def test_valid_tracked_root_and_nested_python_compile_without_execution(self):
        with self._repo() as temp:
            root = Path(temp)
            (root / "root_file.py").write_text("raise RuntimeError('must not execute')\n", encoding="utf-8")
            nested = root / "nested" / "module.py"
            nested.parent.mkdir()
            nested.write_text("VALUE = 1\n", encoding="utf-8")
            _git(root, "add", "root_file.py", "nested/module.py")

            checked = assert_repository_python_syntax(root)

            self.assertEqual(checked, 2)

    def test_malformed_tracked_python_fails_closed(self):
        with self._repo() as temp:
            root = Path(temp)
            bad = root / "bad.py"
            bad.write_text("def broken(:\n    pass\n", encoding="utf-8")
            _git(root, "add", "bad.py")

            with self.assertRaisesRegex(RepositorySyntaxError, r"bad\.py"):
                assert_repository_python_syntax(root)

    def test_malformed_untracked_unignored_python_fails_before_git_add(self):
        with self._repo() as temp:
            root = Path(temp)
            bad = root / "candidate_bad.py"
            bad.write_text("def broken(:\n", encoding="utf-8")

            with self.assertRaisesRegex(RepositorySyntaxError, r"candidate_bad\.py"):
                assert_repository_python_syntax(root)

    def test_malformed_ignored_python_is_outside_repository_source_gate(self):
        with self._repo() as temp:
            root = Path(temp)
            (root / ".gitignore").write_text("generated/\n", encoding="utf-8")
            good = root / "good.py"
            good.write_text("VALUE = 1\n", encoding="utf-8")
            ignored = root / "generated" / "generated_bad.py"
            ignored.parent.mkdir()
            ignored.write_text("def broken(:\n", encoding="utf-8")
            _git(root, "add", ".gitignore", "good.py")

            checked = assert_repository_python_syntax(root)

            self.assertEqual(checked, 1)

    def test_purging_timestamp_valid_stale_local_bytecode_restores_source_truth(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            module = root / "cache_probe.py"
            module.write_text("VALUE = 'old'\n", encoding="utf-8")
            fixed_time = 1_700_000_000
            os.utime(module, (fixed_time, fixed_time))
            py_compile.compile(str(module), doraise=True)

            # Same byte length + same timestamp keeps the local .pyc apparently valid.
            module.write_text("VALUE = 'new'\n", encoding="utf-8")
            os.utime(module, (fixed_time, fixed_time))

            command = [
                sys.executable,
                "-c",
                "import cache_probe; print(cache_probe.VALUE)",
            ]
            stale = subprocess.run(
                command,
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(stale.stdout.strip(), "old")

            cache_dir = root / "__pycache__"
            self.assertTrue(cache_dir.is_dir())
            import shutil
            shutil.rmtree(cache_dir)

            fresh = subprocess.run(
                command,
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(fresh.stdout.strip(), "new")

    def test_audit_entrypoint_purges_repo_bytecode_before_repository_import(self):
        source = (ROOT / "scripts" / "test" / "audit.py").read_text(encoding="utf-8")
        purge_index = source.index("_purged_bytecode_dirs = _purge_repository_bytecode()")
        import_index = source.index("from scripts.test.repository_syntax import")
        self.assertLess(purge_index, import_index)
        self.assertIn('rglob("__pycache__")', source)
