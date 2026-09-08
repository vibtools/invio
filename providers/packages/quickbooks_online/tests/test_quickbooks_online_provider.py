from __future__ import annotations

import importlib.util
import json
import unittest
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

BUNDLE = Path(__file__).resolve().parents[1]


@dataclass
class _Item:
    description: str = "Service"
    quantity: Decimal = Decimal("2")
    unit_amount: Decimal = Decimal("25")
    tax_rate: Decimal = Decimal("0")


@dataclass
class _Template:
    invoice_type: str = "INVOICE"
    invoice_title: str = "Invoice"
    invoice_subtitle: str = ""
    automatic_tax: bool = False
    footer: str = ""
    customer_note: str = ""
    terms: tuple = ()
    items: tuple = (_Item(),)
    currency: str = "USD"
    days_until_due: int = 7
    memo: str = "Thank you"
    reuse_customer: bool = False


@dataclass
class _Customer:
    email: str = "recipient@example.com"
    name: str = "Recipient"


class _Context:
    provider_id = "quickbooks_online"
    task_id = "task-qbo-1"
    account_id = "acc-qbo-1"
    account_name = "QuickBooks Main"
    account_mode = "Sandbox"
    mode = "Sandbox"

    def __init__(self, request):
        self.credentials = {
            "client_id": "CLIENT",
            "client_secret": "SECRET",
            "refresh_token": "REFRESH",
            "realm_id": "1234567890",
            "default_item_id": "10",
        }
        self.customer = _Customer()
        self.template = _Template()
        self.request = request
        self.logs = []
        self.log = self.logs.append


class QuickBooksOnlineProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("invio_qbo_test_adapter", BUNDLE / "adapter.py")
        cls.module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(cls.module)

    def test_manifest_identity_and_official_hosts(self):
        manifest = json.loads((BUNDLE / "provider.json").read_text(encoding="utf-8"))
        adapter = self.module.create_adapter()
        self.assertEqual(manifest["id"], "quickbooks_online")
        self.assertEqual(adapter.provider_id, manifest["id"])
        source = (BUNDLE / "adapter.py").read_text(encoding="utf-8")
        self.assertIn("https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer", source)
        self.assertIn("https://quickbooks.api.intuit.com", source)
        self.assertIn("https://sandbox-quickbooks.api.intuit.com", source)

    def test_api_test_uses_real_company_query_and_item_reads(self):
        calls = []
        def request(**kwargs):
            calls.append(kwargs)
            path = urlsplit(kwargs["url"]).path
            if "/companyinfo/" in path:
                return {"CompanyInfo": {"Id": "1234567890"}}
            if path.endswith("/query"):
                return {"QueryResponse": {"Invoice": []}}
            if path.endswith("/item/10"):
                return {"Item": {"Id": "10", "Active": True}}
            raise AssertionError(kwargs)
        adapter = self.module.create_adapter()
        adapter._access_token = lambda _account: "ACCESS"
        result = adapter.test_account(_Context(request))
        self.assertIn("verified", result.lower())
        self.assertTrue(all(c["operation_kind"] == self.module.SAFE_READ for c in calls))

    def test_real_customer_invoice_and_send_are_requestid_idempotent(self):
        calls = []
        def request(**kwargs):
            calls.append(kwargs)
            parsed = urlsplit(kwargs["url"])
            path = parsed.path
            if path.endswith("/item/10"):
                return {"Item": {"Id": "10", "Active": True}}
            if path.endswith("/preferences"):
                return {"Preferences": {"CurrencyPrefs": {"HomeCurrency": {"value": "USD"}, "MultiCurrencyEnabled": False}}}
            if path.endswith("/customer"):
                return {"Customer": {"Id": "20"}}
            if path.endswith("/invoice"):
                return {"Invoice": {"Id": "30"}}
            if path.endswith("/invoice/30/send"):
                return {"Invoice": {"Id": "30"}}
            raise AssertionError(kwargs)
        adapter = self.module.create_adapter()
        adapter._access_token = lambda _account: "ACCESS"
        result = adapter.execute_recipient(_Context(request))
        self.assertEqual(result.provider_customer_id, "20")
        self.assertEqual(result.provider_invoice_id, "30")
        self.assertEqual(result.final_stage, "external_mutation:invoice_email_send")
        mutations = [c for c in calls if c["operation_kind"] == self.module.IDEMPOTENT_MUTATION]
        self.assertEqual([c["stage"] for c in mutations], ["customer_create", "invoice_create", "invoice_email_send"])
        for call in mutations:
            query = parse_qs(urlsplit(call["url"]).query)
            self.assertIn("requestid", query)
            self.assertEqual(query["requestid"][0], call["idempotency_key"])
        send = mutations[-1]
        self.assertEqual(parse_qs(urlsplit(send["url"]).query)["sendTo"], ["recipient@example.com"])

    def test_validation_fails_closed_for_unmapped_tax_and_terms(self):
        template = _Template()
        template.automatic_tax = True
        template.terms = ("Net 7",)
        template.items = (_Item(tax_rate=Decimal("5")),)
        issues = self.module.create_adapter().validate_task(type("Validation", (), {"template": template})())
        codes = {issue.code for issue in issues}
        self.assertIn("qbo_automatic_tax", codes)
        self.assertIn("qbo_terms", codes)
        self.assertIn("qbo_line_tax", codes)


if __name__ == "__main__":
    unittest.main()
