from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


BUNDLE = Path(__file__).resolve().parents[1]


class _RequestRecorder:
    def __init__(self):
        self.calls = []
        self.contact_exists = True

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        url = kwargs["url"]
        method = kwargs["method"]
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)

        if parsed.path.endswith("/oauth/v2/token"):
            return {"access_token": "ACCESS", "expires_in": 3600, "api_domain": "https://www.zohoapis.com"}
        if "/invoice/v3/organizations/" in parsed.path:
            return {"code": 0, "message": "success", "organization": {"organization_id": "10234695"}}
        if parsed.path.endswith("/invoice/v3/settings/currencies"):
            return {
                "code": 0,
                "message": "success",
                "currencies": [{"currency_id": "9001", "currency_code": "USD", "is_base_currency": True}],
                "page_context": {"has_more_page": False},
            }
        if parsed.path.endswith("/invoice/v3/items") and method == "GET":
            if query.get("name") == ["Service"]:
                return {"code": 0, "message": "success", "items": [{"item_id": "7001", "name": "Service", "status": "active"}]}
            return {"code": 0, "message": "success", "items": []}
        if "/invoice/v3/items/" in parsed.path:
            return {"code": 0, "message": "success", "item": {"item_id": parsed.path.rsplit("/", 1)[-1], "status": "active"}}
        if parsed.path.endswith("/invoice/v3/contacts") and method == "GET":
            if self.contact_exists and query.get("email"):
                return {
                    "code": 0,
                    "message": "success",
                    "contacts": [{
                        "contact_id": "6001",
                        "contact_name": "Customer",
                        "contact_type": "customer",
                        "status": "active",
                        "email": query["email"][0],
                        "currency_id": "9001",
                        "currency_code": "USD",
                    }],
                }
            return {"code": 0, "message": "success", "contacts": []}
        if parsed.path.endswith("/invoice/v3/contacts") and method == "POST":
            return {"code": 0, "message": "created", "contact": {"contact_id": "6002"}}
        if parsed.path.endswith("/invoice/v3/invoices") and method == "GET":
            return {"code": 0, "message": "success", "invoices": []}
        if parsed.path.endswith("/invoice/v3/invoices") and method == "POST":
            return {"code": 0, "message": "created", "invoice": {"invoice_id": "8001"}}
        if parsed.path.endswith("/invoice/v3/invoices/8001/email") and method == "POST":
            return {"code": 0, "message": "Your mail is scheduled to be sent."}
        raise AssertionError((method, url))


@dataclass
class _Item:
    description: str = "Service"
    quantity: Decimal = Decimal("1")
    unit_amount: Decimal = Decimal("10")
    tax_rate: Decimal = Decimal("0")


@dataclass
class _Template:
    invoice_type: str = "INVOICE"
    invoice_title: str = "Invoice"
    invoice_subtitle: str = ""
    automatic_tax: bool = False
    footer: str = ""
    customer_note: str = ""
    items: tuple = (_Item(),)
    currency: str = "USD"
    days_until_due: int = 7
    memo: str = "Memo"
    terms: tuple = ("Net 7",)
    reuse_customer: bool = True


@dataclass
class _Customer:
    email: str = "recipient@example.com"
    name: str = "Recipient"


class _Context:
    provider_id = "zoho_invoice"
    task_id = "task-1"
    account_id = "account-1"
    account_name = "Zoho"
    account_mode = "Default"

    def __init__(self, request):
        self.credentials = {
            "accounts_server_url": "https://accounts.zoho.com",
            "client_id": "1000.CLIENT",
            "client_secret": "SECRET",
            "refresh_token": "1000.REFRESH",
            "organization_id": "10234695",
            "default_item_id": "",
        }
        self.customer = _Customer()
        self.template = _Template()
        self.request = request
        self.logs = []
        self.log = self.logs.append


class ZohoInvoiceProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("invio_zoho_invoice_test_adapter", BUNDLE / "adapter.py")
        cls.module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(cls.module)

    def test_manifest_and_adapter_identity_match(self):
        manifest = json.loads((BUNDLE / "provider.json").read_text(encoding="utf-8"))
        adapter = self.module.create_adapter()
        self.assertEqual(manifest["id"], "zoho_invoice")
        self.assertEqual(adapter.provider_id, manifest["id"])
        self.assertEqual(adapter.adapter_version, manifest["runtime_adapter"]["adapter_version"])
        self.assertEqual(adapter.profile.executable_capabilities, frozenset(manifest["capabilities"]))

    def test_api_test_uses_only_official_zoho_hosts_and_real_books_paths(self):
        recorder = _RequestRecorder()
        context = _Context(recorder)
        result = self.module.create_adapter().test_account(context)
        self.assertIn("verified", result.lower())
        self.assertGreaterEqual(len(recorder.calls), 5)
        for call in recorder.calls:
            host = (urlsplit(call["url"]).hostname or "").lower()
            self.assertIn(host, {"accounts.zoho.com", "www.zohoapis.com"})
            self.assertEqual(call["operation_kind"], self.module.SAFE_READ)

    def test_existing_customer_invoice_create_and_real_email_endpoint(self):
        recorder = _RequestRecorder()
        context = _Context(recorder)
        result = self.module.create_adapter().execute_recipient(context)
        self.assertEqual(result.provider_customer_id, "6001")
        self.assertEqual(result.provider_invoice_id, "8001")
        self.assertEqual(result.final_stage, "external_mutation:invoice_email_send")
        invoice_calls = [c for c in recorder.calls if urlsplit(c["url"]).path.endswith("/invoice/v3/invoices") and c["method"] == "POST"]
        self.assertEqual(len(invoice_calls), 1)
        payload = invoice_calls[0]["json_data"]
        self.assertEqual(payload["customer_id"], "6001")
        self.assertEqual(payload["line_items"][0]["item_id"], "7001")
        self.assertEqual(payload["line_items"][0]["quantity"], 1.0)
        self.assertEqual(payload["line_items"][0]["rate"], 10.0)
        send_calls = [c for c in recorder.calls if urlsplit(c["url"]).path.endswith("/invoice/v3/invoices/8001/email")]
        self.assertEqual(len(send_calls), 1)
        self.assertEqual(send_calls[0]["operation_kind"], self.module.NON_IDEMPOTENT_MUTATION)
        self.assertEqual(send_calls[0]["json_data"], {"to_mail_ids": ["recipient@example.com"]})
        self.assertEqual(parse_qs(urlsplit(send_calls[0]["url"]).query)["send_attachment"], ["true"])

    def test_new_customer_is_created_before_invoice_when_reuse_has_no_match(self):
        recorder = _RequestRecorder()
        recorder.contact_exists = False
        context = _Context(recorder)
        result = self.module.create_adapter().execute_recipient(context)
        self.assertEqual(result.provider_customer_id, "6002")
        mutations = [c["stage"] for c in recorder.calls if c["operation_kind"] == self.module.NON_IDEMPOTENT_MUTATION]
        self.assertEqual(mutations, ["contact_create", "invoice_create", "invoice_email_send"])

    def test_validation_fails_closed_for_unmappable_fields(self):
        adapter = self.module.create_adapter()
        template = _Template()
        template.automatic_tax = True
        template.footer = "footer"
        template.customer_note = "note"
        template.items = (_Item(tax_rate=Decimal("5")),)
        context = type("Validation", (), {"template": template})()
        codes = {issue.code for issue in adapter.validate_task(context)}
        self.assertIn("zoho_invoice_automatic_tax", codes)
        self.assertIn("zoho_invoice_footer", codes)
        self.assertIn("zoho_invoice_customer_note", codes)
        self.assertIn("zoho_invoice_line_tax", codes)


