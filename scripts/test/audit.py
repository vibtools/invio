from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _purge_repository_bytecode() -> int:
    """Remove ignored Python bytecode that can shadow current source on timestamp collisions."""
    removed = 0
    roots = [ROOT / "src", ROOT / "tests", ROOT / "scripts", ROOT / "providers"]
    root_cache = ROOT / "__pycache__"
    if root_cache.is_dir():
        shutil.rmtree(root_cache)
        removed += 1
    for tree in roots:
        if not tree.exists():
            continue
        for cache_dir in sorted(tree.rglob("__pycache__"), reverse=True):
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir)
                removed += 1
    return removed


# Purge before importing any Invio/repository module. Workspace ZIPs can carry
# ignored timestamp-based .pyc files whose metadata still matches extracted
# source files on Windows, causing stale bytecode to override source truth.
_purged_bytecode_dirs = _purge_repository_bytecode()

from scripts.test.repository_hygiene import RepositoryHygieneError, assert_repository_source_hygiene
from scripts.test.repository_syntax import RepositorySyntaxError, assert_repository_python_syntax


print("== Invio bytecode hygiene ==")
print(f"PASS ({_purged_bytecode_dirs} generated __pycache__ directorie(s) purged)")

print("\n== Invio syntax audit ==")
try:
    checked = assert_repository_python_syntax(ROOT)
except RepositorySyntaxError as exc:
    raise SystemExit(str(exc)) from exc
print(f"PASS ({checked} repository Python files)")

print("\n== Repository source hygiene ==")
try:
    source_candidates = assert_repository_source_hygiene(ROOT)
except RepositoryHygieneError as exc:
    raise SystemExit(str(exc)) from exc
print(f"PASS ({source_candidates} public source candidate files)")

print("\n== Invio unit tests ==")
subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)

print("\n== Repository privacy contract ==")
gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
if "/project/" not in gitignore:
    raise SystemExit("project/ is not protected by .gitignore")
print("PASS")

print("\n== Provider visibility contract ==")
from src.core.provider_manager import ProviderManager, ProviderManifestError

manager = ProviderManager(ROOT)
try:
    manager.list_available()
    manager.list_installed()
except ProviderManifestError as exc:
    raise SystemExit(f"Provider manifest validation failed: {exc}") from exc
print("PASS")

print("\nAudit complete.")
