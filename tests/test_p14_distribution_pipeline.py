from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from src.core import paths as runtime_paths

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "scripts" / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from finalize_release_checksums import digest  # noqa: E402
from generate_wix_source import UPGRADE_CODE, generate_wix_source  # noqa: E402
from prepare_windows_distribution import REQUIRED_RELATIVE_RESOURCES, prepare_distribution  # noqa: E402
from version_info import parse_release_version  # noqa: E402


class P14DistributionPipelineTests(unittest.TestCase):
    def _populate_resources(self, root: Path) -> None:
        for relative in (
            Path('assets/icons/checkmark.svg'),
            Path('assets/icons/search.svg'),
            Path('assets/icons/chevron-down.svg'),
            Path('assets/icons/chevron-up.svg'),
            Path('assets/icons/nav/dashboard.svg'),
            Path('assets/icons/nav/accounts.svg'),
            Path('assets/icons/nav/invoice.svg'),
            Path('assets/icons/nav/customers.svg'),
            Path('assets/icons/nav/tasks.svg'),
            Path('assets/icons/nav/providers.svg'),
            Path('assets/icons/nav/reports.svg'),
            Path('assets/icons/nav/logs.svg'),
            Path('assets/icons/nav/settings.svg'),
            Path('assets/icons/window/minimize.svg'),
            Path('assets/icons/window/maximize.svg'),
            Path('assets/icons/window/restore.svg'),
            Path('assets/icons/window/close.svg'),
            Path('assets/icons/providers/stripe.png'),
            Path('assets/icons/providers/refrens.png'),
            Path('assets/icons/providers/agiled.png'),
            Path('assets/icons/providers/odoo.png'),
            Path('assets/icons/app.png'),
            Path('assets/icons/app.ico'),
            Path('providers/packages/stripe/provider.json'),
            Path('providers/packages/refrens/provider.json'),
            Path('providers/packages/agiled/provider.json'),
        ):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative.as_posix(), encoding="utf-8")

    def test_release_version_maps_five_part_identity_to_pe_msi_and_tag(self):
        release = parse_release_version("1.0.0.1.40")
        self.assertEqual(release.application, "1.0.0.1.40")
        self.assertEqual(release.pe_file_version, "1.0.1.40")
        self.assertEqual(release.msi_version, "1.1.40")
        self.assertEqual(release.tag, "v1.0.0.1.40")
        with self.assertRaises(ValueError):
            parse_release_version("1.0.0.1")

    def test_release_version_maps_six_part_hotfix_identity_without_changing_five_part_mapping(self):
        release = parse_release_version("1.0.0.1.40.2")
        self.assertEqual(release.application, "1.0.0.1.40.2")
        self.assertEqual(release.pe_file_version, "1.0.1.4002")
        self.assertEqual(release.msi_version, "1.1.4002")
        self.assertEqual(release.tag, "v1.0.0.1.40.2")
        with self.assertRaises(ValueError):
            parse_release_version("1.0.0.1.700.1")
        with self.assertRaises(ValueError):
            parse_release_version("1.0.0.1.40.200")

    def test_application_root_preserves_module_root_then_uses_exact_executable_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            simulated_module = tmp_root / "missing" / "src" / "core" / "paths.py"
            simulated_module.parent.mkdir(parents=True)
            simulated_module.write_text("# simulated", encoding="utf-8")
            exe_root = tmp_root / "portable"
            exe_root.mkdir()
            simulated_exe = exe_root / "Invio.exe"
            simulated_exe.write_bytes(b"MZ")
            self._populate_resources(exe_root)
            with patch.object(runtime_paths, "__file__", str(simulated_module)), patch.object(
                runtime_paths.sys, "executable", str(simulated_exe)
            ):
                self.assertEqual(runtime_paths.application_root(), exe_root.resolve())

    def test_prepare_distribution_renames_exe_copies_resources_and_creates_versioned_portable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nuitka = root / "main.dist"
            nuitka.mkdir()
            (nuitka / "main.exe").write_bytes(b"MZ-INVIO")
            (nuitka / "support.dll").write_bytes(b"dll")
            self._populate_resources(nuitka)
            app_dir, portable = prepare_distribution(nuitka, root / "dist" / "windows", root / "dist" / "release")
            self.assertTrue((app_dir / "Invio.exe").is_file())
            self.assertFalse((app_dir / "main.exe").exists())
            self.assertEqual(portable.name, "Invio_v1.0.0.1.49.1_windows_x64_portable.zip")
            with zipfile.ZipFile(portable) as archive:
                self.assertIsNone(archive.testzip())
                names = set(archive.namelist())
                self.assertIn("Invio/Invio.exe", names)
                self.assertIn("Invio/support.dll", names)
                for relative in REQUIRED_RELATIVE_RESOURCES:
                    self.assertIn((Path("Invio") / relative).as_posix(), names)
            checksum = (portable.parent / "SHA256SUMS.txt").read_text(encoding="utf-8")
            self.assertEqual(checksum.strip(), f"{digest(portable)}  {portable.name}")

    def test_wix_source_is_deterministic_per_user_localappdata_and_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist = root / "Invio"
            (dist / "nested").mkdir(parents=True)
            (dist / "Invio.exe").write_bytes(b"exe")
            (dist / "nested" / "module.dll").write_bytes(b"dll")
            first = root / "one.wxs"
            second = root / "two.wxs"
            generate_wix_source(dist, first)
            generate_wix_source(dist, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            text = first.read_text(encoding="utf-8")
            self.assertIn('Scope="perUser"', text)
            self.assertIn('Version="1.1.4901"', text)
            self.assertIn(f'UpgradeCode="{UPGRADE_CODE}"', text)
            self.assertIn('Id="LocalAppDataFolder"', text)
            self.assertIn('Name="Vib Tools"', text)
            self.assertIn('Name="Invio"', text)
            self.assertIn("Invio.exe", text)
            self.assertIn("module.dll", text)
            self.assertIn('Id="ProgramMenuFolder"', text)
            self.assertIn('Name="Invio"', text)
            self.assertIn('Target="[INSTALLFOLDER]Invio.exe"', text)
            self.assertIn('WorkingDirectory="INSTALLFOLDER"', text)
            self.assertIn('On="uninstall"', text)
            self.assertIn('Root="HKCU"', text)
            self.assertEqual(text.count("<Component "), 3)
            self.assertEqual(text.count("<ComponentRef "), 3)

    def test_github_workflow_builds_wheel_nuitka_onedir_wix_msi_and_tag_release(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        required_fragments = (
            'INVIO_VERSION: "1.0.0.1.49.1"',
            'INVIO_PE_VERSION: "1.0.1.4901"',
            'NUITKA_VERSION: "4.1.3"',
            'WIX_VERSION: "6.0.2"',
            "$wixVersion = (wix --version).Trim()",
            "$wixCoreVersion = ($wixVersion -split '\\+', 2)[0]",
            "if ($wixCoreVersion -ne $env:WIX_VERSION)",
            "actions/setup-dotnet@v4",
            "dotnet-version: '8.0.x'",
            "Nuitka/Nuitka-Action@99c9d3ab258c7008c0604617d925574101327e5d",
            "mode: standalone",
            "enable-plugins: pyside6",
            "windows-icon-from-ico: assets/icons/app.ico",
            "keyring.backends",
            "keyring",
            "jaraco.classes",
            "jaraco.context",
            "jaraco.functools",
            "more_itertools",
            "win32ctypes",
            "Smoke compiled protected credential storage",
            "INVIO_P14_COMPILED_CREDENTIAL_SMOKE",
            "wix build build\\Invio.wxs -arch x64 -pdbtype none",
            "p14_distribution_audit.py",
            "actions/upload-artifact@v4",
            "startsWith(github.ref, 'refs/tags/v')",
            "gh release create",
            "gh release upload",
            "python -m pip wheel . --no-deps --no-build-isolation",
            "Install Linux Qt runtime dependencies",
            "QT_QPA_PLATFORM: offscreen",
            "libegl1",
            "libgl1",
            "libopengl0",
            "libxkbcommon-x11-0",
            "libxcb-cursor0",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, workflow)
        self.assertNotIn("PyInstaller", workflow)
        self.assertNotIn("Briefcase", workflow)
        self.assertNotIn("$wixVersion.Trim() -ne $env:WIX_VERSION", workflow)
        self.assertNotIn("user-package-configuration-file: .github/nuitka-keyring.nuitka-package.config.yml", workflow)
        self.assertIn("-pdbtype none", workflow)


    def test_compiled_keyring_contract_covers_code_metadata_and_real_credential_round_trip(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        app_source = (ROOT / "src" / "app.py").read_text(encoding="utf-8")
        config = (ROOT / ".github" / "nuitka-keyring.nuitka-package.config.yml").read_text(encoding="utf-8")
        for package in (
            "keyring.backends",
            "keyring",
            "jaraco.classes",
            "jaraco.context",
            "jaraco.functools",
            "more_itertools",
            "win32ctypes",
        ):
            self.assertIn(package, workflow)
        self.assertIn("include-metadata:", config)
        self.assertIn("'keyring'", config)
        self.assertNotIn("user-package-configuration-file: .github/nuitka-keyring.nuitka-package.config.yml", workflow)
        self.assertIn("INVIO_P14_COMPILED_CREDENTIAL_SMOKE", app_source)
        self.assertIn("store.set_credentials", app_source)
        self.assertIn("store.get_credentials", app_source)
        self.assertIn("store.delete_credentials", app_source)
        self.assertIn("Smoke compiled protected credential storage", workflow)
        self.assertIn("MSI-installed protected credential smoke failed", workflow)



    def test_distribution_audit_accepts_complete_structural_payload_with_exact_checksums(self):
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nuitka = root / "main.dist"
            nuitka.mkdir()
            (nuitka / "main.exe").write_bytes(b"MZ-INVIO")
            self._populate_resources(nuitka)
            _app_dir, portable = prepare_distribution(nuitka, root / "windows", root / "release")
            (root / "release" / "Invio_v1.0.0.1.49.1_windows_x64_setup.msi").write_bytes(b"MSI-STRUCTURAL-TEST-FIXTURE")
            (root / "release" / "invio-1.0.0.1.49.1-py3-none-any.whl").write_bytes(b"WHEEL-STRUCTURAL-TEST-FIXTURE")
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build" / "finalize_release_checksums.py"), str(root / "release")],
                check=True,
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "test" / "p14_distribution_audit.py"),
                    "--release-dir",
                    str(root / "release"),
                    "--version",
                    "1.0.0.1.49.1",
                ],
                check=True,
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertIn("P14 Windows release payload audit PASS", completed.stdout)
            self.assertTrue(portable.is_file())

    def test_p14_audits_preserve_public_version_but_expect_canonical_python_wheel_version(self):
        wheel_audit = (ROOT / "scripts" / "test" / "p14_wheel_audit.py").read_text(encoding="utf-8")
        distribution_audit = (ROOT / "scripts" / "test" / "p14_distribution_audit.py").read_text(encoding="utf-8")
        self.assertIn("canonical_python_wheel_version", wheel_audit)
        self.assertIn("EXPECTED_WHEEL_VERSION", wheel_audit)
        self.assertIn("canonical_python_wheel_version(args.version)", distribution_audit)
        self.assertIn('f"Invio_v{args.version}_windows_x64_portable.zip"', distribution_audit)
        self.assertIn('f"Invio_v{args.version}_windows_x64_setup.msi"', distribution_audit)
        self.assertIn('f"invio-{wheel_version}-py3-none-any.whl"', distribution_audit)

    def test_release_pipeline_files_are_build_only_and_runtime_dependencies_unchanged(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").casefold()
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8").casefold()
        for build_tool in ("nuitka", "wix"):
            self.assertNotIn(build_tool, requirements)
        self.assertNotIn('"nuitka', pyproject)
        self.assertNotIn('"wix', pyproject)


if __name__ == "__main__":
    unittest.main()
