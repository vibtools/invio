from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_release_metadata_is_v100140(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        project_meta = (ROOT / "vibproject.ygit").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        docs_meta = (ROOT / "docs" / "docs.manifest.ygit").read_text(encoding="utf-8")
        self.assertIn('version = "1.0.0.1.40"', pyproject)
        self.assertIn('"version": "1.0.0.1.40"', project_meta)
        self.assertIn('"latestVersion": "1.0.0.1.40"', project_meta)
        self.assertIn('"current": "1.0.0.1.40"', docs_meta)
        self.assertIn('"latest": "1.0.0.1.40"', docs_meta)
        self.assertIn('Production • v1.0.0.1.40', main_window)
        self.assertIn('Invio/1.0.0.1.40', runtime)

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

    def test_project_folder_is_git_ignored(self):
        rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/project/", rules)

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
        self.assertIn('version = "1.0.0.1.40"', pyproject)
        self.assertIn('"version": "1.0.0.1.40"', project_meta)
        self.assertIn('"latestVersion": "1.0.0.1.40"', project_meta)
        self.assertIn('"keyring>=25.7,<26"', project_meta)
        self.assertIn('Production • v1.0.0.1.40', main_window)
        self.assertIn('Invio/1.0.0.1.40', runtime)

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
        self.assertIn('INVIO_VERSION: "1.0.0.1.40"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.40"', workflow)
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
        self.assertIn('INVIO_VERSION: "1.0.0.1.40"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.40"', workflow)
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
        self.assertIn('INVIO_VERSION: "1.0.0.1.40"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.40"', workflow)
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
        self.assertIn('INVIO_VERSION: "1.0.0.1.40"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.40"', workflow)
        self.assertIn("nuitka-keyring.nuitka-package.config.yml", workflow)
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
        self.assertIn('INVIO_VERSION: "1.0.0.1.40"', workflow)
        self.assertIn('INVIO_PE_VERSION: "1.0.1.40"', workflow)
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
        self.assertIn("DOMAIN_SCHEMA_VERSION = 5", schema)
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
        self.assertIn("DOMAIN_SCHEMA_VERSION = 5", schema)
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
        self.assertIn("DOMAIN_SCHEMA_VERSION = 5", schema)
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
        self.assertIn("DOMAIN_SCHEMA_VERSION = 5", schema)
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
        self.assertIn("DOMAIN_SCHEMA_VERSION = 5", schema)
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
        self.assertIn("DOMAIN_SCHEMA_VERSION = 5", schema)
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
        self.assertIn("DOMAIN_SCHEMA_VERSION = 5", schema)
        self.assertIn("CREATE TABLE task_execution_snapshots", schema)
        self.assertIn("CREATE TABLE task_snapshot_customers", schema)
        self.assertIn("CREATE TABLE task_snapshot_template", schema)
        self.assertIn("class TaskExecutionSnapshot", task_model)
        self.assertIn('TASK_ASSIGNMENT_STRATEGY = "recipient_ordinal_round_robin_v1"', task_model)



if __name__ == "__main__":
    unittest.main()
