from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.core.provider_manager import ProviderManager, ProviderManifestError


class ProviderManagerTests(unittest.TestCase):
    def _root(self, td: str) -> Path:
        root = Path(td)
        package = root / "providers" / "packages" / "demo"
        package.mkdir(parents=True)
        (root / "providers" / "registry").mkdir(parents=True)
        (package / "provider.json").write_text(
            json.dumps(
                {
                    "id": "demo",
                    "name": "Demo Provider",
                    "version": "1.0.0",
                    "description": "Demo",
                    "credential_fields": [
                        {"key": "token", "label": "Token", "kind": "password", "required": True}
                    ],
                    "account_modes": ["Test", "Live"],
                    "capabilities": ["invoice"],
                }
            ),
            encoding="utf-8",
        )
        return root

    def test_available_provider_is_not_installed_until_install(self):
        with tempfile.TemporaryDirectory() as td:
            manager = ProviderManager(self._root(td))
            self.assertEqual([item.id for item in manager.list_available()], ["demo"])
            self.assertEqual(manager.list_installed(), [])
            manager.install_packaged("demo")
            self.assertEqual([item.id for item in manager.list_installed()], ["demo"])

    def test_external_manifest_loads_to_registry(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            external = root / "external.json"
            external.write_text(
                json.dumps(
                    {
                        "id": "external_provider",
                        "name": "External",
                        "version": "2.0.0",
                        "description": "External provider",
                        "credential_fields": [],
                    }
                ),
                encoding="utf-8",
            )
            manager = ProviderManager(root)
            provider = manager.load_external(external)
            self.assertEqual(provider.id, "external_provider")
            self.assertTrue((root / "providers" / "registry" / "external_provider.json").exists())

    def test_provider_manifest_error_is_publicly_exported(self):
        self.assertTrue(issubclass(ProviderManifestError, ValueError))


if __name__ == "__main__":
    unittest.main()
