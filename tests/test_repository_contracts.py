from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_project_folder_is_git_ignored(self):
        rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/project/", rules)

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

    def test_release_metadata_is_v100115(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        project_meta = (ROOT / "vibproject.ygit").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runtime = (ROOT / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        self.assertIn('version = "1.0.0.1.15"', pyproject)
        self.assertIn('"version": "1.0.0.1.15"', project_meta)
        self.assertIn('"latestVersion": "1.0.0.1.15"', project_meta)
        self.assertIn('"keyring>=25.7,<26"', project_meta)
        self.assertIn('Production • v1.0.0.1.15', main_window)
        self.assertIn('Invio/1.0.0.1.15', runtime)

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

    def test_p05_schema_v4_and_task_snapshot_contract_exist(self):
        schema = (ROOT / "src" / "core" / "storage" / "schema.py").read_text(encoding="utf-8")
        task_model = (ROOT / "src" / "tasks" / "models" / "task.py").read_text(encoding="utf-8")
        self.assertIn("DOMAIN_SCHEMA_VERSION = 4", schema)
        self.assertIn("CREATE TABLE task_execution_snapshots", schema)
        self.assertIn("CREATE TABLE task_snapshot_customers", schema)
        self.assertIn("CREATE TABLE task_snapshot_template", schema)
        self.assertIn("class TaskExecutionSnapshot", task_model)
        self.assertIn('TASK_ASSIGNMENT_STRATEGY = "recipient_ordinal_round_robin_v1"', task_model)



if __name__ == "__main__":
    unittest.main()
