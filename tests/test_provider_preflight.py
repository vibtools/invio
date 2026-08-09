from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from src.accounts.models import Account
from src.core.provider_manager import ProviderManager, ProviderManifest, ProviderManifestError
from src.core.provider_runtime import (
    CANONICAL_REFRENS_BASE_URL,
    ProviderRuntime,
    ProviderRuntimeError,
    canonical_refrens_base_url,
    effective_capabilities,
    executable_capabilities,
    manifest_runtime_contract_matches,
    preflight_candidate,
    preflight_task,
)
from src.customers.models import CustomerRecord
from src.invoices.templates import InvoiceItemTemplate, InvoiceTemplate
from src.tasks.models import Task, TaskExecutionSnapshot

ROOT = Path(__file__).resolve().parents[1]


def verified_account(provider_id: str, provider_name: str, *, mode: str, credentials: dict[str, str]) -> Account:
    return Account(
        id=f"acct_{provider_id}",
        provider_id=provider_id,
        provider_name=provider_name,
        name="Primary",
        mode=mode,
        status="Verified",
        credentials=credentials,
        last_verification_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        verification_error_summary="",
    )


def invoice_template(**changes) -> InvoiceTemplate:
    values = dict(
        id="tpl_1",
        name="Standard",
        currency="USD",
        days_until_due=7,
        memo="Memo",
        footer="Footer",
        automatic_tax=False,
        reuse_customer=True,
        items=[InvoiceItemTemplate("Service", Decimal("1"), Decimal("10"), Decimal("0"))],
        invoice_title="Invoice",
        invoice_subtitle="",
        invoice_type="INVOICE",
        customer_note="Note",
        terms=["Pay in 7 days"],
    )
    values.update(changes)
    return InvoiceTemplate(**values)


