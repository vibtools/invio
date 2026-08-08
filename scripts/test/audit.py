from __future__ import annotations

import compileall
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

print("== Invio syntax audit ==")
if not compileall.compile_dir(ROOT / "src", quiet=1) or not compileall.compile_file(ROOT / "main.py", quiet=1):
    raise SystemExit("Syntax audit failed")
print("PASS")

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
