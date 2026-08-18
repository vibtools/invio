from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.core.dynamic_tags import (
    DYNAMIC_TAGS_VERSION,
    SUPPORTED_DYNAMIC_TAGS,
    DynamicTagContext,
    contains_supported_dynamic_tag,
    render_dynamic_text,
    render_invoice_template,
)
from src.core.provider_runtime.runtime import AccountSnapshot, CustomerSnapshot, ProviderRuntime, TaskSnapshot
from src.core.storage import DomainStore
from src.core.storage.schema import (
    DOMAIN_SCHEMA_VERSION,
    MIGRATION_V1_TO_V2,
    MIGRATION_V2_TO_V3,
    MIGRATION_V3_TO_V4,
    MIGRATION_V4_TO_V5,
    MIGRATION_V5_TO_V6,
    SCHEMA_V1,
)
from src.customers.importers import apply_customer_defaults
from src.customers.models import CustomerList, CustomerRecord
from src.invoices.templates import InvoiceItemTemplate, InvoiceTemplate
from src.tasks.models import TaskExecutionSnapshot


REFERENCE_UTC = "2026-08-18T04:00:00Z"


def _template() -> InvoiceTemplate:
    return InvoiceTemplate(
        id="tpl-1",
        name="Literal #EMAIL# template name",
        currency="USD",
        days_until_due=7,
        memo="Memo #NAME# #R5# #UNKNOWN#",
        footer="Footer #EMAIL# #R11#",
        invoice_title="Title #DATE#",
        invoice_subtitle="Subtitle #YAAR#",
        invoice_type="INVOICE",
        customer_note="Note #DATE#",
        terms=["Term #DATE-NAME#", "Year #YAAR#"],
        items=[InvoiceItemTemplate("Item #NAME# #R5#", Decimal("1"), Decimal("10"))],
    )


class DynamicTagRendererTests(unittest.TestCase):
    def test_supported_registry_is_exact_and_unknown_tags_remain_literal(self):
        self.assertEqual(
            SUPPORTED_DYNAMIC_TAGS,
            ("#NAME#", "#EMAIL#", "#R5#", "#R11#", "#DATE#", "#DATE-NAME#", "#YAAR#"),
        )
        context = DynamicTagContext("task-1", "User.Name@Example.com", REFERENCE_UTC)
        rendered = render_dynamic_text("#NAME#|#EMAIL#|#DATE#|#DATE-NAME#|#YAAR#|#UNKNOWN#", context)
        self.assertEqual(
            rendered,
            "user.name|user.name@example.com|August 18, 2026|Tuesday|2026|#UNKNOWN#",
        )

    def test_r5_and_r11_are_fixed_width_and_deterministic_for_task_recipient(self):
        context = DynamicTagContext("task-stable", "person@example.com", REFERENCE_UTC)
        first = render_dynamic_text("#R5#:#R11#:#R5#:#R11#", context)
        second = render_dynamic_text("#R5#:#R11#:#R5#:#R11#", context)
        self.assertEqual(first, second)
        r5a, r11a, r5b, r11b = first.split(":")
        self.assertEqual(r5a, r5b)
        self.assertEqual(r11a, r11b)
        self.assertEqual(len(r5a), 5)
        self.assertEqual(len(r11a), 11)
        self.assertTrue(r5a.isdigit())
        self.assertTrue(r11a.isdigit())
        self.assertGreaterEqual(int(r5a), 10000)
        self.assertLessEqual(int(r5a), 99999)
        self.assertGreaterEqual(int(r11a), 10000000000)
        self.assertLessEqual(int(r11a), 99999999999)

    def test_invoice_renderer_changes_only_approved_target_fields(self):
        template = _template()
        context = DynamicTagContext("task-1", "alpha@example.com", REFERENCE_UTC)
        rendered = render_invoice_template(template, context)

        self.assertEqual(template.memo, "Memo #NAME# #R5# #UNKNOWN#")
        self.assertIn("alpha", rendered.memo)
        self.assertIn("#UNKNOWN#", rendered.memo)
        self.assertEqual(rendered.footer.split()[1], "alpha@example.com")
        self.assertEqual(rendered.customer_note, "Note August 18, 2026")
        self.assertEqual(rendered.terms, ["Term Tuesday", "Year 2026"])
        self.assertTrue(rendered.items[0].description.startswith("Item alpha "))

        # Non-target template fields deliberately remain literal.
        self.assertEqual(rendered.name, "Literal #EMAIL# template name")
        self.assertEqual(rendered.invoice_title, "Title #DATE#")
        self.assertEqual(rendered.invoice_subtitle, "Subtitle #YAAR#")


