from __future__ import annotations

import unittest

from src.core.state import AppState, StateError


class AppStateTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.account_a = self.state.add_account("stripe", "Stripe", "A", "Test", {"secret_key": "x"})
        self.account_b = self.state.add_account("stripe", "Stripe", "B", "Test", {"secret_key": "y"})
        self.account_other = self.state.add_account("other", "Other", "C", "Test", {"token": "z"})
        self.customer_list = self.state.create_customer_list("List 1")
        self.state.add_emails(self.customer_list.id, ["a@example.com", "b@example.com"])

    def test_accounts_are_filtered_by_provider(self):
        ids = {item.id for item in self.state.accounts_for_provider("stripe")}
        self.assertEqual(ids, {self.account_a.id, self.account_b.id})

    def test_account_cannot_be_reserved_by_two_tasks(self):
        first = self.state.create_task("stripe", "Stripe", [self.account_a.id], self.customer_list.id)
        with self.assertRaises(StateError):
            self.state.create_task("stripe", "Stripe", [self.account_a.id], self.customer_list.id)
        self.state.close_task(first.id)
        second = self.state.create_task("stripe", "Stripe", [self.account_a.id], self.customer_list.id)
        self.assertIn(second.id, self.state.tasks)

    def test_mixed_provider_accounts_are_rejected(self):
        with self.assertRaises(StateError):
            self.state.create_task(
                "stripe",
                "Stripe",
                [self.account_a.id, self.account_other.id],
                self.customer_list.id,
            )

    def test_customer_list_deduplicates_emails(self):
        added = self.state.add_emails(self.customer_list.id, ["A@example.com", "c@example.com"])
        self.assertEqual(added, 1)
        self.assertEqual(self.customer_list.count, 3)

    def test_invoice_template_has_no_customer_fields(self):
        template = self.state.save_invoice_template(
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
        self.assertEqual(template.name, "Default")
        self.assertFalse(hasattr(template, "customer"))
        self.assertFalse(hasattr(template, "billing"))
        self.assertFalse(hasattr(template, "shipping"))


if __name__ == "__main__":
    unittest.main()
