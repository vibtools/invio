from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_release_metadata_is_v100141(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        project_meta = (ROOT / "vibproject.ygit").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        docs_meta = (ROOT / "docs" / "docs.manifest.ygit").read_text(encoding="utf-8")
        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('"version": "1.0.0.1.50.1"', project_meta)
        self.assertIn('"latestVersion": "1.0.0.1.50.1"', project_meta)
        self.assertIn('"current": "1.0.0.1.50.1"', docs_meta)
        self.assertIn('"latest": "1.0.0.1.50.1"', docs_meta)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)

    def test_release_metadata_is_v1001402(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100141()

    def test_release_metadata_is_v1001401(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v1001402()

    def test_release_metadata_is_v100140(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v1001401()

    def test_release_metadata_is_v100139(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100140()

    def test_release_metadata_is_v100138(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100139()

    def test_release_metadata_is_v100137(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100138()

    def test_release_metadata_is_v100136(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100137()

    def test_release_metadata_is_v100135(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100136()

    def test_release_metadata_is_v100134(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100135()

    def test_release_metadata_is_v100133(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100134()

    def test_release_metadata_is_v100132(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100133()

    def test_release_metadata_is_v100131(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100132()

    def test_release_metadata_is_v100130(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100131()

    def test_release_metadata_is_v100129(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100130()

    def test_release_metadata_is_v100128(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100129()

    def test_release_metadata_is_v100127(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100128()

    def test_release_metadata_is_v100126(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100127()

    def test_release_metadata_is_v100125(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100126()

    def test_release_metadata_is_v100123(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100125()

    def test_release_metadata_is_v100121(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100125()


    def test_v1001470_vib_desktop_design_system_truthfulness(self):
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        title_bars = (ROOT / "src" / "ui" / "title_bars.py").read_text(encoding="utf-8")
        tokens = (ROOT / "src" / "ui" / "tokens.py").read_text(encoding="utf-8")
        styles = (ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        dialogs = (ROOT / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.47.0.md").read_text(encoding="utf-8")
        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertNotIn('root.addWidget(self._build_header())', main_window)
        self.assertIn('for group_name, items in NAV_GROUPS', main_window)
        self.assertIn('class MainTitleBar(TitleBar):', title_bars)
        self.assertIn('def build_dialog_shell', title_bars)
        self.assertIn('setObjectName("ModalOverlay")', title_bars)
        self.assertIn('NAV_GROUPS = (', tokens)
        self.assertIn('QLabel#SidebarSectionLabel', styles)
        self.assertIn('QWidget#DialogActionFooter', styles)
        self.assertGreaterEqual(dialogs.count('build_dialog_shell(self)'), 5)
        self.assertIn('"nav/*.svg"', pyproject)
        self.assertIn('"window/*.svg"', pyproject)
        self.assertIn('UI/UX only', release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.47.0.md").read_text(encoding="utf-8")
            scope = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.47.0.md").read_text(encoding="utf-8")
            self.assertIn('description rule A', root_cause)
            self.assertIn('Inline Status', scope)

    def test_project_folder_is_git_ignored(self):
        rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/project/", rules)
        self.assertIn("/project/*", rules)
        self.assertIn("/project/research/*", rules)

    def test_ci_required_root_cause_verification_records_are_narrowly_allowlisted(self):
        """Compatibility test name retained; private project records must stay private."""
        rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/project/", rules)
        self.assertNotIn("!/project/", rules)
        self.assertNotIn("!/project/research/", rules)
        for name in (
            "ROOT_CAUSE_VERIFICATION_v1.0.0.1.47.0.md",
            "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.0.md",
            "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.01.md",
            "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.02.md",
        ):
            with self.subTest(name=name):
                self.assertNotIn(f"!/project/research/{name}", rules)

    def test_distribution_build_helpers_are_explicitly_tracked(self):
        rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("!scripts/build/", rules)
        self.assertIn("!scripts/build/*.py", rules)
        for name in (
            "version_info.py",
            "prepare_windows_distribution.py",
            "generate_wix_source.py",
            "finalize_release_checksums.py",
        ):
            self.assertTrue((ROOT / "scripts" / "build" / name).is_file(), name)

    def test_provider_registry_runtime_files_are_ignored(self):
        rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("providers/registry/*", rules)
        self.assertIn("!providers/registry/.gitkeep", rules)

    def test_required_pages_exist(self):
        page_dir = ROOT / "src" / "ui" / "pages"
        required = {
            "accounts_page.py",
            "dashboard_page.py",
            "invoice_templates_page.py",
            "customer_lists_page.py",
            "tasks_page.py",
            "providers_page.py",
            "reports_page.py",
            "logs_page.py",
            "settings_page.py",
        }
        self.assertTrue(required.issubset({path.name for path in page_dir.glob("*.py")}))

    def test_settings_backend_exists(self):
        self.assertTrue((ROOT / "src" / "core" / "settings" / "manager.py").is_file())
        self.assertTrue((ROOT / "src" / "core" / "settings" / "__init__.py").is_file())

    def test_release_metadata_is_v100119(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        project_meta = (ROOT / "vibproject.ygit").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('"version": "1.0.0.1.50.1"', project_meta)
        self.assertIn('"latestVersion": "1.0.0.1.50.1"', project_meta)
        self.assertIn('"keyring>=25.7,<26"', project_meta)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)

    def test_release_metadata_is_v100117(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100123()

    def test_release_metadata_is_v100116(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100117()

    def test_release_metadata_is_v100115(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100116()

    def test_release_metadata_is_v100114(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100115()

    def test_release_metadata_is_v100113(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100114()

    def test_release_metadata_is_v100111(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100114()

    def test_release_metadata_is_v100110(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100114()

    def test_release_metadata_is_v10019(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100114()

    def test_release_metadata_is_v10018(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100114()

    def test_release_metadata_is_v10017(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100114()

    def test_release_metadata_is_v10014(self):
        """Compatibility alias retained under the no-removal baseline contract."""
        self.test_release_metadata_is_v100114()


    def test_p14_candidate_records_are_truthful_and_packaging_contract_is_present(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.34.md").read_text(encoding="utf-8")
        self.assertIn('"src.core.settings"', pyproject)
        self.assertIn('"providers.packages.stripe"', pyproject)
        self.assertIn('"assets.icons"', pyproject)
        self.assertIn("windows-latest", workflow)
        self.assertIn("p14_windows_smoke.py", workflow)
        self.assertIn("P14 CERTIFICATION PENDING", roadmap)
        self.assertIn("Production-ready: NO", release)
        self.assertIn("NOT EXECUTED", release)
        self.assertTrue((ROOT / "src" / "core" / "paths.py").is_file())
        self.assertTrue((ROOT / "scripts" / "test" / "p14_wheel_audit.py").is_file())
        self.assertTrue((ROOT / "scripts" / "test" / "p14_windows_smoke.py").is_file())
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "P14_LIVE_INTEGRATION_MATRIX_v1.0.0.1.34.md").is_file())
            self.assertTrue((project_root / "research" / "P14_WINDOWS_NATIVE_CERTIFICATION_v1.0.0.1.34.md").is_file())
            pending = (project_root / "specifications" / "P14_CERTIFICATION_PENDING_v1.0.0.1.34.md").read_text(encoding="utf-8")
            self.assertIn("not a production-certified Official Baseline", pending)

    def test_v100135_distribution_pipeline_and_certification_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.35.md").read_text(encoding="utf-8")
        self.assertIn("Nuitka/Nuitka-Action@99c9d3ab258c7008c0604617d925574101327e5d", workflow)
        self.assertIn('WIX_VERSION: "6.0.2"', workflow)
        prepare = (ROOT / "scripts" / "build" / "prepare_windows_distribution.py").read_text(encoding="utf-8")
        distribution_audit = (ROOT / "scripts" / "test" / "p14_distribution_audit.py").read_text(encoding="utf-8")
        self.assertIn("windows_x64_portable.zip", prepare)
        self.assertIn("windows_x64_setup.msi", distribution_audit)
        self.assertIn("gh release create", workflow)
        self.assertIn("P14 CERTIFICATION PENDING", roadmap)
        self.assertIn("Production-ready: NO", release)
        self.assertIn("P11", release)
        self.assertIn("LIVE ACCEPTANCE PENDING", release)
        self.assertTrue((ROOT / "scripts" / "build" / "version_info.py").is_file())
        self.assertTrue((ROOT / "scripts" / "build" / "prepare_windows_distribution.py").is_file())
        self.assertTrue((ROOT / "scripts" / "build" / "generate_wix_source.py").is_file())
        self.assertTrue((ROOT / "scripts" / "test" / "p14_distribution_audit.py").is_file())
        project_root = ROOT / "project"
        if project_root.is_dir():
            pending = (project_root / "specifications" / "P14_CERTIFICATION_PENDING_v1.0.0.1.35.md").read_text(encoding="utf-8")
            self.assertIn("not production-certified", pending)

    def test_v100136_ci_correction_and_certification_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.36.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn("P14 CERTIFICATION PENDING", roadmap)
        self.assertIn("Production-ready: NO", release)
        self.assertIn("GitHub Actions run `31371279808`", release)
        self.assertIn("scripts/build", release)
        self.assertIn("WinError 32", release)
        self.assertTrue((ROOT / "scripts" / "build" / "finalize_release_checksums.py").is_file())
        project_root = ROOT / "project"
        if project_root.is_dir():
            pending = (project_root / "specifications" / "P14_CERTIFICATION_PENDING_v1.0.0.1.36.md").read_text(encoding="utf-8")
            self.assertIn("not production-certified", pending)

    def test_v100137_wix_version_verification_correction_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.37.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('WIX_VERSION: "6.0.2"', workflow)
        self.assertIn("$wixCoreVersion = ($wixVersion -split '\\+', 2)[0]", workflow)
        self.assertIn("GitHub Actions run `31374749523`", release)
        self.assertIn("6.0.2+b3f3403", release)
        self.assertIn("P14: **CERTIFICATION PENDING**", release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            pending = (project_root / "specifications" / "P14_CERTIFICATION_PENDING_v1.0.0.1.37.md").read_text(encoding="utf-8")
            self.assertIn("not production-certified", pending)

    def test_v100138_wixpdb_release_inventory_correction_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.38.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('WIX_VERSION: "6.0.2"', workflow)
        self.assertIn('wix build build\\Invio.wxs -arch x64 -pdbtype none -o $msi', workflow)
        self.assertIn("31386258538", release)
        self.assertIn("93447256779", release)
        self.assertIn(".wixpdb", release)
        self.assertIn("P14: **CERTIFICATION PENDING**", release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            pending = (project_root / "specifications" / "P14_CERTIFICATION_PENDING_v1.0.0.1.38.md").read_text(encoding="utf-8")
            self.assertIn("not production-certified", pending)

    def test_v100139_compiled_keyring_credential_correction_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.39.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertNotIn("user-package-configuration-file: .github/nuitka-keyring.nuitka-package.config.yml", workflow)
        self.assertTrue((ROOT / ".github" / "nuitka-keyring.nuitka-package.config.yml").is_file())
        self.assertIn("Smoke compiled protected credential storage", workflow)
        self.assertIn("INVIO_P14_COMPILED_CREDENTIAL_SMOKE", workflow)
        self.assertIn("Protected credential storage is unavailable.", release)
        self.assertIn("v1.0.0.1.38", release)
        self.assertIn("P14: **CERTIFICATION PENDING**", release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            pending = (project_root / "specifications" / "P14_CERTIFICATION_PENDING_v1.0.0.1.39.md").read_text(encoding="utf-8")
            self.assertIn("not production-certified", pending)

    def test_v100140_live_refrens_ui_customer_defaults_and_icon_correction_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.40.md").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        styles = (ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        settings = (ROOT / "src" / "core" / "settings" / "manager.py").read_text(encoding="utf-8")
        importer = (ROOT / "src" / "customers" / "importers" / "email_importer.py").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn("windows-icon-from-ico: assets/icons/app.ico", workflow)
        self.assertNotIn('payload["terms"]', runtime[runtime.index("def build_refrens_invoice_payload"):runtime.index("def create_and_send_refrens_invoice")])
        self.assertIn("QListWidget {", styles)
        self.assertIn("QMenu {", styles)
        self.assertIn("default_customer_name", settings)
        self.assertIn("default_customer_country", settings)
        self.assertIn("def apply_customer_defaults", importer)
        self.assertIn("LOCAL SOURCE/LIVE CORRECTION CANDIDATE", release)
        self.assertIn("P11 remains **LIVE ACCEPTANCE PENDING**", release)
        self.assertIn("P14 remains **CERTIFICATION PENDING**", release)
        self.assertTrue((ROOT / "docs" / "api" / "refrens-runtime.md").is_file())
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.40.md").is_file())
            self.assertTrue((project_root / "specifications" / "P14_CERTIFICATION_PENDING_v1.0.0.1.40.md").is_file())


    def test_v1001401_refrens_email_settings_brand_and_nuitka_correction_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        settings_page = (ROOT / "src" / "ui" / "pages" / "settings_page.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.40.1.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertNotIn("user-package-configuration-file: .github/nuitka-keyring.nuitka-package.config.yml", workflow)
        self.assertIn('f"/businesses/{url_key}/invoices/{invoice_id}/email"', runtime)
        self.assertIn('stage = "refrens_invoice_create"', runtime)
        self.assertIn('stage = "refrens_invoice_create_email"', runtime)
        self.assertIn("root.setContentsMargins(CONST.page_padding", settings_page)
        self.assertIn("self.settings_grid.setHorizontalSpacing(_SETTINGS_GRID_GAP)", settings_page)
        self.assertIn("P11 remains **LIVE ACCEPTANCE PENDING**", release)
        self.assertIn("P14 remains **CERTIFICATION PENDING**", release)
        self.assertIn("Agiled remains fail-closed", release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.40.1.md").is_file())
            self.assertTrue((project_root / "specifications" / "P14_CERTIFICATION_PENDING_v1.0.0.1.40.1.md").is_file())

    def test_v1001402_agiled_api_test_and_refrens_status_logging_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        adapters = (ROOT / "src" / "core" / "provider_runtime" / "adapters.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.40.2.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('AGILED_PUBLIC_API_BASE_URL = "https://api.agiled.ai"', runtime)
        self.assertIn('AGILED_PUBLIC_API_ME_PATH = "/public/v1/me"', runtime)
        self.assertIn('def _test_agiled_account', runtime)
        self.assertIn('"Authorization": f"Bearer {api_key}"', runtime)
        self.assertIn('f"CODE {exc.http_status}"', runtime)
        self.assertIn('executable_capabilities=frozenset({"api_test"})', adapters)
        self.assertIn('no invoice email/send operation', adapters)
        self.assertIn('provider-side API mail permission', release)
        self.assertIn('GET /public/v1/me', release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.40.2.md").is_file())
            self.assertTrue((project_root / "specifications" / "P14_CERTIFICATION_PENDING_v1.0.0.1.40.2.md").is_file())

    def test_v100141_providers_page_compact_ui_truthfulness(self):
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.41.md").read_text(encoding="utf-8")
        self.assertIn('Parent Official Production Baseline: **v1.0.0.1.40.2**', release)
        self.assertIn('ProviderManager, ProviderRuntime', release)
        self.assertIn('220px', release)
        self.assertIn('2–4', release)

    def test_v1001450_provider_transient_window_fix_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        providers = (ROOT / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        styles = (ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.45.0.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        reflow = providers.split("def _reflow_cards", 1)[1].split("def _apply_filter", 1)[0]
        self.assertIn("item.setVisible(False)", reflow)
        self.assertLess(reflow.index("self.grid.addWidget(item, row, column)"), reflow.index("item.setVisible(True)"))
        self.assertIn("PROVIDER_CARD_HEIGHT = 194", providers)
        self.assertIn("PROVIDER_STATUS_HEIGHT = 18", providers)
        self.assertIn("identity.addWidget(status, 0, Qt.AlignmentFlag.AlignLeft)", providers)
        self.assertIn("QFrame#PluginCard QLabel#StatusBadgeSuccess", styles)
        self.assertIn("visible parentless `QFrame` becomes a temporary native top-level window", release)
        self.assertIn("SQLite remains schema v5", release)
        self.assertIn("P13 remains interface v1", release)

    def test_v1001440_intro_subtitle_cleanup_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        widgets = (ROOT / "src" / "ui" / "widgets.py").read_text(encoding="utf-8")
        tasks = (ROOT / "src" / "ui" / "pages" / "tasks_page.py").read_text(encoding="utf-8")
        providers = (ROOT / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        dashboard = (ROOT / "src" / "ui" / "pages" / "dashboard_page.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.44.0.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertNotIn('text_layout.addWidget(label(description, "Description", True))', widgets)
        self.assertNotIn('layout.addWidget(label(description, "Description", True))', widgets)
        self.assertEqual(widgets.count("_ = description"), 2)
        self.assertNotIn("Independent provider task with dedicated account reservation and worker-thread slot.", tasks)
        self.assertIn('self.setObjectName("PluginCardDescription")', providers)
        self.assertIn('self.next_step = label("", "Description")', dashboard)
        self.assertIn('**Official Parent Baseline:** Invio v1.0.0.1.43.0', release)
        self.assertIn('SQLite remains schema v5', release)
        self.assertIn('P13 remains interface v1', release)

    def test_v1001430_global_data_grid_ui_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        widgets = (ROOT / "src" / "ui" / "widgets.py").read_text(encoding="utf-8")
        accounts = (ROOT / "src" / "ui" / "pages" / "accounts_page.py").read_text(encoding="utf-8")
        customers = (ROOT / "src" / "ui" / "pages" / "customer_lists_page.py").read_text(encoding="utf-8")
        templates = (ROOT / "src" / "ui" / "pages" / "invoice_templates_page.py").read_text(encoding="utf-8")
        reports = (ROOT / "src" / "ui" / "pages" / "reports_page.py").read_text(encoding="utf-8")
        dialogs = (ROOT / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.43.0.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('class DataGridToolbar(QWidget):', widgets)
        self.assertIn('class DataGridPager(QWidget):', widgets)
        self.assertIn('"Search accounts..."', accounts)
        self.assertIn('"Search lists..."', customers)
        self.assertIn('"Search templates..."', templates)
        self.assertIn('"Search delivery history..."', reports)
        self.assertIn('self.accounts = QTableWidget(0, 4)', dialogs)
        self.assertIn('**Official Parent Baseline:** Invio v1.0.0.1.42.0', release)
        self.assertIn('ProviderManager, ProviderRuntime', release)
        self.assertIn('SQLite schema v5', release)

    def test_v1001420_global_forms_and_settings_ui_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        settings = (ROOT / "src" / "ui" / "pages" / "settings_page.py").read_text(encoding="utf-8")
        dialogs = (ROOT / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        styles = (ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.42.0.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Search settings... (Ctrl+F)', settings)
        self.assertIn('button("Reset Settings")', settings)
        self.assertIn('def _filter_settings_cards', settings)
        self.assertIn('def _reflow_settings_grid', settings)
        self.assertIn('def _dialog_footer', dialogs)
        self.assertNotIn('QDialogButtonBox', dialogs)
        self.assertIn("QDialog QLineEdit", styles)
        self.assertIn("QWidget#SettingsPage QPushButton", styles)
        self.assertIn('**Official Parent Baseline:** Invio v1.0.0.1.41.1', release)
        self.assertIn('settings persistence changes are included', release)

    def test_v1001411_providers_page_final_polish_truthfulness(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        page = (ROOT / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        styles = (ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.41.1.md").read_text(encoding="utf-8")
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('PROVIDER_CARD_HEIGHT = 194', page)
        self.assertIn('PROVIDER_LOGO_SIZE = 40', page)
        self.assertIn('"ProviderSearchInput"', page)
        self.assertIn('"ProviderLogo"', page)
        self.assertIn('"Verified" if installed else "Available"', page)
        self.assertIn('"ProviderVersionText"', page)
        self.assertIn('"ProviderUninstallButton"', page)
        self.assertNotIn('"ProviderLogoPlaceholder"', page)
        self.assertNotIn('"ProviderCapabilityChip"', page)
        self.assertNotIn('"ProviderMeta"', page)
        self.assertIn('QPushButton#ProviderUninstallButton', styles)
        self.assertIn('"providers/*.png"', pyproject)
        self.assertIn('Official Parent Baseline: **Invio v1.0.0.1.41**', release)
        self.assertIn('Provider runtime/API behavior is unchanged', release)

    def test_p02_storage_package_and_keyring_dependency_exist(self):
        storage_dir = ROOT / "src" / "core" / "storage"
        self.assertTrue((storage_dir / "domain_store.py").is_file())
        self.assertTrue((storage_dir / "credential_store.py").is_file())
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn('"src.core.storage"', pyproject)
        self.assertIn('keyring>=25.7,<26', pyproject)
        self.assertIn('keyring>=25.7,<26', requirements)

    def test_builtin_provider_runtime_package_exists(self):
        self.assertTrue((ROOT / "src" / "core" / "provider_runtime" / "runtime.py").is_file())
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"src.core.provider_runtime"', pyproject)

    def test_packaged_stripe_and_refrens_providers_exist(self):
        import json

        expected = {
            "stripe": {"secret_key"},
            "refrens": {"base_url", "url_key", "app_id", "app_secret"},
        }
        for provider_id, credential_keys in expected.items():
            manifest_path = ROOT / "providers" / "packages" / provider_id / "provider.json"
            self.assertTrue(manifest_path.is_file(), f"Missing packaged provider: {provider_id}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["id"], provider_id)
            self.assertNotIn("-ui", manifest["version"])
            actual_keys = {field["key"] for field in manifest.get("credential_fields", [])}
            self.assertEqual(actual_keys, credential_keys)

    def test_p09_completion_records_are_synchronized(self):
        public_roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        public_release = (ROOT / "docs" / "release-notes" / "1.0.0.1.25.md").read_text(encoding="utf-8")
        self.assertIn("**P09 - Multi-Account Scheduling, Limits and Health [COMPLETE in v1.0.0.1.25; CI verification-corrected in v1.0.0.1.26]**", public_roadmap)
        self.assertIn("## P09 Completion - v1.0.0.1.25", public_roadmap)
        self.assertIn("## v1.0.0.1.25 P09 Multi-Account Scheduling, Limits and Health", public_readme)
        self.assertIn("Production progress: **9/14**", public_release)
        self.assertIn("P10 - Persistent Delivery Ledger, Idempotency and Recovery", public_release)

        # ``project/`` is intentionally Git-ignored private development material.
        # Validate its richer completion records only when the full private
        # baseline is present; public CI must never require ignored files.
        project_root = ROOT / "project"
        if project_root.is_dir():
            phase_log = (project_root / "planning" / "PHASE_COMPLETION_LOG.md").read_text(encoding="utf-8")
            roadmap = (project_root / "planning" / "PRODUCTION_ROADMAP.md").read_text(encoding="utf-8")
            project_readme = (project_root / "README.md").read_text(encoding="utf-8")
            self.assertIn("## 2026-08-09 - P09 Multi-Account Scheduling, Limits and Health - v1.0.0.1.25", phase_log)
            self.assertIn("Production phases complete: **9 / 14**", phase_log)
            self.assertIn("## P09 - Multi-Account Scheduling, Limits and Health [COMPLETE - v1.0.0.1.25; CI verification-corrected v1.0.0.1.26]", roadmap)
            self.assertIn("- P09: COMPLETE", project_readme)

    def test_p10_completion_records_are_synchronized(self):
        public_roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        public_release = (ROOT / "docs" / "release-notes" / "1.0.0.1.27.md").read_text(encoding="utf-8")
        self.assertIn("## P10 Completion - v1.0.0.1.27", public_roadmap)
        self.assertIn("## P10 Persistent Delivery Ledger and Restart Recovery", public_readme)
        self.assertIn("Production progress: **10/14**", public_release)
        self.assertIn("P11 - Refrens End-to-End Task Enablement", public_release)

        project_root = ROOT / "project"
        if project_root.is_dir():
            phase_log = (project_root / "planning" / "PHASE_COMPLETION_LOG.md").read_text(encoding="utf-8")
            roadmap = (project_root / "planning" / "PRODUCTION_ROADMAP.md").read_text(encoding="utf-8")
            project_readme = (project_root / "README.md").read_text(encoding="utf-8")
            self.assertIn("## 2026-08-09 - P10 Persistent Delivery Ledger, Idempotency and Recovery - v1.0.0.1.27", phase_log)
            self.assertIn("P10 - Persistent Delivery Ledger, Idempotency and Recovery [COMPLETE - v1.0.0.1.27", roadmap)
            self.assertIn("## v1.0.0.1.27 P10 records", project_readme)

    def test_p10_verification_correction_records_are_synchronized(self):
        public_roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        public_release = (ROOT / "docs" / "release-notes" / "1.0.0.1.28.md").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")
        self.assertIn("## P10 Verification Correction - v1.0.0.1.28", public_roadmap)
        self.assertIn("P10 remains complete, production progress remains 10/14", public_roadmap)
        self.assertIn("## v1.0.0.1.28 P10 Verification Correction", public_readme)
        self.assertIn("P11 remains unimplemented", public_readme)
        self.assertIn("P10 Verification Correction", public_release)
        self.assertIn("Production progress remains **10/14**", public_release)
        self.assertIn("DOMAIN_SCHEMA_VERSION = 7", schema)
        self.assertEqual(schema.count("CREATE TABLE task_delivery_"), 3)

        project_root = ROOT / "project"
        if project_root.is_dir():
            phase_log = (project_root / "planning" / "PHASE_COMPLETION_LOG.md").read_text(encoding="utf-8")
            roadmap = (project_root / "planning" / "PRODUCTION_ROADMAP.md").read_text(encoding="utf-8")
            project_readme = (project_root / "README.md").read_text(encoding="utf-8")
            self.assertIn("## 2026-08-09 - P10 verification correction - v1.0.0.1.28", phase_log)
            self.assertIn("P10 - Persistent Delivery Ledger, Idempotency and Recovery [COMPLETE - v1.0.0.1.27; verification-corrected v1.0.0.1.28]", roadmap)
            self.assertIn("## v1.0.0.1.28 P10 verification-correction records", project_readme)

    def test_p11_implementation_candidate_records_are_synchronized(self):
        public_roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        public_release = (ROOT / "docs" / "release-notes" / "1.0.0.1.29.md").read_text(encoding="utf-8")
        adapters = (ROOT / "src" / "core" / "provider_runtime" / "adapters.py").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")

        self.assertIn("P11 remains **IMPLEMENTED / LIVE ACCEPTANCE PENDING**", public_roadmap)
        self.assertIn("P11 remains **IMPLEMENTED / LIVE ACCEPTANCE PENDING**", public_roadmap)
        self.assertIn("Owner explicitly froze `v1.0.0.1.29` and unlocked P12", public_roadmap)
        self.assertIn("P11 is **IMPLEMENTED / LIVE ACCEPTANCE PENDING**", public_readme)
        self.assertIn("**P11 IMPLEMENTED / LIVE ACCEPTANCE PENDING.**", public_release)
        self.assertIn("Production progress remains **10/14**", public_release)
        self.assertIn('task_batch_handler="_run_refrens_batch"', adapters)
        self.assertIn("DOMAIN_SCHEMA_VERSION = 7", schema)
        self.assertEqual(schema.count("CREATE TABLE task_delivery_"), 3)

        project_root = ROOT / "project"
        if project_root.is_dir():
            phase_log = (project_root / "planning" / "PHASE_COMPLETION_LOG.md").read_text(encoding="utf-8")
            roadmap = (project_root / "planning" / "PRODUCTION_ROADMAP.md").read_text(encoding="utf-8")
            project_readme = (project_root / "README.md").read_text(encoding="utf-8")
            pending = (project_root / "specifications" / "P11_LIVE_ACCEPTANCE_PENDING_v1.0.0.1.29.md").read_text(encoding="utf-8")
            self.assertTrue((project_root / "research" / "P11_IMPLEMENTATION_LOG_v1.0.0.1.29.md").is_file())
            self.assertTrue((project_root / "research" / "PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.29.md").is_file())
            self.assertTrue((project_root / "research" / "FINAL_FORENSIC_VERIFICATION_v1.0.0.1.29.md").is_file())
            self.assertIn("P11 Refrens End-to-End | **IMPLEMENTED / LIVE ACCEPTANCE PENDING**", phase_log)
            self.assertIn("## 2026-08-09 - P11 Refrens End-to-End Task implementation candidate - v1.0.0.1.29", phase_log)
            self.assertIn("**Status:** IMPLEMENTED in `v1.0.0.1.29`; LIVE ACCEPTANCE PENDING", roadmap)
            self.assertIn("P11: IMPLEMENTED / LIVE ACCEPTANCE PENDING", project_readme)
            self.assertIn("not a completed-phase Official Baseline", pending)

    def test_p12_completion_records_are_synchronized(self):
        public_roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        public_release = (ROOT / "docs" / "release-notes" / "1.0.0.1.30.md").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")
        reports = (ROOT / "src" / "ui" / "pages" / "reports_page.py").read_text(encoding="utf-8")
        observability = (ROOT / "src" / "core" / "observability.py").read_text(encoding="utf-8")

        self.assertIn("## P12 Completion - v1.0.0.1.30", public_roadmap)
        self.assertIn("P13 remains **COMPLETE / verification-corrected in v1.0.0.1.33**", public_roadmap)
        self.assertIn("P11 remains **IMPLEMENTED / LIVE ACCEPTANCE PENDING**", public_readme)
        self.assertIn("P12 COMPLETE", public_release)
        self.assertIn("Recipient Delivery History", reports)
        self.assertIn("StructuredLogEvent", observability)
        self.assertIn("DOMAIN_SCHEMA_VERSION = 7", schema)
        self.assertEqual(schema.count("CREATE TABLE task_delivery_"), 3)

        project_root = ROOT / "project"
        if project_root.is_dir():
            phase_log = (project_root / "planning" / "PHASE_COMPLETION_LOG.md").read_text(encoding="utf-8")
            baseline = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.30.md")
            self.assertIn("P12 Reports/Logs/Privacy | **COMPLETE**", phase_log)
            self.assertIn("Completed acceptance phases: **12 / 14**", phase_log)
            self.assertTrue(baseline.is_file())

    def test_p12_verification_correction_records_are_synchronized(self):
        public_roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        public_release = (ROOT / "docs" / "release-notes" / "1.0.0.1.31.md").read_text(encoding="utf-8")
        observability = (ROOT / "src" / "core" / "observability.py").read_text(encoding="utf-8")
        domain_store = (ROOT / "src" / "core" / "storage" / "domain_store.py").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")

        self.assertIn("Last fully accepted pre-certification baseline: **Invio v1.0.0.1.33**", public_roadmap)
        self.assertIn("P12 remains **COMPLETE / verification-corrected in v1.0.0.1.31**", public_roadmap)
        self.assertIn("v1.0.0.1.31 P12 Verification Correction", public_readme)
        self.assertIn("P12 COMPLETE / verification-corrected", public_release)
        self.assertIn("accessToken", observability)
        self.assertIn("provider_send_acceptance != \"Accepted\"", domain_store)
        self.assertIn("conflicting account assignment evidence", domain_store)
        self.assertIn("DOMAIN_SCHEMA_VERSION = 7", schema)
        self.assertEqual(schema.count("CREATE TABLE task_delivery_"), 3)

        project_root = ROOT / "project"
        if project_root.is_dir():
            phase_log = (project_root / "planning" / "PHASE_COMPLETION_LOG.md").read_text(encoding="utf-8")
            roadmap = (project_root / "planning" / "PRODUCTION_ROADMAP.md").read_text(encoding="utf-8")
            self.assertIn("P12 forensic verification correction - v1.0.0.1.31", phase_log)
            self.assertIn("VERIFICATION-CORRECTED - v1.0.0.1.31", roadmap)
            self.assertTrue((project_root / "research" / "P12_VERIFICATION_CORRECTION_v1.0.0.1.31.md").is_file())
            self.assertTrue((project_root / "research" / "FINAL_FORENSIC_VERIFICATION_v1.0.0.1.31.md").is_file())
            self.assertTrue((project_root / "research" / "PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.31.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.31.md").is_file())

    def test_p13_completion_records_are_synchronized(self):
        public_roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        public_release = (ROOT / "docs" / "release-notes" / "1.0.0.1.32.md").read_text(encoding="utf-8")
        external = (ROOT / "src" / "core" / "provider_runtime" / "external.py").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")
        self.assertIn("Last fully accepted pre-certification baseline: **Invio v1.0.0.1.33**", public_roadmap)
        self.assertIn("Completed acceptance phases: **12 / 14**", public_roadmap)
        self.assertIn("P13 Completion - v1.0.0.1.32", public_roadmap)
        self.assertIn("v1.0.0.1.32 P13 Executable External Provider Adapter Contract", public_readme)
        self.assertIn("P13 is COMPLETE", public_release)
        self.assertIn("P11 remains **IMPLEMENTED / LIVE ACCEPTANCE PENDING**", public_release)
        self.assertIn("EXTERNAL_ADAPTER_INTERFACE_VERSION = 1", external)
        self.assertIn("DOMAIN_SCHEMA_VERSION = 7", schema)
        self.assertEqual(schema.count("CREATE TABLE task_delivery_"), 3)

        project_root = ROOT / "project"
        if project_root.is_dir():
            phase_log = (project_root / "planning" / "PHASE_COMPLETION_LOG.md").read_text(encoding="utf-8")
            roadmap = (project_root / "planning" / "PRODUCTION_ROADMAP.md").read_text(encoding="utf-8")
            self.assertIn("P13 External Provider Runtime Contract | **COMPLETE / VERIFICATION-CORRECTED**", phase_log)
            self.assertIn("Completed acceptance phases: **12 / 14**", phase_log)
            self.assertIn("P13 - Executable External Provider Adapter Contract [COMPLETE - v1.0.0.1.32; VERIFICATION-CORRECTED - v1.0.0.1.33]", roadmap)
            self.assertTrue((project_root / "research" / "P13_IMPLEMENTATION_LOG_v1.0.0.1.32.md").is_file())
            self.assertTrue((project_root / "research" / "FINAL_FORENSIC_VERIFICATION_v1.0.0.1.32.md").is_file())
            self.assertTrue((project_root / "research" / "PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.32.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.32.md").is_file())

    def test_p13_verification_correction_records_are_synchronized(self):
        public_roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        public_release = (ROOT / "docs" / "release-notes" / "1.0.0.1.33.md").read_text(encoding="utf-8")
        external = (ROOT / "src" / "core" / "provider_runtime" / "external.py").read_text(encoding="utf-8")
        manager = (ROOT / "src" / "core" / "provider_manager" / "manager.py").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")

        self.assertIn("Last fully accepted pre-certification baseline: **Invio v1.0.0.1.33**", public_roadmap)
        self.assertIn("P13 remains **COMPLETE / verification-corrected in v1.0.0.1.33**", public_roadmap)
        self.assertIn("v1.0.0.1.33 P13 Verification Correction", public_readme)
        self.assertIn("P13 COMPLETE / verification-corrected", public_release)
        self.assertIn("External adapter metadata validation failed", external)
        self.assertIn("os.replace(target, staged_manifest)", manager)
        self.assertIn("os.replace(staged_manifest, target)", manager)
        self.assertIn("DOMAIN_SCHEMA_VERSION = 7", schema)
        self.assertEqual(schema.count("CREATE TABLE task_delivery_"), 3)

        project_root = ROOT / "project"
        if project_root.is_dir():
            phase_log = (project_root / "planning" / "PHASE_COMPLETION_LOG.md").read_text(encoding="utf-8")
            roadmap = (project_root / "planning" / "PRODUCTION_ROADMAP.md").read_text(encoding="utf-8")
            self.assertIn("P13 forensic verification correction - v1.0.0.1.33", phase_log)
            self.assertIn("VERIFICATION-CORRECTED - v1.0.0.1.33", roadmap)
            self.assertTrue((project_root / "research" / "P13_VERIFICATION_CORRECTION_v1.0.0.1.33.md").is_file())
            self.assertTrue((project_root / "research" / "FINAL_FORENSIC_VERIFICATION_v1.0.0.1.33.md").is_file())
            self.assertTrue((project_root / "research" / "PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.33.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.33.md").is_file())

    def test_p05_schema_v4_and_task_snapshot_contract_exist(self):
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")
        task_model = (ROOT / "src" / "tasks" / "models" / "task.py").read_text(encoding="utf-8")
        self.assertIn("DOMAIN_SCHEMA_VERSION = 7", schema)
        self.assertIn("CREATE TABLE task_execution_snapshots", schema)
        self.assertIn("CREATE TABLE task_snapshot_customers", schema)
        self.assertIn("CREATE TABLE task_snapshot_template", schema)
        self.assertIn("class TaskExecutionSnapshot", task_model)
        self.assertIn('TASK_ASSIGNMENT_STRATEGY = "recipient_ordinal_round_robin_v1"', task_model)



class V1497DistributionAuditCorrectionReleaseContractTests(unittest.TestCase):
    def test_v1497_identity_ci_root_cause_and_frozen_runtime_boundaries_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        distribution_audit = (ROOT / "scripts" / "test" / "p14_distribution_audit.py").read_text(encoding="utf-8")
        p14_tests = (ROOT / "tests" / "test_p14_distribution_pipeline.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        odoo = (ROOT / "providers" / "plugins" / "odoo" / "adapter.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.7.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.49.7.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertNotIn('Invio/truststore/__init__.py', distribution_audit)
        self.assertNotIn("Path('truststore/__init__.py')", p14_tests)
        self.assertIn('Smoke compiled Windows native TLS backend', workflow)
        self.assertIn('MSI-installed Windows native TLS backend smoke failed', workflow)
        self.assertIn('_truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)', runtime)
        self.assertIn('halt_batch: bool = False', runtime)
        self.assertIn('ADAPTER_VERSION = "1.0.1"', odoo)
        self.assertIn('CI Release-Audit Correction', release)
        self.assertIn('Phase 1 and Phase 2 runtime behavior remains unchanged', manifest)



if __name__ == "__main__":
    unittest.main()


class V1480DialogChromeReleaseContractTests(unittest.TestCase):
    def test_v148_current_identity_and_scope_records_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.48.0.md").read_text(encoding="utf-8")
        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn("right margin", release)
        self.assertIn("subtle shadow", release)
        self.assertIn("title duplication", release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.0.md").read_text(encoding="utf-8")
            scope = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.48.0.md").read_text(encoding="utf-8")
            self.assertIn("zero right margin", root_cause)
            self.assertIn("duplicate body PageTitle", root_cause)
            self.assertIn("v1.0.0.1.47.0", scope)
            self.assertIn("chrome/dialog presentation only", scope)



class V14801TaskCloseHotfixContractTests(unittest.TestCase):
    def test_v14801_current_identity_and_task_close_scope_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        dialogs = (ROOT / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.48.01.md").read_text(encoding="utf-8")
        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        close = main_window.split("def close_task", 1)[1].split("def _task_persistence_failure", 1)[0]
        self.assertIn("force_widget_dialog=True", close)
        self.assertIn("QMessageBox.Option.DontUseNativeDialog", dialogs)
        self.assertIn("Task Close confirmation", release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.01.md").read_text(encoding="utf-8")
            scope = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.48.01.md").read_text(encoding="utf-8")
            self.assertIn("backend close path remained valid", root_cause)
            self.assertIn("Tasks subsystem only", scope)


class V14802PopupLifecycleReleaseContractTests(unittest.TestCase):
    def test_v14802_current_identity_and_popup_lifecycle_scope_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        dialogs = (ROOT / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        chrome = (ROOT / "src" / "ui" / "title_bars.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.48.02.md").read_text(encoding="utf-8")
        wheel_audit = (ROOT / "scripts" / "test" / "p14_wheel_audit.py").read_text(encoding="utf-8")
        distribution_audit = (ROOT / "scripts" / "test" / "p14_distribution_audit.py").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn("box.setOption(QMessageBox.Option.DontUseNativeDialog, True)", dialogs)
        self.assertIn("install_dialog_chrome(box, preserve_client_height=False)", dialogs)
        self.assertIn("layout = dialog.layout()", chrome)
        self.assertIn("caller-captured Qt-owned `QMessageBox.layout()`", release)
        self.assertIn("wrapper stale", release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.02.md").read_text(encoding="utf-8")
            scope = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.48.02.md").read_text(encoding="utf-8")
            self.assertIn("libshiboken", root_cause)
            self.assertIn("Global QMessageBox / Popup Lifecycle", scope)
        self.assertIn("1.0.0.1.48.2", release)
        self.assertIn("invio-1.0.0.1.48.2-py3-none-any.whl", release)
        self.assertIn("EXPECTED_WHEEL_VERSION", wheel_audit)
        self.assertIn('f"invio-{wheel_version}-py3-none-any.whl"', distribution_audit)


class V1484NewTaskCompactModalReleaseContractTests(unittest.TestCase):
    def test_v1484_current_identity_and_release_records_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.48.4.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn("Install Linux Qt runtime dependencies", workflow)
        self.assertIn("QT_QPA_PLATFORM: offscreen", workflow)
        self.assertIn("/project/", gitignore)
        self.assertNotIn("!/project/", gitignore)
        self.assertNotIn("!/project/research/", gitignore)
        self.assertIn("Compact Add Task Modal UI Redesign", release)
        self.assertIn("Provider + account filters + account search", release)
        self.assertIn("Invoice Template + Customer List + Cancel + Create Task", release)
        self.assertIn("1.1.4804", release)
        self.assertIn("invio", pyproject)

        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.4.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.48.4.md").is_file())


class V1485AccountsFlatTableReleaseContractTests(unittest.TestCase):
    def test_v1485_current_identity_and_release_records_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.48.5.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)
        self.assertIn("Accounts Page — Compact Flat Account Table & Semantic Status UI", release)
        self.assertIn("ACCOUNT`, `PROVIDER`, `STATUS`, `ACTION", release)
        self.assertIn("Edit`, `Re-test` and `Delete", release)
        self.assertIn("1.1.4805", release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.5.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.48.5.md").is_file())


class V1486AccountsActionMenuCorrectionReleaseContractTests(unittest.TestCase):
    def test_v1486_current_identity_and_release_records_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.48.6.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)
        self.assertIn('Accounts Page — Action Column & Context Menu UI Correction', release)
        self.assertIn('`ACTION` at 68px', release)
        self.assertIn('current screen availableGeometry', release)
        self.assertIn('1.1.4806', release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.6.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.48.6.md").is_file())

class V1487GlobalStatusRenderingReleaseContractTests(unittest.TestCase):
    def test_v1487_current_identity_and_global_status_scope_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.48.7.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)
        self.assertIn('Global Status Badge Rendering & Table Cell Alignment Fix', release)
        self.assertIn('set_data_status_cell', release)
        self.assertIn('1.1.4807', release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.7.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.48.7.md").is_file())
class V1488StatusColumnRuntimeCorrectionReleaseContractTests(unittest.TestCase):
    def test_v1488_current_identity_and_status_column_scope_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.48.8.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)
        self.assertIn('Canonical Status Column Natural-Width Runtime Correction', release)
        self.assertIn('QHeaderView.ResizeToContents', release)
        self.assertIn('1.1.4808', release)
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.8.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.48.8.md").is_file())

class V1489CustomerListsGlobalHeaderReleaseContractTests(unittest.TestCase):
    def test_v1489_current_identity_and_ui_scope_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.48.9.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.48.9.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)
        self.assertIn('Customer Lists Compact UI + Global Header Standardization', release)
        self.assertIn('UI-only', release)
        self.assertIn('No provider/runtime logic', release)
        self.assertIn('Customer Lists final compact design', manifest)
        self.assertIn('No backend/provider/storage/business behavior change', manifest)
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.9.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.48.9.md").is_file())



class V149ProviderSettingsTemplatesReportsReleaseContractTests(unittest.TestCase):
    def test_v149_current_identity_and_locked_ui_scope_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.49.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)
        self.assertIn('Provider/Settings Compact Header + Template/Reports Table Layout Fix', release)
        self.assertIn('UI-only correction', release)
        self.assertIn('Preserves `TEMPLATE / CURRENCY / TYPE / DUE / ITEMS / TAX / ACTIONS`', release)
        self.assertIn('Preserves all 9 Task Summary columns and all 11 Recipient Delivery History columns/values', release)
        self.assertIn('No provider API', release)
        self.assertIn('Official parent baseline: `Invio_v1.0.0.1.48.9_Baseline.zip`', manifest)
        self.assertIn('Content-preservation lock', manifest)
        project_root = ROOT / "project"
        if project_root.is_dir():
            self.assertTrue((project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.md").is_file())
            self.assertTrue((project_root / "research" / "FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.md").is_file())
            self.assertTrue((project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.49.md").is_file())

class V1491PersistentBrowserOAuthMsiReleaseContractTests(unittest.TestCase):
    def test_v1491_current_identity_msi_and_browser_oauth_scope_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        oauth = (ROOT / "src" / "core" / "provider_runtime" / "oauth.py").read_text(encoding="utf-8")
        wix = (ROOT / "scripts" / "build" / "generate_wix_source.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.1.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.49.1.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)
        self.assertIn('class LoopbackOAuthReceiver:', oauth)
        self.assertIn('secrets.compare_digest', oauth)
        self.assertIn('Name": "Invio"', wix)
        self.assertIn('ProgramMenuFolder', wix)
        self.assertIn('Start Menu', release)
        self.assertIn('Signing Option C', release)
        self.assertIn('Host-managed Browser OAuth authorization system', manifest)
        self.assertIn('Signing Option C is frozen', manifest)
        self.assertNotIn('signtool', workflow.casefold())

        # /project is a deliberately private, Git-ignored forensic workspace.
        # Validate those records only when a full private baseline is present;
        # clean public GitHub checkouts must never depend on ignored files.
        project_root = ROOT / "project"
        if project_root.is_dir():
            baseline = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.49.1.md").read_text(encoding="utf-8")
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.1.md").read_text(encoding="utf-8")
            self.assertIn('no signing integration', baseline)
            self.assertIn('Browser OAuth', root_cause)

class V1492ProviderEasyOnboardingCompatibilityReleaseContractTests(unittest.TestCase):
    def test_v1492_identity_scope_and_root_cause_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        dialogs = (ROOT / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.2.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.49.2.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)
        self.assertIn('checker = getattr(self.provider_runtime, "supports_onboarding", None)', dialogs)
        self.assertNotIn('self.provider_runtime.supports_onboarding(provider.id)', dialogs)
        self.assertIn('Browser-OAuth-only', release)
        self.assertIn('Official current baseline', manifest)
        self.assertIn('v1.0.0.1.49.1 Provider Easy Onboarding V1', manifest)
        self.assertIn('No provider Task/send semantics', release)

        project_root = ROOT / "project"
        if project_root.is_dir():
            scope = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.49.2.md").read_text(encoding="utf-8")
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.2.md").read_text(encoding="utf-8")
            self.assertIn('supports_onboarding', root_cause)
            self.assertIn('scope lock', scope.casefold())


class V1493ProviderIvxPackageReleaseContractTests(unittest.TestCase):
    def test_v1493_identity_ivx_scope_and_frozen_boundaries_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        manager = (ROOT / "src" / "core" / "provider_manager" / "manager.py").read_text(encoding="utf-8")
        ivx = (ROOT / "src" / "core" / "provider_manager" / "ivx.py").read_text(encoding="utf-8")
        page = (ROOT / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.3.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.49.3.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio Provider Extension (*.ivx)', main_window)
        self.assertIn('def import_ivx(self, path: str | Path)', manager)
        self.assertIn('Loading an IVX package must never import/execute adapter.py', manager)
        self.assertIn('IVX_FORMAT_VERSION = 1', ivx)
        self.assertIn('MAX_IVX_COMPRESSED_BYTES = 50 * 1024 * 1024', ivx)
        self.assertIn('MAX_IVX_EXTRACTED_BYTES = 200 * 1024 * 1024', ivx)
        self.assertIn('logo_resolver = getattr(self.manager, "provider_logo_path", None)', page)
        self.assertIn('fallback.png', page)
        self.assertIn('Provider IVX Package System V1', release)
        self.assertIn('Load never executes `adapter.py`', release)
        self.assertIn('Official frozen parent', manifest)
        self.assertIn('Invio v1.0.0.1.49.2', manifest)
        self.assertIn('Task state machine', manifest)
        self.assertTrue((ROOT / "scripts" / "provider" / "build_ivx.py").is_file())
        self.assertTrue((ROOT / "assets" / "icons" / "providers" / "fallback.png").is_file())

        project_root = ROOT / "project"
        if project_root.is_dir():
            scope = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.49.3.md").read_text(encoding="utf-8")
            security = (project_root / "research" / "IVX_SECURITY_VERIFICATION_v1.0.0.1.49.3.md").read_text(encoding="utf-8")
            self.assertIn('Provider IVX Package System V1', scope)
            self.assertIn('must not execute `adapter.py`', scope)
            self.assertIn('path traversal', security)
            self.assertIn('rollback', security)


class V1494ProviderIvxWindowsCompatibilityReleaseContractTests(unittest.TestCase):
    def test_v1494_identity_root_causes_and_scope_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        ivx = (ROOT / "src" / "core" / "provider_manager" / "ivx.py").read_text(encoding="utf-8")
        provider_page = (ROOT / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        builder = (ROOT / "scripts" / "provider" / "build_ivx.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.4.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.49.4.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Production • v1.0.0.1.50.1', main_window)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)

        self.assertIn('name = info.orig_filename', ivx)
        self.assertIn('raw_parts = name.split("/")', ivx)
        self.assertIn('MAX_IVX_LOGO_DIMENSION = 4096', ivx)
        self.assertIn('NotImplementedError', ivx)
        self.assertIn('logo_resolver = getattr(self.manager, "provider_logo_path", None)', provider_page)
        self.assertNotIn('self.manager.provider_logo_path(provider.id)', provider_page)
        self.assertIn('temporary = output.with_name(output.stem + ".tmp.ivx")', builder)
        self.assertLess(builder.index('inspect_ivx(temporary)'), builder.index('temporary.replace(output)'))

        self.assertIn('Native Windows ZIP-name normalization', release)
        self.assertIn('Provider IVX Package System V1 verification/correction only', manifest)
        self.assertIn('Task state machine', manifest)
        self.assertIn('Browser OAuth V1', manifest)
        self.assertIn('MSI/WiX', manifest)

        project_root = ROOT / "project"
        if project_root.is_dir():
            scope = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.49.4.md").read_text(encoding="utf-8")
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.4.md").read_text(encoding="utf-8")
            verification = (project_root / "research" / "UPDATE_IMPLEMENTATION_VERIFICATION_v1.0.0.1.49.4.md").read_text(encoding="utf-8")
            self.assertIn('Provider IVX Package System V1', scope)
            self.assertIn('orig_filename', root_cause)
            self.assertIn('ManagerStub', root_cause)
            self.assertIn('Plan-to-implementation findings', verification)


class V1495WindowsNativeTlsReleaseContractTests(unittest.TestCase):
    def test_v1495_identity_tls_security_scope_and_distribution_contract_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        app_source = (ROOT / "src" / "app.py").read_text(encoding="utf-8")
        odoo = (ROOT / "providers" / "plugins" / "odoo" / "adapter.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.5.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.49.5.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('truststore>=0.10.4,<0.11', requirements)
        self.assertIn('truststore>=0.10.4,<0.11', pyproject)
        self.assertIn('import truststore as _truststore', runtime)
        self.assertIn('_truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)', runtime)
        self.assertIn('context.verify_mode = ssl.CERT_REQUIRED', runtime)
        self.assertIn('context.check_hostname = True', runtime)
        self.assertIn('def _verified_urlopen', runtime)
        self.assertIn('context=_windows_native_tls_context()', runtime)
        tls_helper = runtime.split('def _windows_native_tls_context', 1)[1].split('def _verified_urlopen', 1)[0]
        self.assertNotIn('CERT_NONE', tls_helper)
        self.assertNotIn('check_hostname = False', tls_helper)
        self.assertNotIn('truststore', odoo)
        self.assertIn('truststore', workflow)
        self.assertIn('INVIO_P14_COMPILED_TLS_SMOKE', app_source)
        self.assertIn('Smoke compiled Windows native TLS backend', workflow)
        self.assertIn('MSI-installed Windows native TLS backend smoke failed', workflow)
        self.assertIn('Windows/RDP Native TLS Trust Correction', release)
        self.assertIn('Phase 1', manifest)
        self.assertIn('Phase 2-4', manifest)

        project_root = ROOT / "project"
        if project_root.is_dir():
            scope = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.49.5.md").read_text(encoding="utf-8")
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.5.md").read_text(encoding="utf-8")
            verification = (project_root / "research" / "UPDATE_IMPLEMENTATION_VERIFICATION_v1.0.0.1.49.5.md").read_text(encoding="utf-8")
            self.assertIn('Phase 1', scope)
            self.assertIn('CryptoAPI', root_cause)
            self.assertIn('truststore.SSLContext', verification)


class V1496ProviderFatalLimitCircuitBreakerContractTests(unittest.TestCase):
    def test_v1496_identity_phase2_circuit_breaker_and_frozen_boundaries_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        odoo = (ROOT / "providers" / "plugins" / "odoo" / "adapter.py").read_text(encoding="utf-8")
        odoo_manifest = (ROOT / "providers" / "plugins" / "odoo" / "provider.json").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.6.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.49.6.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('halt_batch: bool = False', runtime)
        self.assertIn('halt_code: str | None = None', runtime)
        self.assertIn('user_message: str | None = None', runtime)
        self.assertIn('if halt_error is not None:', runtime)
        self.assertIn('No additional recipients were started after the provider stop condition.', runtime)
        self.assertIn('Resolved {summary.processed}/{len(snapshot.customer_emails)} external recipient(s)', runtime)
        self.assertIn('provider_stop_message.startswith("Stopped: ")', main_window)
        self.assertIn('ADAPTER_VERSION = "1.0.1"', odoo)
        self.assertIn('scheduling_policy = None', odoo)
        self.assertIn('halt_code="daily-email-limit"', odoo)
        self.assertIn('halt_code="mail-evidence-unverified"', odoo)
        self.assertIn('"version": "1.0.1"', odoo_manifest)
        self.assertIn('"adapter_version": "1.0.1"', odoo_manifest)
        self.assertIn('Provider Fatal-Limit Circuit Breaker', release)
        self.assertIn('Phase 2', manifest)
        self.assertIn('Phase 3', manifest)
        self.assertIn('Phase 4', manifest)
        self.assertIn('truststore>=0.10.4,<0.11', pyproject)

        project_root = ROOT / "project"
        if project_root.is_dir():
            scope = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.49.6.md").read_text(encoding="utf-8")
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.6.md").read_text(encoding="utf-8")
            verification = (project_root / "research" / "UPDATE_IMPLEMENTATION_VERIFICATION_v1.0.0.1.49.6.md").read_text(encoding="utf-8")
            self.assertIn('Phase 2', scope)
            self.assertIn('recipient loop', root_cause)
            self.assertIn('Uncertain', verification)


class V1498SendingControlsReleaseContractTests(unittest.TestCase):
    def test_v1498_identity_phase3_controls_and_frozen_boundaries_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        settings = (ROOT / "src" / "core" / "settings" / "manager.py").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")
        task_model = (ROOT / "src" / "tasks" / "models" / "task.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        external = (ROOT / "src" / "core" / "provider_runtime" / "external.py").read_text(encoding="utf-8")
        settings_page = (ROOT / "src" / "ui" / "pages" / "settings_page.py").read_text(encoding="utf-8")
        worker = (ROOT / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        odoo = (ROOT / "providers" / "plugins" / "odoo" / "adapter.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.8.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('SETTINGS_SCHEMA_VERSION = 2', settings)
        self.assertIn('NETWORK_TIMEOUT_MIN_SECONDS = 10.0', settings)
        self.assertIn('NETWORK_TIMEOUT_MAX_SECONDS = 120.0', settings)
        self.assertIn('MAX_AUTOMATIC_ATTEMPTS_LIMIT = 3', settings)
        self.assertIn('RECIPIENT_DELAY_MAX_SECONDS = 60.0', settings)
        self.assertIn('DOMAIN_SCHEMA_VERSION = 7', schema)
        self.assertIn('MIGRATION_V5_TO_V6', schema)
        self.assertIn('class TaskSendingControls', task_model)
        self.assertIn('sending_controls: TaskSendingControls', task_model)
        self.assertIn('def resolve_task_sending_controls', runtime)
        self.assertIn('def _wait_additional_recipient_delay', runtime)
        self.assertIn('def validate_provider_rate_overrides', runtime)
        self.assertIn('burst_capacity != 1', external)
        self.assertIn('Sending & Retry', settings_page)
        self.assertIn('Provider Rate Limits', settings_page)
        self.assertIn('class WorkerManager', worker)
        self.assertIn('scheduling_policy = None', odoo)
        self.assertIn('Dynamic Tags', release)
        self.assertIn('one QThread per active Task', release)


class V1499WindowsPhase3CiCorrectionReleaseContractTests(unittest.TestCase):
    def test_v1499_identity_windows_sqlite_fixture_correction_and_frozen_boundaries_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        storage_tests = (ROOT / "tests" / "test_storage.py").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")
        store = (ROOT / "src" / "core" / "storage" / "domain_store.py").read_text(encoding="utf-8")
        settings = (ROOT / "src" / "core" / "settings" / "manager.py").read_text(encoding="utf-8")
        worker = (ROOT / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.49.9.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertGreaterEqual(storage_tests.count('with closing(sqlite3.connect(db_path)) as connection:'), 2)
        self.assertNotIn('with sqlite3.connect(db_path) as connection:', storage_tests)
        self.assertIn('DOMAIN_SCHEMA_VERSION = 7', schema)
        self.assertIn('finally:\n            connection.close()', store)
        self.assertIn('SETTINGS_SCHEMA_VERSION = 2', settings)
        self.assertIn('class WorkerManager', worker)
        self.assertIn('WinError 32', release)
        self.assertIn('No production storage implementation', release)


class V150DynamicTagsReleaseContractTests(unittest.TestCase):
    def test_v150_identity_dynamic_tags_schema_and_frozen_boundaries_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        dynamic = (ROOT / "src" / "core" / "dynamic_tags.py").read_text(encoding="utf-8")
        customer_model = (ROOT / "src" / "customers" / "models" / "customer_list.py").read_text(encoding="utf-8")
        importer = (ROOT / "src" / "customers" / "importers" / "email_importer.py").read_text(encoding="utf-8")
        task_model = (ROOT / "src" / "tasks" / "models" / "task.py").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        worker = (ROOT / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.50.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.50.md").read_text(encoding="utf-8")

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('SUPPORTED_DYNAMIC_TAGS', dynamic)
        for tag in ("#NAME#", "#EMAIL#", "#R5#", "#R11#", "#DATE#", "#DATE-NAME#", "#YAAR#"):
            self.assertIn(tag, dynamic)
        self.assertIn('"invio-dynamic-tags-v1"', dynamic)
        self.assertIn('hashlib.sha256', dynamic)
        self.assertIn('rendered = rendered.replace(tag, replacement)', dynamic)
        self.assertIn('name_is_dynamic: bool = False', customer_model)
        self.assertIn('contains_supported_dynamic_tag(configured_name)', importer)
        self.assertIn('dynamic_tags_version: int = 0', task_model)
        self.assertIn('tag_reference_utc: str = ""', task_model)
        self.assertIn('DOMAIN_SCHEMA_VERSION = 7', schema)
        self.assertIn('MIGRATION_V6_TO_V7', schema)
        self.assertIn('name_is_dynamic INTEGER NOT NULL DEFAULT 0', schema)
        self.assertIn('dynamic_tags_version INTEGER NOT NULL DEFAULT 0', schema)
        self.assertIn('tag_reference_utc TEXT NOT NULL DEFAULT', schema)
        self.assertIn('def _render_recipient_dynamic_inputs', runtime)
        self.assertIn('render_invoice_template(snapshot.template, tag_context)', runtime)
        self.assertIn('class WorkerManager', worker)
        self.assertIn('KEEP_LITERAL', release)
        self.assertIn('Task-creation UTC', release)
        self.assertIn('Phase 4 Dynamic Tags Patch Manifest', manifest)

        project_root = ROOT / "project"
        if project_root.is_dir():
            completion = (project_root / "planning" / "PHASE_04_DYNAMIC_TAGS_COMPLETION_v1.0.0.1.50.md").read_text(encoding="utf-8")
            freeze = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.50.md").read_text(encoding="utf-8")
            verification = (project_root / "research" / "UPDATE_IMPLEMENTATION_VERIFICATION_v1.0.0.1.50.md").read_text(encoding="utf-8")
            self.assertIn('KEEP_LITERAL', completion)
            self.assertIn('This baseline contains only', freeze)
            self.assertIn('deterministic fixed-width R5/R11', verification)


class V1501Phase1To4ReleaseReadinessContractTests(unittest.TestCase):
    def test_v1501_identity_green_parent_ci_and_frozen_phase1_to4_boundaries_are_truthful(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")
        settings = (ROOT / "src" / "core" / "settings" / "manager.py").read_text(encoding="utf-8")
        dynamic = (ROOT / "src" / "core" / "dynamic_tags.py").read_text(encoding="utf-8")
        worker = (ROOT / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        odoo = (ROOT / "providers" / "plugins" / "odoo" / "adapter.py").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "release-notes" / "1.0.0.1.50.1.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PATCH_MANIFEST_v1.0.0.1.50.1.md").read_text(encoding="utf-8")
        prior_manifest_lines = (ROOT / "PATCH_MANIFEST_v1.0.0.1.50.md").read_text(encoding="utf-8").splitlines()

        self.assertIn('version = "1.0.0.1.50.1"', pyproject)
        self.assertIn('INVIO_VERSION: "1.0.0.1.50.1"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.5001"', workflow)
        self.assertIn('Invio/1.0.0.1.50.1', runtime)
        self.assertIn('DOMAIN_SCHEMA_VERSION = 7', schema)

        # Phase 1 remains fail-closed Windows native TLS.
        self.assertIn('_truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)', runtime)
        self.assertIn('context.verify_mode = ssl.CERT_REQUIRED', runtime)
        self.assertIn('context.check_hostname = True', runtime)
        self.assertNotIn('verify=False', runtime)
        self.assertNotIn('ssl.CERT_NONE', runtime)
        self.assertNotIn('check_hostname = False', runtime)

        # Phase 2 remains the accepted generic/Odoo terminal-stop contract.
        self.assertIn('halt_batch: bool = False', runtime)
        self.assertIn('halt_code: str | None = None', runtime)
        self.assertIn('halt_code="daily-email-limit"', odoo)
        self.assertIn('halt_code="mail-evidence-unverified"', odoo)

        # Phase 3 remains bounded/frozen and Phase 4 remains schema-v7 Dynamic Tags V1.
        self.assertIn('network_timeout_seconds: float = 30.0', settings)
        self.assertIn('max_automatic_attempts: int = 3', settings)
        self.assertIn('additional_recipient_delay_seconds: float = 0.0', settings)
        for tag in ("#NAME#", "#EMAIL#", "#R5#", "#R11#", "#DATE#", "#DATE-NAME#", "#YAAR#"):
            self.assertIn(tag, dynamic)
        self.assertIn('class WorkerManager', worker)

        # Exact parent/CI evidence and maintenance scope are recorded.
        for text in (release, manifest):
            self.assertIn('32109507918', text)
            self.assertIn('b87b412413f8788656c89b3b97a487d855d10d5f', text)
        self.assertIn('642/642', release)
        self.assertIn('No production behavior is changed', release)
        self.assertTrue(all(line == line.rstrip() for line in prior_manifest_lines))

        project_root = ROOT / "project"
        if project_root.is_dir():
            root_cause = (project_root / "research" / "ROOT_CAUSE_VERIFICATION_v1.0.0.1.50.1.md").read_text(encoding="utf-8")
            freeze = (project_root / "specifications" / "BASELINE_FREEZE_v1.0.0.1.50.1.md").read_text(encoding="utf-8")
            self.assertIn('32109507918', root_cause)
            self.assertIn('release-readiness', freeze.lower())
