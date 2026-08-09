from __future__ import annotations

import unittest

from src.core.state import AppState, StateError
from src.customers.models import CustomerRecord


class AppStateTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.account_a = self.state.add_account("stripe", "Stripe", "A", "Test", {"secret_key": "x"}, status="Verified")
        self.account_b = self.state.add_account("stripe", "Stripe", "B", "Test", {"secret_key": "y"}, status="Verified")
        self.account_other = self.state.add_account("other", "Other", "C", "Test", {"token": "z"}, status="Verified")
        self.customer_list = self.state.create_customer_list("List 1")
        self.state.add_emails(self.customer_list.id, ["a@example.com", "b@example.com"])
        self.template = self.state.save_invoice_template(
            template_id=None,
            name="Default",
            currency="usd",
            days_until_due=30,
            memo="Memo",
            footer="Footer",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "1", "10.00")],
        )

    def create_task(self, account_ids: list[str] | None = None):
        return self.state.create_task(
            "stripe",
            "Stripe",
            account_ids or [self.account_a.id],
            self.customer_list.id,
            self.template.id,
        )

    def test_unverified_account_cannot_create_task(self):
        unverified = self.state.add_account(
            "stripe", "Stripe", "Pending", "Test", {"secret_key": "sk_test_pending"}, status="Not Verified"
        )
        with self.assertRaisesRegex(StateError, "not verified"):
            self.create_task([unverified.id])

    def test_reserved_account_cannot_be_edited_or_deleted(self):
        task = self.create_task()
        with self.assertRaisesRegex(StateError, "Close that task before editing"):
            self.state.update_account(
                self.account_a.id, name="Changed", mode="Test", credentials={"secret_key": "new"},
                status="Verified", last_verification_at="2026-08-09T02:00:00+00:00"
            )
        with self.assertRaisesRegex(StateError, "Close that task before deleting"):
            self.state.delete_account(self.account_a.id)
        self.assertIn(task.id, self.state.tasks)

    def test_unreserved_account_edit_requires_verified_candidate(self):
        with self.assertRaisesRegex(StateError, "successful API Test"):
            self.state.update_account(
                self.account_b.id, name="Changed", mode="Test", credentials={"secret_key": "new"},
                status="Not Verified", last_verification_at="2026-08-09T02:00:00+00:00"
            )
        updated = self.state.update_account(
            self.account_b.id, name="Changed", mode="Live", credentials={"secret_key": "new"},
            status="Verified", last_verification_at="2026-08-09T02:01:00+00:00"
        )
        self.assertEqual(updated.provider_id, "stripe")
        self.assertEqual(updated.name, "Changed")
        self.assertEqual(updated.mode, "Live")
        self.assertEqual(updated.last_verification_at, "2026-08-09T02:01:00+00:00")

    def test_retest_failure_marks_account_unverified_and_blocks_task_creation(self):
        self.state.record_account_verification(
            self.account_b.id, verified=False, last_verification_at="2026-08-09T02:02:00+00:00",
            error_summary="Credential rejected."
        )
        self.assertEqual(self.account_b.status, "Not Verified")
        self.assertEqual(self.account_b.verification_error_summary, "Credential rejected.")
        with self.assertRaisesRegex(StateError, "not verified"):
            self.create_task([self.account_b.id])

    def test_verification_error_summary_redacts_current_account_secrets(self):
        self.account_b.credentials = {"secret_key": "super-secret-value"}
        self.state.record_account_verification(
            self.account_b.id, verified=False, last_verification_at="2026-08-09T02:03:00+00:00",
            error_summary="Provider rejected super-secret-value."
        )
        self.assertNotIn("super-secret-value", self.account_b.verification_error_summary)
        self.assertIn("***REDACTED***", self.account_b.verification_error_summary)

    def test_unreserved_account_delete_removes_account(self):
        account_id = self.account_b.id
        self.state.delete_account(account_id)
        self.assertNotIn(account_id, self.state.accounts)

    def test_accounts_are_filtered_by_provider(self):
        ids = {item.id for item in self.state.accounts_for_provider("stripe")}
        self.assertEqual(ids, {self.account_a.id, self.account_b.id})

    def test_account_cannot_be_reserved_by_two_tasks(self):
        first = self.create_task()
        with self.assertRaises(StateError):
            self.create_task()
        self.state.close_task(first.id)
        second = self.create_task()
        self.assertIn(second.id, self.state.tasks)

    def test_mixed_provider_accounts_are_rejected(self):
        with self.assertRaises(StateError):
            self.create_task([self.account_a.id, self.account_other.id])

    def test_customer_list_deduplicates_emails(self):
        added = self.state.add_emails(self.customer_list.id, ["A@example.com", "c@example.com"])
        self.assertEqual(added, 1)
        self.assertEqual(self.customer_list.count, 3)


    def test_customer_records_preserve_email_only_compatibility_and_explicit_metadata(self):
        self.assertEqual(self.customer_list.emails, ["a@example.com", "b@example.com"])
        result = self.state.add_customers(
            self.customer_list.id,
            [CustomerRecord("c@example.com", "Customer C", "bd")],
        )
        self.assertEqual(result.added, 1)
        record = self.customer_list.customers[-1]
        self.assertEqual((record.email, record.name, record.country), ("c@example.com", "Customer C", "BD"))

    def test_existing_email_only_record_can_be_enriched_without_silent_overwrite(self):
        first = self.state.add_customers(
            self.customer_list.id,
            [CustomerRecord("a@example.com", "Alice", "US")],
        )
        self.assertEqual(first.enriched, 1)
        second = self.state.add_customers(
            self.customer_list.id,
            [CustomerRecord("a@example.com", "Alicia", "GB")],
        )
        self.assertEqual(second.enriched, 0)
        self.assertEqual(len(second.conflicts), 1)
        record = self.customer_list.customers[0]
        self.assertEqual((record.name, record.country), ("Alice", "US"))

    def test_customer_name_and_country_are_never_inferred(self):
        item = self.state.create_customer_list("No Guess")
        self.state.add_emails(item.id, ["person@example.com"])
        self.assertEqual(item.customers[0].name, "")
        self.assertEqual(item.customers[0].country, "")

    def test_invoice_template_has_no_customer_billing_shipping_or_payment_fields(self):
        self.assertEqual(self.template.currency, "USD")
        for field in ("customer", "billing", "shipping", "payment_details"):
            self.assertFalse(hasattr(self.template, field))

    def test_invoice_template_supports_optional_notes_terms_type_and_line_tax(self):
        template = self.state.save_invoice_template(
            template_id=None,
            name="Global",
            currency="eur",
            days_until_due=14,
            memo="Invoice note",
            footer="Footer",
            automatic_tax=True,
            reuse_customer=False,
            invoice_title="Consulting Invoice",
            invoice_subtitle="August services",
            invoice_type="BOS",
            customer_note="Thank you",
            terms=["Net 14", "Late fees may apply"],
            items=[("Consulting", "2.5", "125.00", "7.5")],
        )
        self.assertEqual(template.currency, "EUR")
        self.assertEqual(template.invoice_type, "BOS")
        self.assertEqual(template.customer_note, "Thank you")
        self.assertEqual(template.terms, ["Net 14", "Late fees may apply"])
        self.assertEqual(str(template.items[0].tax_rate), "7.5")

    def test_task_is_bound_to_invoice_template(self):
        task = self.create_task()
        self.assertEqual(task.invoice_template_id, self.template.id)
        self.assertEqual(task.invoice_template_name, self.template.name)

    def test_bound_template_cannot_be_deleted_until_task_is_closed(self):
        task = self.create_task()
        with self.assertRaises(StateError):
            self.state.delete_invoice_template(self.template.id)
        self.state.close_task(task.id)
        self.state.delete_invoice_template(self.template.id)
        self.assertNotIn(self.template.id, self.state.invoice_templates)

    def test_task_requires_an_existing_invoice_template(self):
        with self.assertRaises(StateError):
            self.state.create_task(
                "stripe", "Stripe", [self.account_a.id], self.customer_list.id, "missing-template"
            )


    def test_customer_list_emails_keeps_pre_p04_mutable_list_behavior(self):
        from src.customers.models import CustomerList

        item = CustomerList("legacy", "Legacy", customers=[CustomerRecord("a@example.com", "Alice", "US")])
        legacy_view = item.emails
        self.assertIsInstance(legacy_view, list)
        legacy_view.append("B@Example.com")
        self.assertEqual(item.emails, ["a@example.com", "b@example.com"])
        self.assertEqual((item.customers[0].name, item.customers[0].country), ("Alice", "US"))
        legacy_view[0] = "c@example.com"
        self.assertEqual(item.emails, ["c@example.com", "b@example.com"])

    def test_existing_list_conflict_can_preserve_import_row_number(self):
        self.state.add_customers(
            self.customer_list.id,
            [CustomerRecord("a@example.com", "Alice", "US")],
        )
        result = self.state.add_customers(
            self.customer_list.id,
            [CustomerRecord("a@example.com", "Alicia", "GB")],
            source_rows=[7],
        )
        self.assertEqual(len(result.conflicts), 1)
        self.assertTrue(result.conflicts[0].startswith("Row 7: a@example.com:"))

