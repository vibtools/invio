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
            "invoice_templates_page.py",
            "customer_lists_page.py",
            "tasks_page.py",
            "providers_page.py",
            "reports_page.py",
            "logs_page.py",
            "settings_page.py",
        }
        self.assertTrue(required.issubset({path.name for path in page_dir.glob("*.py")}))

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


if __name__ == "__main__":
    unittest.main()
