from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.accounts.models import Account
from src.core.provider_manager import ProviderManager, ProviderManifest
from src.core.provider_runtime import (
    ProviderRuntime,
    ProviderRuntimeError,
    effective_capabilities,
    executable_capabilities,
    manifest_runtime_contract_matches,
    provider_adapter_contract,
    registered_provider_ids,
)
from src.core.state import AppState

ROOT = Path(__file__).resolve().parents[1]


class ProviderAdapterRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = ProviderManager(ROOT)

    def test_builtin_provider_contracts_are_registry_driven(self):
        self.assertEqual(registered_provider_ids(), ("stripe", "refrens", "agiled"))
        stripe = provider_adapter_contract("stripe")
        refrens = provider_adapter_contract("refrens")
        agiled = provider_adapter_contract("agiled")
        self.assertIsNotNone(stripe)
        self.assertIsNotNone(refrens)
        self.assertIsNotNone(agiled)
        assert stripe is not None and refrens is not None and agiled is not None
        self.assertEqual(stripe.api_test_handler, "_test_stripe_account")
        self.assertEqual(stripe.task_batch_handler, "_run_stripe_batch")
        self.assertEqual(refrens.api_test_handler, "_test_refrens_account")
        self.assertEqual(refrens.task_batch_handler, "_run_refrens_batch")
        self.assertEqual(agiled.api_test_handler, "_test_agiled_account")
        self.assertIsNone(agiled.task_batch_handler)

    def test_agiled_packaged_manifest_matches_registered_runtime_contract(self):
        packaged = self.manager.get_packaged("agiled")
        self.assertIsNotNone(packaged)
        assert packaged is not None
        self.assertEqual(packaged.name, "Agiled")
        self.assertEqual(packaged.account_modes, ("Default",))
        self.assertEqual(tuple(field.key for field in packaged.credential_fields), ("api_key",))
        self.assertEqual(packaged.capabilities, ("invoice", "send_invoice", "api_test"))
        self.assertTrue(manifest_runtime_contract_matches(packaged, packaged))

    def test_agiled_manifest_drift_is_rejected_fail_closed(self):
        packaged = self.manager.get_packaged("agiled")
        assert packaged is not None
        drifted = ProviderManifest(
            id="agiled",
            name="Agiled",
            version="1.0.0",
            description="",
            credential_fields=(),
            account_modes=packaged.account_modes,
            capabilities=packaged.capabilities,
        )
        self.assertFalse(manifest_runtime_contract_matches(drifted, drifted))

    def test_agiled_reports_only_verified_api_test_as_executable(self):
        packaged = self.manager.get_packaged("agiled")
        assert packaged is not None
        self.assertEqual(executable_capabilities("agiled"), ("api_test",))
        self.assertEqual(effective_capabilities(packaged), ("api_test",))

    def test_agiled_api_test_uses_exact_current_bearer_safe_read(self):
        calls: list[tuple] = []
        runtime = ProviderRuntime(transport=lambda *args: calls.append(args) or {"data": {"token_id": "tok"}})
        self.assertTrue(runtime.supports_api_test("agiled"))
        message = runtime.test_account("agiled", {"api_key": "agiled-secret-key"}, mode="Default")
        self.assertEqual(message, "Agiled API connection verified.")
        self.assertEqual(len(calls), 1)
        method, url, headers, body, _timeout = calls[0]
        self.assertEqual(method, "GET")
        self.assertEqual(url, "https://api.agiled.ai/public/v1/me")
        self.assertEqual(headers["Authorization"], "Bearer agiled-secret-key")
        self.assertEqual(headers["Accept"], "application/json")
        self.assertIsNone(body)

    def test_agiled_package_install_uninstall_round_trip_uses_manifest_only(self):
        source_manifest = ROOT / "providers" / "packages" / "agiled" / "provider.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            package_dir = project_root / "providers" / "packages" / "agiled"
            package_dir.mkdir(parents=True)
            (project_root / "providers" / "registry").mkdir(parents=True)
            package_dir.joinpath("provider.json").write_text(
                source_manifest.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            manager = ProviderManager(project_root)
            self.assertEqual([item.id for item in manager.list_available()], ["agiled"])
            self.assertEqual(manager.installed_ids(), set())
            installed = manager.install_packaged("agiled")
            self.assertEqual(installed.id, "agiled")
            self.assertEqual(manager.installed_ids(), {"agiled"})
            registry_payload = json.loads(
                (project_root / "providers" / "registry" / "agiled.json").read_text(encoding="utf-8")
            )
            self.assertEqual(registry_payload["credential_fields"][0]["key"], "api_key")
            manager.uninstall("agiled")
            self.assertEqual(manager.installed_ids(), set())
            self.assertTrue(source_manifest.is_file())

    def test_executable_adapter_handler_bindings_resolve_and_agiled_task_stays_disabled(self):
        runtime = ProviderRuntime(transport=lambda *_args, **_kwargs: {})
        for provider_id in ("stripe", "refrens", "agiled"):
            adapter = provider_adapter_contract(provider_id)
            self.assertIsNotNone(adapter)
            assert adapter is not None and adapter.api_test_handler is not None
            self.assertTrue(callable(getattr(runtime, adapter.api_test_handler, None)))
        for provider_id in ("stripe", "refrens"):
            adapter = provider_adapter_contract(provider_id)
            assert adapter is not None and adapter.task_batch_handler is not None
            self.assertTrue(callable(getattr(runtime, adapter.task_batch_handler, None)))
        refrens = provider_adapter_contract("refrens")
        agiled = provider_adapter_contract("agiled")
        assert refrens is not None and agiled is not None
        self.assertEqual(refrens.task_batch_handler, "_run_refrens_batch")
        self.assertEqual(agiled.api_test_handler, "_test_agiled_account")
        self.assertIsNone(agiled.task_batch_handler)

    def test_agiled_ui_contract_is_generic_manifest_driven_and_api_test_gated(self):
        dialogs = (ROOT / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        providers_page = (ROOT / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        main_window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertIn("for field in provider.credential_fields", dialogs)
        self.assertIn("provider_runtime.supports_api_test(provider.id)", dialogs)
        self.assertIn("This provider cannot become Task-ready because no executable API-test adapter is available.", dialogs)
        self.assertIn("runtime_capabilities(provider)", providers_page)
        self.assertIn("effective_capabilities(provider)", main_window)
        self.assertNotIn('provider.id == "agiled"', dialogs)
        self.assertNotIn('provider.id == "agiled"', providers_page)

    def test_agiled_task_runner_fails_closed_before_any_transport(self):
        calls: list[tuple] = []
        state = AppState()
        account = state.add_account(
            "agiled",
            "Agiled",
            "Primary",
            "Default",
            {"api_key": "agiled-secret-key"},
            status="Verified",
            last_verification_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, ["customer@example.com"])
        template = state.save_invoice_template(
            template_id=None,
            name="Standard",
            currency="USD",
            days_until_due=30,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=False,
            invoice_title="Invoice",
            invoice_subtitle="",
            customer_note="",
            terms=[],
            items=[("Service", "1", "10", "0")],
        )
        task = state.create_task("agiled", "Agiled", [account.id], customer_list.id, template.id)
        runtime = ProviderRuntime(transport=lambda *args: calls.append(args) or {})
        with self.assertRaisesRegex(ProviderRuntimeError, "Agiled Task sending is fail-closed"):
            runtime.make_task_runner(task, state)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