if __name__ == "__main__":
    unittest.main()


class P05TaskSnapshotStateTests(unittest.TestCase):
    def _state_with_task(self):
        state = AppState()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_snapshot"}, status="Verified"
        )
        customer_list = state.create_customer_list("Customers")
        state.add_customers(
            customer_list.id,
            [
                CustomerRecord("one@example.com", "One", "US"),
                CustomerRecord("two@example.com", "Two", "BD"),
            ],
        )
        template = state.save_invoice_template(
            template_id=None,
            name="Frozen Template",
            currency="USD",
            days_until_due=30,
            memo="Original memo",
            footer="Original footer",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "2.50", "10.25", "7.5")],
            invoice_title="Original title",
            invoice_subtitle="Original subtitle",
            invoice_type="INVOICE",
            customer_note="Original note",
            terms=["Original term"],
        )
        task = state.create_task("stripe", "Stripe", [account.id], customer_list.id, template.id)
        return state, account, customer_list, template, task

    def test_task_creation_captures_immutable_customer_template_provider_and_account_basis(self):
        state, account, customer_list, template, task = self._state_with_task()
        snapshot = task.execution_snapshot
        self.assertIsNotNone(snapshot)
        self.assertTrue(task.has_immutable_execution_snapshot)
        self.assertEqual(snapshot.provider_id, "stripe")
        self.assertEqual(snapshot.account_ids, (account.id,))
        self.assertEqual(snapshot.assignment_strategy, "recipient_ordinal_round_robin_v1")
        self.assertEqual(
            [(item.email, item.name, item.country) for item in snapshot.customers],
            [("one@example.com", "One", "US"), ("two@example.com", "Two", "BD")],
        )
        self.assertEqual(task.total, len(snapshot.customers))
        self.assertEqual(snapshot.template.id, template.id)
        self.assertEqual(snapshot.template.memo, "Original memo")
        self.assertEqual(str(snapshot.template.items[0].quantity), "2.50")
        self.assertEqual(tuple(snapshot.template.terms), ("Original term",))

    def test_customer_and_template_changes_after_task_creation_do_not_change_existing_snapshot(self):
        state, _account, customer_list, template, task = self._state_with_task()
        original_snapshot = task.execution_snapshot
        state.add_customers(customer_list.id, [CustomerRecord("three@example.com", "Three", "GB")])
        state.save_invoice_template(
            template_id=template.id,
            name=template.name,
            currency="EUR",
            days_until_due=14,
            memo="Edited memo",
            footer="Edited footer",
            automatic_tax=True,
            reuse_customer=False,
            items=[("Changed service", "1", "99.00", "0")],
            invoice_title="Edited title",
            invoice_subtitle="Edited subtitle",
            invoice_type="BOS",
            customer_note="Edited note",
            terms=["Edited term"],
        )
        self.assertIs(task.execution_snapshot, original_snapshot)
        self.assertEqual([item.email for item in task.execution_snapshot.customers], ["one@example.com", "two@example.com"])
        self.assertEqual(task.total, 2)
        self.assertEqual(task.execution_snapshot.template.currency, "USD")
        self.assertEqual(task.execution_snapshot.template.memo, "Original memo")
        self.assertEqual(task.execution_snapshot.template.items[0].description, "Service")
        self.assertEqual(task.execution_snapshot.template.terms, ("Original term",))

    def test_progress_remains_clamped_to_immutable_snapshot_total_after_source_list_expands(self):
        state, _account, customer_list, _template, task = self._state_with_task()
        state.add_customers(customer_list.id, [CustomerRecord("three@example.com", "Three", "GB")])
        state.set_task_progress(task.id, processed=99, success=2, failed=0)
        self.assertEqual(task.total, 2)
        self.assertEqual(task.processed, 2)
        self.assertEqual(len(task.execution_snapshot.customers), 2)

    def test_progress_rejects_success_failed_counts_that_disagree_with_processed_snapshot_count(self):
        state, _account, _customer_list, _template, task = self._state_with_task()
        with self.assertRaisesRegex(StateError, "success/failed progress"):
            state.set_task_progress(task.id, processed=1, success=2, failed=0)
        self.assertEqual((task.processed, task.success, task.failed), (0, 0, 0))

    def test_new_logical_execution_requires_new_task_identity_and_captures_current_inputs(self):
        state, account, customer_list, template, first = self._state_with_task()
        state.add_customers(customer_list.id, [CustomerRecord("three@example.com", "Three", "GB")])
        state.save_invoice_template(
            template_id=template.id,
            name=template.name,
            currency="EUR",
            days_until_due=14,
            memo="Edited memo",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Changed", "1", "20", "0")],
        )
        state.close_task(first.id)
        second = state.create_task("stripe", "Stripe", [account.id], customer_list.id, template.id)
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(second.total, 3)
        self.assertEqual(second.execution_snapshot.template.currency, "EUR")
        self.assertEqual(second.execution_snapshot.template.memo, "Edited memo")