class ProviderPreflightTests(unittest.TestCase):
    def setUp(self):
        self.manager = ProviderManager(ROOT)
        self.stripe = self.manager.get_packaged("stripe")
        self.refrens = self.manager.get_packaged("refrens")
        self.assertIsNotNone(self.stripe)
        self.assertIsNotNone(self.refrens)

    def stripe_account(self) -> Account:
        return verified_account(
            "stripe",
            "Stripe",
            mode="Test",
            credentials={"secret_key": "sk_test_valid_for_contract"},
        )

    def refrens_account(self, base_url: str = CANONICAL_REFRENS_BASE_URL) -> Account:
        return verified_account(
            "refrens",
            "Refrens",
            mode="Default",
            credentials={
                "base_url": base_url,
                "url_key": "biz",
                "app_id": "app",
                "app_secret": "secret",
            },
        )

    def test_builtin_runtime_capabilities_reconcile_with_manifests(self):
        assert self.stripe is not None and self.refrens is not None
        self.assertEqual(executable_capabilities("stripe"), ("invoice", "send_invoice", "api_test"))
        self.assertEqual(effective_capabilities(self.stripe), ("invoice", "send_invoice", "api_test"))
        self.assertEqual(executable_capabilities("refrens"), ("api_test",))
        self.assertEqual(effective_capabilities(self.refrens), ("api_test",))

    def test_packaged_manifest_contract_ignores_display_fields_but_not_execution_fields(self):
        assert self.stripe is not None
        display_only = ProviderManifest(
            id=self.stripe.id,
            name="Different Display Name",
            version="999",
            description="Different description",
            credential_fields=self.stripe.credential_fields,
            account_modes=self.stripe.account_modes,
            capabilities=self.stripe.capabilities,
        )
        self.assertTrue(manifest_runtime_contract_matches(display_only, self.stripe))
        conflicting = ProviderManifest(
            id=self.stripe.id,
            name=self.stripe.name,
            version=self.stripe.version,
            description=self.stripe.description,
            credential_fields=self.stripe.credential_fields,
            account_modes=self.stripe.account_modes,
            capabilities=("api_test",),
        )
        self.assertFalse(manifest_runtime_contract_matches(conflicting, self.stripe))

    def test_external_manifest_cannot_claim_packaged_provider_id(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for provider_id in ("stripe", "refrens"):
                package = root / "providers" / "packages" / provider_id
                package.mkdir(parents=True, exist_ok=True)
                (package / "provider.json").write_text(
                    json.dumps({"id": provider_id, "name": provider_id.title(), "version": "1", "description": ""}),
                    encoding="utf-8",
                )
            (root / "providers" / "registry").mkdir(parents=True)
            manager = ProviderManager(root)
            for provider_id, provider_name in (("stripe", "Stripe"), ("refrens", "Refrens")):
                external = root / f"external-{provider_id}.json"
                external.write_text(
                    json.dumps({"id": provider_id, "name": f"Fake {provider_name}", "version": "1", "description": ""}),
                    encoding="utf-8",
                )
                with self.subTest(provider_id=provider_id):
                    with self.assertRaisesRegex(
                        ProviderManifestError,
                        rf"reserved by the packaged {provider_name} integration",
                    ):
                        manager.load_external(external)

    def test_conflicting_installed_builtin_manifest_fails_closed(self):
        assert self.stripe is not None
        conflicting = ProviderManifest(
            id="stripe",
            name="Stripe",
            version="1.0.0",
            description="",
            credential_fields=self.stripe.credential_fields,
            account_modes=self.stripe.account_modes,
            capabilities=("api_test",),
        )
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=conflicting,
            packaged_manifest=self.stripe,
            accounts=(self.stripe_account(),),
            template=invoice_template(),
            customers=(CustomerRecord("a@example.com"),),
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.first_issue.code, "packaged-manifest-runtime-mismatch")

    def test_valid_stripe_candidate_passes_without_network(self):
        assert self.stripe is not None
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=self.stripe,
            packaged_manifest=self.stripe,
            accounts=(self.stripe_account(),),
            template=invoice_template(),
            customers=(CustomerRecord("a@example.com"),),
        )
        self.assertTrue(result.passed, result.message)

    def test_stripe_bos_is_blocked(self):
        assert self.stripe is not None
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=self.stripe,
            packaged_manifest=self.stripe,
            accounts=(self.stripe_account(),),
            template=invoice_template(invoice_type="BOS"),
            customers=(CustomerRecord("a@example.com"),),
        )
        self.assertIn("invoice-type-unsupported", [issue.code for issue in result.issues])
        self.assertIn("Select Invoice instead of Bill of Supply", result.message)

    def test_stripe_automatic_tax_is_blocked_by_current_customer_contract(self):
        assert self.stripe is not None
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=self.stripe,
            packaged_manifest=self.stripe,
            accounts=(self.stripe_account(),),
            template=invoice_template(automatic_tax=True),
            customers=(CustomerRecord("a@example.com", country="US"),),
        )
        self.assertIn("automatic-tax-unsupported", [issue.code for issue in result.issues])

    def test_stripe_nonzero_line_tax_is_blocked(self):
        assert self.stripe is not None
        template = invoice_template()
        template.items[0].tax_rate = Decimal("5")
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=self.stripe,
            packaged_manifest=self.stripe,
            accounts=(self.stripe_account(),),
            template=template,
            customers=(CustomerRecord("a@example.com"),),
        )
        self.assertIn("line-tax-unsupported", [issue.code for issue in result.issues])

    def test_stripe_unsupported_currency_is_blocked(self):
        assert self.stripe is not None
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=self.stripe,
            packaged_manifest=self.stripe,
            accounts=(self.stripe_account(),),
            template=invoice_template(currency="ZZZ"),
            customers=(CustomerRecord("a@example.com"),),
        )
        self.assertIn("currency-unsupported", [issue.code for issue in result.issues])

    def test_provider_installation_is_required_before_candidate_execution(self):
        assert self.stripe is not None
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=None,
            packaged_manifest=self.stripe,
            accounts=(self.stripe_account(),),
            template=invoice_template(),
            customers=(CustomerRecord("a@example.com"),),
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.first_issue.code, "provider-not-installed")

    def test_account_status_mode_and_required_credentials_fail_closed(self):
        assert self.stripe is not None
        account = self.stripe_account()
        account.status = "Not Verified"
        account.mode = "Unsupported"
        account.credentials = {"secret_key": ""}
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=self.stripe,
            packaged_manifest=self.stripe,
            accounts=(account,),
            template=invoice_template(),
            customers=(CustomerRecord("a@example.com"),),
        )
        codes = [issue.code for issue in result.issues]
        self.assertIn("account-not-verified", codes)
        self.assertIn("account-mode-unsupported", codes)
        self.assertIn("account-credential-missing", codes)

    def test_account_health_requires_verified_timestamp_and_no_error(self):
        assert self.stripe is not None
        account = self.stripe_account()
        account.last_verification_at = ""
        account.verification_error_summary = "old failure"
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=self.stripe,
            packaged_manifest=self.stripe,
            accounts=(account,),
            template=invoice_template(),
            customers=(CustomerRecord("a@example.com"),),
        )
        codes = [issue.code for issue in result.issues]
        self.assertIn("account-verification-health-incomplete", codes)
        self.assertIn("account-verification-error", codes)

    def test_invalid_verification_timestamp_is_not_accepted_as_health(self):
        assert self.stripe is not None
        account = self.stripe_account()
        account.last_verification_at = "not-a-timestamp"
        result = preflight_candidate(
            provider_id="stripe",
            installed_manifest=self.stripe,
            packaged_manifest=self.stripe,
            accounts=(account,),
            template=invoice_template(),
            customers=(CustomerRecord("a@example.com"),),
        )
        self.assertIn("account-verification-health-incomplete", [issue.code for issue in result.issues])

    def test_builtin_stripe_runner_rechecks_static_preflight_before_network(self):
        from src.core.state import AppState

        calls = []
        state = AppState()
        account = state.add_account(
            "stripe",
            "Stripe",
            "Primary",
            "Test",
            {"secret_key": "sk_test_valid_for_contract"},
            status="Verified",
            last_verification_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, ["a@example.com"])
        template = state.save_invoice_template(
            template_id=None,
            name="BOS",
            currency="USD",
            days_until_due=7,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "1", "10", "0")],
            invoice_type="BOS",
        )
        task = state.create_task("stripe", "Stripe", [account.id], customer_list.id, template.id)
        runtime = ProviderRuntime(transport=lambda *args: calls.append(args) or {})
        with self.assertRaisesRegex(ProviderRuntimeError, r"Bill of Supply"):
            runtime.make_task_runner(task, state)
        self.assertEqual(calls, [])

    def test_refrens_required_customer_data_is_reported_without_guessing(self):
        assert self.refrens is not None
        result = preflight_candidate(
            provider_id="refrens",
            installed_manifest=self.refrens,
            packaged_manifest=self.refrens,
            accounts=(self.refrens_account(),),
            template=invoice_template(invoice_type="BOS", reuse_customer=False),
            customers=(CustomerRecord("a@example.com"),),
        )
        codes = [issue.code for issue in result.issues]
        self.assertEqual(codes[0], "task-runtime-unavailable")
        self.assertIn("customer-data-missing", codes)
        customer_issue = next(issue for issue in result.issues if issue.code == "customer-data-missing")
        self.assertIn("name, country", customer_issue.message)
        self.assertIn("will not guess", customer_issue.correction)

    def test_refrens_task_capability_remains_disabled_until_p11(self):
        assert self.refrens is not None
        result = preflight_candidate(
            provider_id="refrens",
            installed_manifest=self.refrens,
            packaged_manifest=self.refrens,
            accounts=(self.refrens_account(),),
            template=invoice_template(reuse_customer=False),
            customers=(CustomerRecord("a@example.com", "Alice", "BD"),),
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.first_issue.code, "task-runtime-unavailable")
        self.assertIn("P11", result.message)

    def test_refrens_endpoint_trust_accepts_only_canonical_contract(self):
        accepted = (
            "https://api.refrens.com",
            "https://api.refrens.com/",
            "https://api.refrens.com:443",
        )
        for value in accepted:
            with self.subTest(value=value):
                self.assertEqual(canonical_refrens_base_url(value), CANONICAL_REFRENS_BASE_URL)
        rejected = (
            "http://api.refrens.com",
            "https://api.refrens.com.evil.example",
            "https://evil.example",
            "https://user:pass@api.refrens.com",
            "https://api.refrens.com/custom/path",
            "https://api.refrens.com?redirect=x",
            "https://api.refrens.com#fragment",
            "https://api.refrens.com:444",
        )
        for value in rejected:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    canonical_refrens_base_url(value)

    def test_refrens_untrusted_endpoint_is_rejected_before_transport(self):
        calls = []
        runtime = ProviderRuntime(transport=lambda *args: calls.append(args) or {"accessToken": "token"})
        with self.assertRaisesRegex(ProviderRuntimeError, r"exactly https://api.refrens.com"):
            runtime.test_account(
                "refrens",
                {
                    "base_url": "https://api.refrens.com.evil.example",
                    "url_key": "biz",
                    "app_id": "app",
                    "app_secret": "secret",
                },
                mode="Default",
            )
        self.assertEqual(calls, [])

    def test_task_preflight_uses_frozen_snapshot_not_live_inputs(self):
        assert self.stripe is not None
        account = self.stripe_account()
        snapshot = TaskExecutionSnapshot.capture(
            provider_id="stripe",
            account_ids=[account.id],
            customers=[CustomerRecord("frozen@example.com")],
            template=invoice_template(),
        )
        task = Task(
            id="task_1",
            name="Task 1",
            provider_id="stripe",
            provider_name="Stripe",
            account_ids=[account.id],
            customer_list_id="list_1",
            customer_list_name="Customers",
            invoice_template_id="tpl_1",
            invoice_template_name="Standard",
            total=1,
            execution_snapshot=snapshot,
        )
        result = preflight_task(
            task=task,
            installed_manifest=self.stripe,
            packaged_manifest=self.stripe,
            accounts=(account,),
        )
        self.assertTrue(result.passed, result.message)

    def test_external_registered_runner_keeps_existing_generic_runtime_boundary(self):
        manifest = ProviderManifest(
            id="external_provider",
            name="External",
            version="1",
            description="",
            credential_fields=(),
            account_modes=(),
            capabilities=("invoice",),
        )
        account = verified_account("external_provider", "External", mode="Default", credentials={})
        result = preflight_candidate(
            provider_id=manifest.id,
            installed_manifest=manifest,
            packaged_manifest=None,
            accounts=(account,),
            template=invoice_template(),
            customers=(CustomerRecord("a@example.com"),),
            injected_runner_available=True,
        )
        self.assertTrue(result.passed, result.message)


if __name__ == "__main__":
    unittest.main()
