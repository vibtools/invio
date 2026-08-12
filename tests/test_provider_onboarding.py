from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.core.provider_manager import ProviderManager, ProviderManifestError
from src.core.provider_runtime import (
    IDEMPOTENT_MUTATION,
    NON_IDEMPOTENT_MUTATION,
    ProviderRuntime,
    ProviderRuntimeError,
)


ADAPTER_SOURCE = '''from src.core.provider_runtime import (\n    ExternalOnboardingResult, ExternalRecipientResult,\n    NON_IDEMPOTENT_MUTATION, ProviderCapabilityProfile, ProviderOnboardingProfile, SAFE_READ\n)\nclass Adapter:\n    interface_version=1\n    provider_id="onboarding_demo"\n    adapter_version="1.2.0"\n    scheduling_policy=None\n    profile=ProviderCapabilityProfile(provider_id="onboarding_demo", executable_capabilities=frozenset({"invoice","send_invoice","api_test"}), task_execution_enabled=True, task_unavailable_message="", invoice_types=frozenset({"INVOICE"}), currencies=None, supports_automatic_tax=False, supports_line_tax=False, supports_customer_reuse=False, supports_memo=True, supports_footer=True, supports_customer_note=True, supports_terms=True, required_customer_fields=("email",))\n    onboarding_profile=ProviderOnboardingProfile(button_label="Prepare Demo", auto_verify=True)\n    def prepare_account(self, context):\n        data=context.request(stage="discover", operation_kind=SAFE_READ, method="GET", url="https://api.example/discover")\n        created=context.request(stage="bootstrap", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST", url="https://api.example/bootstrap", json_data={"name":"Invio Service"})\n        return ExternalOnboardingResult(credential_updates={"tenant_id": data["tenant_id"], "managed_id": created["id"]}, message="Prepared", account_label="Demo Company")\n    def test_account(self, context):\n        context.request(stage="health", operation_kind=SAFE_READ, method="GET", url="https://api.example/health")\n        return "ok"\n    def validate_task(self, context): return ()\n    def execute_recipient(self, context): return ExternalRecipientResult(final_stage="done")\ndef create_adapter(): return Adapter()\n'''


class ProviderEasyOnboardingHostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "providers" / "packages").mkdir(parents=True)
        (self.root / "providers" / "registry").mkdir(parents=True)

    def _bundle(self) -> Path:
        bundle = self.root / "bundle"
        bundle.mkdir(exist_ok=True)
        (bundle / "provider.json").write_text(json.dumps({
            "id": "onboarding_demo",
            "name": "Onboarding Demo",
            "version": "1.2.0",
            "description": "Easy onboarding host contract test",
            "credential_fields": [
                {"key": "client_id", "label": "Client ID", "kind": "text", "required": True, "ownership": "user_required"},
                {"key": "refresh_token", "label": "Refresh Token", "kind": "password", "required": True, "ownership": "generated"},
                {"key": "tenant_id", "label": "Tenant", "kind": "text", "required": True, "ownership": "discovered"},
                {"key": "managed_id", "label": "Managed ID", "kind": "text", "required": True, "ownership": "managed"},
            ],
            "account_modes": ["Default"],
            "capabilities": ["invoice", "send_invoice", "api_test"],
            "runtime_adapter": {"interface_version": 1, "adapter_version": "1.2.0", "entrypoint": "create_adapter"},
            "onboarding": {"interface_version": 1},
        }), encoding="utf-8")
        (bundle / "adapter.py").write_text(ADAPTER_SOURCE, encoding="utf-8")
        return bundle / "provider.json"

    @staticmethod
    def _transport(method, url, headers, body, timeout):
        del headers, body, timeout
        if method == "GET" and url == "https://api.example/discover": return {"tenant_id": "tenant-1"}
        if method == "POST" and url == "https://api.example/bootstrap": return {"id": "managed-1"}
        if method == "GET" and url == "https://api.example/health": return {"ok": True}
        raise AssertionError((method, url))

    def _runtime(self):
        runtime = ProviderRuntime(project_root=self.root, transport=self._transport)
        manager = ProviderManager(self.root)
        manager.load_external(self._bundle(), allow_executable=True, adapter_validator=runtime.validate_external_adapter)
        runtime.reload_external_adapters()
        return manager, runtime

    def test_manifest_ownership_defaults_legacy_to_user_required(self):
        path = self._bundle()
        raw = json.loads(path.read_text())
        raw["credential_fields"][0].pop("ownership")
        path.write_text(json.dumps(raw), encoding="utf-8")
        manifest = ProviderManager(self.root).inspect_manifest(path)
        self.assertEqual(manifest.credential_fields[0].ownership, "user_required")
        self.assertTrue(manifest.credential_fields[0].quick_connect_visible)
        self.assertFalse(manifest.credential_fields[1].quick_connect_visible)


    def test_manifest_choice_field_preserves_friendly_label_and_machine_value(self):
        path = self._bundle()
        raw = json.loads(path.read_text())
        raw["credential_fields"][0]["choices"] = [
            {"label": "Global", "value": "https://accounts.example.com"},
            {"label": "Europe", "value": "https://accounts.example.eu"},
        ]
        path.write_text(json.dumps(raw), encoding="utf-8")
        manifest = ProviderManager(self.root).inspect_manifest(path)
        self.assertEqual(
            [(choice.label, choice.value) for choice in manifest.credential_fields[0].choices],
            [("Global", "https://accounts.example.com"), ("Europe", "https://accounts.example.eu")],
        )

    def test_manifest_rejects_unknown_ownership(self):
        path = self._bundle()
        raw = json.loads(path.read_text())
        raw["credential_fields"][0]["ownership"] = "mystery"
        path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ProviderManifestError, "ownership"):
            ProviderManager(self.root).inspect_manifest(path)

    def test_manifest_onboarding_requires_runtime(self):
        path = self._bundle()
        raw = json.loads(path.read_text())
        raw.pop("runtime_adapter")
        path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ProviderManifestError, "onboarding requires"):
            ProviderManager(self.root).inspect_manifest(path)

    def test_runtime_prepares_declared_fields_and_supports_non_idempotent_single_attempt(self):
        manager, runtime = self._runtime()
        manifest = manager.get_installed("onboarding_demo")
        self.assertIsNotNone(manifest.onboarding)
        self.assertTrue(runtime.supports_onboarding("onboarding_demo"))
        result = runtime.prepare_external_account("onboarding_demo", {"client_id": "client"}, mode="Default")
        self.assertEqual(result.credential_updates, {"tenant_id": "tenant-1", "managed_id": "managed-1"})
        self.assertEqual(result.account_label, "Demo Company")

    def test_onboarding_mutation_contract_rejects_fake_idempotency(self):
        runtime = ProviderRuntime(project_root=self.root, transport=self._transport)
        with self.assertRaisesRegex(ProviderRuntimeError, "stable provider-supported"):
            runtime._external_onboarding_request(provider_id="demo", stage="mutate", operation_kind=IDEMPOTENT_MUTATION, method="POST", url="https://api.example/mutate")
        with self.assertRaisesRegex(ProviderRuntimeError, "Only IDEMPOTENT_MUTATION"):
            runtime._external_onboarding_request(provider_id="demo", stage="mutate", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST", url="https://api.example/mutate", idempotency_key="fake")

    def test_add_account_quick_connect_source_hides_managed_fields_and_preserves_advanced_fallback(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn('button("Advanced / Manual Setup", "ghost")', source)
        self.assertIn('if onboarding_enabled and not field.quick_connect_visible:', source)
        self.assertIn('group.setVisible(False)', source)
        self.assertIn('group.setVisible(field.quick_connect_visible or self._advanced_credentials_visible)', source)
        self.assertIn('self.provider_runtime.supports_browser_oauth(provider.id)', source)
        self.assertIn('self._supports_onboarding(provider.id)', source)

    def test_add_account_quick_connect_source_chains_authorize_prepare_and_verify(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn('self._pending_onboarding_after_oauth = True', source)
        self.assertIn('QTimer.singleShot(0, self._start_account_onboarding)', source)
        self.assertIn('self._pending_auto_verify_after_onboarding = bool(profile and profile.auto_verify)', source)
        self.assertIn('QTimer.singleShot(0, self._start_api_test)', source)
        self.assertIn('if not self.account_name.text().strip() and result.account_label:', source)

    def test_add_account_onboarding_capability_remains_optional_for_legacy_browser_oauth_runtime(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn('checker = getattr(self.provider_runtime, "supports_onboarding", None)', source)
        self.assertIn('return bool(callable(checker) and checker(provider_id))', source)
        self.assertIn('getter = getattr(self.provider_runtime, "onboarding_profile", None)', source)
        self.assertNotIn('self.provider_runtime.supports_onboarding(provider.id)', source)
        self.assertNotIn('self.provider_runtime.onboarding_profile(provider.id)', source)
        self.assertIn('if onboarding_available:', source)
        self.assertIn('Connect once in your browser; Invio will use the saved refresh token afterward.', source)
        self.assertIn('OAuth connection credentials are stored. Reconnect only if access is revoked.', source)


if __name__ == "__main__":
    unittest.main()