class ZohoInvoiceInvioP13IntegrationTests(unittest.TestCase):
    def test_bundle_installs_and_executes_through_real_invio_external_runtime_contract(self):
        import json as _json
        import shutil
        import tempfile
        import threading
        from datetime import datetime, timezone

        from src.core.provider_manager import ProviderManager
        from src.core.provider_runtime import ProviderRuntime
        from src.core.state import AppState
        from src.core.storage import CredentialStore, DomainStore
        from src.customers.models import CustomerRecord

        class Keyring:
            def __init__(self):
                self.values = {}
            def set_password(self, service_name, username, password):
                self.values[(service_name, username)] = password
            def get_password(self, service_name, username):
                return self.values.get((service_name, username))
            def delete_password(self, service_name, username):
                self.values.pop((service_name, username), None)

        class RunContext:
            def __init__(self, task):
                self.task = task
                self.pause_gate = threading.Event(); self.pause_gate.set()
                self.stop_flag = threading.Event()
                self.logs = []
                self.progress_events = []
            def log(self, message):
                self.logs.append(message)
            def progress(self, processed, success, failed, message):
                self.progress_events.append((processed, success, failed, message))

        calls = []
        def transport(method, url, headers, body, timeout):
            del timeout
            calls.append((method, url, headers, body))
            parsed = urlsplit(url)
            query = parse_qs(parsed.query)
            if parsed.path.endswith('/oauth/v2/token'):
                return {'access_token': 'ACCESS', 'expires_in': 3600, 'api_domain': 'https://www.zohoapis.com'}
            if parsed.path.endswith('/invoice/v3/settings/currencies'):
                return {'code': 0, 'message': 'success', 'currencies': [{'currency_id':'9001','currency_code':'USD'}], 'page_context': {'has_more_page': False}}
            if parsed.path.endswith('/invoice/v3/items') and method == 'GET':
                return {'code': 0, 'message': 'success', 'items': [{'item_id':'7001','name':'Service','status':'active'}]}
            if parsed.path.endswith('/invoice/v3/contacts') and method == 'GET':
                return {'code': 0, 'message': 'success', 'contacts': [{'contact_id':'6001','contact_type':'customer','status':'active','email':'recipient@example.com','currency_id':'9001','currency_code':'USD'}]}
            if parsed.path.endswith('/invoice/v3/invoices') and method == 'POST':
                payload = _json.loads(body.decode('utf-8'))
                self.assertEqual(payload['customer_id'], '6001')
                self.assertEqual(payload['line_items'][0]['item_id'], '7001')
                return {'code': 0, 'message': 'created', 'invoice': {'invoice_id':'8001'}}
            if parsed.path.endswith('/invoice/v3/invoices/8001/email') and method == 'POST':
                payload = _json.loads(body.decode('utf-8'))
                self.assertEqual(payload, {'to_mail_ids':['recipient@example.com']})
                self.assertEqual(query['send_attachment'], ['true'])
                return {'code': 0, 'message': 'scheduled'}
            raise AssertionError((method, url))

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'providers' / 'packages').mkdir(parents=True)
            (root / 'providers' / 'registry').mkdir(parents=True)
            bundle = root / 'bundle'; bundle.mkdir()
            shutil.copy2(BUNDLE / 'provider.json', bundle / 'provider.json')
            shutil.copy2(BUNDLE / 'adapter.py', bundle / 'adapter.py')

            store = DomainStore(root / 'domain.sqlite3')
            credential_store = CredentialStore(Keyring())
            runtime = ProviderRuntime(project_root=root, domain_store=store, transport=transport)
            manager = ProviderManager(root)
            provider = manager.load_external(
                bundle / 'provider.json',
                allow_executable=True,
                adapter_validator=runtime.validate_external_adapter,
            )
            runtime.reload_external_adapters()
            self.assertEqual(provider.id, 'zoho_invoice')
            self.assertEqual(runtime.runtime_capabilities('zoho_invoice'), ('invoice', 'send_invoice', 'api_test'))

            state = AppState(domain_store=store, credential_store=credential_store, loaded=store.load(credential_store))
            account = state.add_account(
                'zoho_invoice', 'Zoho Invoice', 'Zoho Main', 'Default',
                {
                    'accounts_server_url': 'https://accounts.zoho.com',
                    'client_id': '1000.CLIENT',
                    'client_secret': 'SECRET',
                    'refresh_token': '1000.REFRESH',
                    'organization_id': '10234695',
                    'default_item_id': '',
                },
                status='Verified',
                last_verification_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
            )
            customer_list = state.create_customer_list('Zoho Customers')
            state.add_customers(customer_list.id, [CustomerRecord('recipient@example.com', 'Recipient', 'US')])
            template = state.save_invoice_template(
                template_id=None,
                name='Zoho Invoice',
                currency='USD',
                days_until_due=7,
                memo='Memo',
                footer='',
                automatic_tax=False,
                reuse_customer=True,
                items=[('Service', '1', '10', '0')],
            )
            task = state.create_task('zoho_invoice', 'Zoho Invoice', [account.id], customer_list.id, template.id)
            ctx = RunContext(task)
            runner = runtime.make_task_runner(task, state)
            runner(ctx)
            summary = runtime.delivery_summary(task)
            self.assertIsNotNone(summary)
            self.assertEqual(summary.success, 1)
            self.assertEqual(summary.failed, 0)
            self.assertEqual(summary.remaining, 0)
            self.assertTrue(any('/invoice/v3/invoices/8001/email' in url for _m, url, _h, _b in calls))


if __name__ == "__main__":
    unittest.main()