class DynamicCustomerDefaultTests(unittest.TestCase):
    def test_only_supported_tagged_settings_default_marks_customer_name_dynamic(self):
        explicit = CustomerRecord("person@example.com", "Explicit #NAME#", "GB")
        without_default = apply_customer_defaults([explicit], default_name="", default_country="")
        self.assertEqual(without_default[0].name, "Explicit #NAME#")
        self.assertFalse(without_default[0].name_is_dynamic)

        tagged_default = apply_customer_defaults(
            [explicit], default_name="Customer #NAME# #UNKNOWN#", default_country="US"
        )
        self.assertEqual(tagged_default[0].name, "Customer #NAME# #UNKNOWN#")
        self.assertTrue(tagged_default[0].name_is_dynamic)

        unknown_only = apply_customer_defaults(
            [CustomerRecord("other@example.com")], default_name="Customer #UNKNOWN#", default_country="US"
        )
        self.assertFalse(unknown_only[0].name_is_dynamic)
        self.assertTrue(contains_supported_dynamic_tag("#R5#"))
        self.assertFalse(contains_supported_dynamic_tag("#UNKNOWN#"))


class Phase4ProviderPayloadTests(unittest.TestCase):
    def test_stripe_payload_receives_recipient_rendered_target_fields(self):
        captured: dict[str, dict[str, list[str]]] = {}

        def transport(method, url, _headers, body, _timeout):
            path = urlparse(url).path
            form = parse_qs((body or b"").decode("utf-8"))
            if method == "GET" and path.endswith("/customers"):
                return {"data": []}
            if method == "POST" and path.endswith("/customers"):
                return {"id": "cus_1"}
            if method == "POST" and path.endswith("/invoices"):
                captured["invoice"] = form
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/invoiceitems"):
                captured["item"] = form
                return {"id": "ii_1"}
            if method == "POST" and path.endswith("/finalize"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/send"):
                return {"id": "in_1"}
            raise AssertionError(f"Unexpected Stripe call: {method} {path}")

        snapshot = TaskSnapshot(
            task_id="task-stripe-tags",
            task_name="Task",
            provider_id="stripe",
            accounts=(AccountSnapshot("acct", "Stripe", "Test", {"secret_key": "sk_test_DYNAMIC_TAGS"}),),
            customer_emails=None,
            customers=(CustomerSnapshot("person@example.com", "Client #NAME#", "US", True),),
            template=_template(),
            dynamic_tags_version=DYNAMIC_TAGS_VERSION,
            tag_reference_utc=REFERENCE_UTC,
        )
        runtime = ProviderRuntime(transport=transport, retry_jitter_source=lambda: 0.0)
        runtime._send_stripe_invoice(snapshot, snapshot.accounts[0], "person@example.com", recipient_ordinal=0)

        self.assertIn("Memo person", captured["invoice"]["description"][0])
        self.assertIn("person@example.com", captured["invoice"]["footer"][0])
        self.assertIn("Note August 18, 2026", captured["invoice"]["footer"][0])
        self.assertIn("Term Tuesday", captured["invoice"]["footer"][0])
        self.assertTrue(captured["item"]["description"][0].startswith("Item person "))

    def test_refrens_payload_receives_rendered_name_memo_and_item_description(self):
        snapshot = TaskSnapshot(
            task_id="task-refrens-tags",
            task_name="Task",
            provider_id="refrens",
            accounts=(),
            customer_emails=None,
            customers=(CustomerSnapshot("person@example.com", "Client #NAME#", "US", True),),
            template=_template(),
            dynamic_tags_version=DYNAMIC_TAGS_VERSION,
            tag_reference_utc=REFERENCE_UTC,
        )
        customer, template = ProviderRuntime._render_recipient_dynamic_inputs(snapshot, 0)
        payload = ProviderRuntime().build_refrens_invoice_payload(
            template,
            customer_email=customer.email,
            customer_country=customer.country,
            customer_name=customer.name,
        )
        self.assertEqual(payload["billedTo"]["name"], "Client person")
        self.assertIn("Memo person", payload["notes"])
        self.assertTrue(payload["items"][0]["name"].startswith("Item person "))


class Phase4TaskSnapshotTests(unittest.TestCase):
    def test_new_task_snapshot_captures_dynamic_tag_version_and_utc_reference_once(self):
        snapshot = TaskExecutionSnapshot.capture(
            provider_id="stripe",
            account_ids=["acct-1"],
            customers=[CustomerRecord("person@example.com", "Hi #NAME#", "US", True)],
            template=_template(),
        )
        self.assertEqual(snapshot.dynamic_tags_version, DYNAMIC_TAGS_VERSION)
        self.assertTrue(snapshot.tag_reference_utc.endswith("Z"))
        self.assertTrue(snapshot.customers[0].name_is_dynamic)

    def test_runtime_rendering_uses_frozen_reference_and_never_changes_recipient_email(self):
        snapshot = TaskSnapshot(
            task_id="task-1",
            task_name="Task 1",
            provider_id="refrens",
            accounts=(),
            customer_emails=None,
            customers=(CustomerSnapshot("person@example.com", "Client #NAME# #R5#", "US", True),),
            template=_template(),
            dynamic_tags_version=DYNAMIC_TAGS_VERSION,
            tag_reference_utc=REFERENCE_UTC,
        )
        customer1, template1 = ProviderRuntime._render_recipient_dynamic_inputs(snapshot, 0)
        customer2, template2 = ProviderRuntime._render_recipient_dynamic_inputs(snapshot, 0)
        self.assertEqual(customer1.email, "person@example.com")
        self.assertEqual(customer1.name, customer2.name)
        self.assertEqual(template1.memo, template2.memo)
        self.assertEqual(template1.footer, template2.footer)
        self.assertIn("August 18, 2026", template1.customer_note)

    def test_legacy_snapshot_version_zero_keeps_reserved_tokens_literal(self):
        snapshot = TaskSnapshot(
            task_id="legacy-task",
            task_name="Legacy",
            provider_id="refrens",
            accounts=(),
            customer_emails=None,
            customers=(CustomerSnapshot("person@example.com", "#NAME#", "US", True),),
            template=_template(),
            dynamic_tags_version=0,
            tag_reference_utc="",
        )
        customer, template = ProviderRuntime._render_recipient_dynamic_inputs(snapshot, 0)
        self.assertEqual(customer.name, "#NAME#")
        self.assertEqual(template.memo, "Memo #NAME# #R5# #UNKNOWN#")


class Phase4SchemaMigrationTests(unittest.TestCase):
    def test_customer_dynamic_name_provenance_round_trips_through_storage(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "domain.sqlite3"
            store = DomainStore(db_path)
            customer_list = CustomerList(
                id="list-dynamic",
                name="Dynamic",
                customers=[CustomerRecord("person@example.com", "Client #NAME#", "US", True)],
            )
            store.create_customer_list(customer_list)
            store.replace_customer_records(customer_list)
            loaded = store.load(object())
            restored = loaded.customer_lists["list-dynamic"].customers[0]
            self.assertTrue(restored.name_is_dynamic)
            self.assertEqual(restored.name, "Client #NAME#")

    def test_schema_v6_migrates_to_v7_without_activating_tags_in_existing_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "domain.sqlite3"
            with closing(sqlite3.connect(db_path)) as connection:
                connection.executescript(
                    "\n".join(
                        (
                            SCHEMA_V1,
                            MIGRATION_V1_TO_V2,
                            MIGRATION_V2_TO_V3,
                            MIGRATION_V3_TO_V4,
                            MIGRATION_V4_TO_V5,
                            MIGRATION_V5_TO_V6,
                        )
                    )
                )
                connection.execute("PRAGMA user_version = 6")
                connection.execute("INSERT INTO customer_lists (id, name) VALUES ('list-1', 'List')")
                connection.execute(
                    "INSERT INTO customer_emails (list_id, ordinal, email, name, country) VALUES (?, ?, ?, ?, ?)",
                    ("list-1", 0, "old@example.com", "Old #NAME#", "US"),
                )
                connection.execute(
                    "INSERT INTO invoice_templates (id, name, currency, days_until_due, memo, footer, automatic_tax, reuse_customer, invoice_title, invoice_subtitle, invoice_type, customer_note) "
                    "VALUES ('tpl-1','T','USD',7,'','','0','1','Invoice','','INVOICE','')"
                )
                connection.execute(
                    "INSERT INTO tasks (id,name,provider_id,provider_name,customer_list_id,customer_list_name,invoice_template_id,invoice_template_name,status,total,success,failed,processed,last_message) "
                    "VALUES ('task-old','Task','stripe','Stripe','list-1','List','tpl-1','T','Ready',1,0,0,0,'Ready')"
                )
                connection.execute(
                    "INSERT INTO task_execution_snapshots (task_id,snapshot_state,provider_id,assignment_strategy,network_timeout_seconds,max_automatic_attempts,additional_recipient_delay_seconds,rate_limit_per_account) "
                    "VALUES ('task-old','Captured','stripe','recipient_ordinal_round_robin_v1',30,3,0,20)"
                )
                connection.execute(
                    "INSERT INTO task_snapshot_customers (task_id,ordinal,email,name,country) VALUES ('task-old',0,'old@example.com','Old #NAME#','US')"
                )
                connection.execute(
                    "INSERT INTO task_snapshot_template (task_id,template_id,name,currency,days_until_due,memo,footer,automatic_tax,reuse_customer,invoice_title,invoice_subtitle,invoice_type,customer_note) "
                    "VALUES ('task-old','tpl-1','T','USD',7,'#EMAIL#','',0,1,'Invoice','','INVOICE','')"
                )
                connection.execute(
                    "INSERT INTO task_snapshot_template_items (task_id,ordinal,description,quantity,unit_amount,tax_rate) VALUES ('task-old',0,'Item', '1','1','0')"
                )
                connection.commit()

            DomainStore(db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], DOMAIN_SCHEMA_VERSION)
                self.assertEqual(DOMAIN_SCHEMA_VERSION, 7)
                customer = connection.execute(
                    "SELECT name, name_is_dynamic FROM customer_emails WHERE list_id='list-1'"
                ).fetchone()
                snapshot_customer = connection.execute(
                    "SELECT name, name_is_dynamic FROM task_snapshot_customers WHERE task_id='task-old'"
                ).fetchone()
                snapshot = connection.execute(
                    "SELECT dynamic_tags_version, tag_reference_utc FROM task_execution_snapshots WHERE task_id='task-old'"
                ).fetchone()
                self.assertEqual(customer, ("Old #NAME#", 0))
                self.assertEqual(snapshot_customer, ("Old #NAME#", 0))
                self.assertEqual(snapshot, (0, ""))


if __name__ == "__main__":
    unittest.main()
