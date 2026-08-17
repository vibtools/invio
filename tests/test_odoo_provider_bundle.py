from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from src.core.provider_manager import ProviderManager
from src.core.provider_runtime import ExternalAdapterRegistry, SAFE_READ

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "providers" / "plugins" / "odoo"


class OdooProviderBundleTests(unittest.TestCase):
    def test_odoo_bundle_is_shipped_as_external_not_packaged_provider(self):
        manager = ProviderManager(ROOT)
        manifest = manager.inspect_manifest(BUNDLE / "provider.json")
        self.assertEqual(manifest.id, "odoo")
        self.assertEqual(manifest.version, "1.0.0")
        self.assertIsNone(manager.get_packaged("odoo"))
        self.assertIsNotNone(manifest.runtime_adapter)
        self.assertEqual(manifest.runtime_adapter.interface_version, 1)
        self.assertEqual(manifest.runtime_adapter.adapter_version, "1.0.0")
        self.assertEqual(set(manifest.capabilities), {"invoice", "send_invoice", "api_test"})

    def test_odoo_adapter_validates_against_frozen_p13_interface(self):
        manager = ProviderManager(ROOT)
        manifest = manager.inspect_manifest(BUNDLE / "provider.json")
        adapter = ExternalAdapterRegistry.validate_adapter(manifest, BUNDLE / "adapter.py")
        self.assertEqual(adapter.provider_id, "odoo")
        self.assertEqual(adapter.interface_version, 1)
        self.assertEqual(adapter.adapter_version, "1.0.0")
        self.assertTrue(adapter.profile.task_execution_enabled)
        self.assertEqual(
            adapter.profile.executable_capabilities,
            frozenset({"invoice", "send_invoice", "api_test"}),
        )

    def test_odoo_api_test_contract_still_uses_safe_read_jsonrpc_stages(self):
        manager = ProviderManager(ROOT)
        manifest = manager.inspect_manifest(BUNDLE / "provider.json")
        adapter = ExternalAdapterRegistry.validate_adapter(manifest, BUNDLE / "adapter.py")

        class Context:
            credentials = {
                "base_url": "https://applemobileshopnow.odoo.com",
                "database": "demo-db",
                "username": "user@example.com",
                "api_key": "secret",
            }

            def __init__(self):
                self.calls = []

            def request(self, **kwargs):
                self.calls.append(kwargs)
                stage = kwargs["stage"]
                if stage == "authenticate":
                    return {"result": 7}
                if stage == "account_move_access":
                    return {"result": []}
                if stage == "send_wizard_contract":
                    return {
                        "result": {
                            "move_id": {},
                            "sending_methods": {},
                            "sending_method_checkboxes": {},
                            "mail_partner_ids": {},
                        }
                    }
                raise AssertionError(stage)

        context = Context()
        message = adapter.test_account(context)
        self.assertEqual(message, "Odoo API connection verified.")
        self.assertEqual([call["stage"] for call in context.calls], ["authenticate", "account_move_access", "send_wizard_contract"])
        self.assertTrue(all(call["operation_kind"] == SAFE_READ for call in context.calls))
        self.assertTrue(all(call["url"] == "https://applemobileshopnow.odoo.com/jsonrpc" for call in context.calls))

    def test_odoo_bundle_internal_checksums_are_complete(self):
        declared = {}
        for raw in (BUNDLE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            digest, relative = raw.split("  ", 1)
            declared[relative] = digest
        expected = {
            path.relative_to(BUNDLE).as_posix()
            for path in BUNDLE.rglob("*")
            if path.is_file() and path.name != "SHA256SUMS.txt" and "__pycache__" not in path.parts and path.suffix != ".pyc"
        }
        self.assertEqual(set(declared), expected)
        for relative, wanted in declared.items():
            actual = hashlib.sha256((BUNDLE / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, wanted, relative)


if __name__ == "__main__":
    unittest.main()
