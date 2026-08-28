from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

EXPECTED_ACTION_PINS = {
    "actions/checkout": "fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
    "actions/setup-python": "ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/setup-dotnet": "26b0ec14cb23fa6904739307f278c14f94c95bf1",
    "actions/upload-artifact": "b7c566a772e6b6bfb58ed0dc250532a479d7789f",
    "actions/download-artifact": "37930b1c2abaa49bbe596cd826c3c89aef350131",
    "Nuitka/Nuitka-Action": "99c9d3ab258c7008c0604617d925574101327e5d",
}

EXPECTED_LINUX_CONSTRAINTS = {
    "PySide6==6.11.2",
    "PySide6_Addons==6.11.2",
    "PySide6_Essentials==6.11.2",
    "shiboken6==6.11.2",
    "openpyxl==3.1.5",
    "keyring==25.7.0",
    "truststore==0.10.4",
    "et-xmlfile==2.0.0",
    "SecretStorage==3.5.0",
    "jeepney==0.9.0",
    "cryptography==50.0.1",
    "cffi==2.1.1",
    "pycparser==3.0",
    "jaraco.classes==3.4.0",
    "jaraco.context==6.1.2",
    "jaraco.functools==4.6.0",
    "more-itertools==11.1.0",
}

EXPECTED_WINDOWS_CONSTRAINTS = {
    "PySide6==6.11.2",
    "PySide6_Addons==6.11.2",
    "PySide6_Essentials==6.11.2",
    "shiboken6==6.11.2",
    "openpyxl==3.1.5",
    "keyring==25.7.0",
    "truststore==0.10.4",
    "pywin32-ctypes==0.2.3",
    "et-xmlfile==2.0.0",
    "jaraco.classes==3.4.0",
    "jaraco.context==6.1.2",
    "jaraco.functools==4.6.0",
    "more-itertools==11.1.0",
}

EXPECTED_TOOL_LOCK = {
    "pip==26.2.1",
    "setuptools==84.0.0",
    "wheel==0.48.0",
    "packaging==26.3",
}


def _requirements(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


class CiReproducibilityTests(unittest.TestCase):
    def test_all_external_actions_are_immutable_sha_pinned(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        uses_lines = [line.strip() for line in workflow.splitlines() if line.strip().startswith("- uses:")]
        self.assertTrue(uses_lines)
        pattern = re.compile(r"^- uses: ([^@\s]+)@([0-9a-f]{40})(?:\s+#\s+\S+)?$")
        for line in uses_lines:
            with self.subTest(line=line):
                self.assertIsNotNone(pattern.fullmatch(line))
        self.assertNotRegex(workflow, r"uses:\s+[^\s]+@(v\d+|main|master|latest)(?:\s|$)")

    def test_expected_node24_action_revisions_are_pinned(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        seen: dict[str, set[str]] = {}
        for owner_repo, sha in re.findall(r"uses:\s+([^@\s]+)@([0-9a-f]{40})", workflow):
            seen.setdefault(owner_repo, set()).add(sha)
        self.assertEqual(set(seen), set(EXPECTED_ACTION_PINS))
        for action, expected_sha in EXPECTED_ACTION_PINS.items():
            with self.subTest(action=action):
                self.assertEqual(seen[action], {expected_sha})

    def test_runner_python_and_dotnet_versions_are_explicit(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual(workflow.count("runs-on: ubuntu-24.04"), 2)
        self.assertEqual(workflow.count("runs-on: windows-2025"), 2)
        self.assertEqual(workflow.count("python-version: '3.12.14'"), 2)
        self.assertEqual(workflow.count("python-version: '3.12.10'"), 2)
        self.assertIn("dotnet-version: '8.0.424'", workflow)
        for floating in ("ubuntu-latest", "windows-latest", "python-version: '3.12'", "dotnet-version: '8.0.x'"):
            with self.subTest(floating=floating):
                self.assertNotIn(floating, workflow)

    def test_platform_dependency_constraints_match_frozen_ci_environment(self):
        self.assertEqual(_requirements(ROOT / "constraints" / "ci-linux-py312.txt"), EXPECTED_LINUX_CONSTRAINTS)
        self.assertEqual(_requirements(ROOT / "constraints" / "ci-windows-py312.txt"), EXPECTED_WINDOWS_CONSTRAINTS)
        self.assertEqual(_requirements(ROOT / "constraints" / "ci-tools.txt"), EXPECTED_TOOL_LOCK)

    def test_workflow_uses_constraints_and_exact_build_tools_without_floating_upgrades(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python -m pip install -r requirements.txt -c constraints/ci-linux-py312.txt", workflow)
        self.assertEqual(
            workflow.count("python -m pip install -r requirements.txt -c constraints/ci-windows-py312.txt"),
            2,
        )
        self.assertIn("python -m pip install --disable-pip-version-check -r constraints/ci-tools.txt", workflow)
        self.assertEqual(workflow.count('python -m pip install --disable-pip-version-check "pip==26.2.1"'), 3)
        self.assertIn(
            ".\\.p14-wheel-venv\\Scripts\\python.exe -m pip install -c constraints/ci-windows-py312.txt $wheel",
            workflow,
        )
        self.assertNotIn("pip install --upgrade setuptools wheel", workflow)
        self.assertNotIn("pip install --upgrade pip", workflow)

    def test_update_fix_jobs_remain_source_only_and_release_jobs_remain_tag_gated(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        linux_test = workflow.split("\n  test:\n", 1)[1].split("\n  windows-test:\n", 1)[0]
        windows_test = workflow.split("\n  windows-test:\n", 1)[1].split("\n  windows-build:\n", 1)[0]
        windows_build = workflow.split("\n  windows-build:\n", 1)[1].split("\n  release:\n", 1)[0]
        release = workflow.split("\n  release:\n", 1)[1]
        forbidden = (
            "pip wheel",
            "Nuitka",
            "wix build",
            "msiexec",
            "prepare_windows_distribution.py",
            "finalize_release_checksums.py",
            "actions/upload-artifact",
            "gh release",
        )
        for job_name, block in (("test", linux_test), ("windows-test", windows_test)):
            with self.subTest(job=job_name):
                self.assertIn("python scripts/test/audit.py", block)
                for fragment in forbidden:
                    self.assertNotIn(fragment, block)
        self.assertIn("if: startsWith(github.ref, 'refs/tags/v')", windows_build)
        self.assertIn("if: startsWith(github.ref, 'refs/tags/v')", release)
        self.assertIn("needs: [test, windows-test, windows-build]", release)


if __name__ == "__main__":
    unittest.main()
