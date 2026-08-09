from __future__ import annotations

import uuid
from decimal import Decimal

from ...accounts.models import Account
from ...customers.models import CustomerList
from ...invoices.templates import InvoiceItemTemplate, InvoiceTemplate, normalize_invoice_currency
from ...tasks.models import Task


class StateError(ValueError):
    pass


class AppState:
    """In-memory application state for the current application session."""

    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}
        self.customer_lists: dict[str, CustomerList] = {}
        self.invoice_templates: dict[str, InvoiceTemplate] = {}
        self.tasks: dict[str, Task] = {}
        self.account_reservations: dict[str, str] = {}

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def add_account(
        self,
        provider_id: str,
        provider_name: str,
        name: str,
        mode: str,
        credentials: dict[str, str],
        status: str = "Ready",
    ) -> Account:
        if not name.strip():
            raise StateError("Account name is required.")
        account = Account(
            id=self._id("acct"),
            provider_id=provider_id,
            provider_name=provider_name,
            name=name.strip(),
            mode=mode.strip() or "Default",
            status=status,
            credentials=dict(credentials),
        )
        self.accounts[account.id] = account
        return account

    def accounts_for_provider(self, provider_id: str, *, available_only: bool = False) -> list[Account]:
        accounts = [item for item in self.accounts.values() if item.provider_id == provider_id]
        if available_only:
            accounts = [item for item in accounts if item.id not in self.account_reservations]
        return sorted(accounts, key=lambda item: item.name.casefold())

    def create_customer_list(self, name: str) -> CustomerList:
        if not name.strip():
            raise StateError("Customer list name is required.")
        item = CustomerList(id=self._id("list"), name=name.strip())
        self.customer_lists[item.id] = item
        return item

    def add_emails(self, list_id: str, emails: list[str]) -> int:
        customer_list = self.customer_lists.get(list_id)
        if customer_list is None:
            raise StateError("Customer list was not found.")
        existing = set(customer_list.emails)
        added = 0
        for email in emails:
            normalized = email.strip().lower()
            if normalized and normalized not in existing:
                customer_list.emails.append(normalized)
                existing.add(normalized)
                added += 1
        return added

    def delete_customer_list(self, list_id: str) -> None:
        if any(task.customer_list_id == list_id for task in self.tasks.values()):
            raise StateError("This customer list is currently used by a task.")
        self.customer_lists.pop(list_id, None)

    def save_invoice_template(
        self,
        *,
        template_id: str | None,
        name: str,
        currency: str,
        days_until_due: int,
        memo: str,
        footer: str,
        automatic_tax: bool,
        reuse_customer: bool,
        items: list[tuple[str, ...]],
        invoice_title: str = "Invoice",
        invoice_subtitle: str = "",
        invoice_type: str = "INVOICE",
        customer_note: str = "",
        terms: list[str] | tuple[str, ...] = (),
    ) -> InvoiceTemplate:
        clean_name = name.strip()
        if not clean_name:
            raise StateError("Template name is required.")
        try:
            clean_currency = normalize_invoice_currency(currency)
        except ValueError as exc:
            raise StateError(str(exc)) from exc

        due_days = int(days_until_due)
        if due_days < 1 or due_days > 365:
            raise StateError("Days until due must be between 1 and 365.")

        normalized_type = invoice_type.strip().upper() or "INVOICE"
        if normalized_type not in {"INVOICE", "BOS"}:
            raise StateError("Invoice type must be INVOICE or BOS.")

        parsed_items: list[InvoiceItemTemplate] = []
        for index, raw_item in enumerate(items, 1):
            if len(raw_item) not in {3, 4}:
                raise StateError(f"Item {index}: invalid invoice item structure.")
            description, quantity, amount = raw_item[:3]
            tax_rate = raw_item[3] if len(raw_item) == 4 else "0"
            if not description.strip():
                raise StateError(f"Item {index}: description is required.")
            try:
                quantity_value = Decimal(quantity)
                amount_value = Decimal(amount)
                tax_rate_value = Decimal(tax_rate or "0")
            except Exception as exc:
                raise StateError(f"Item {index}: quantity, amount and tax rate must be numeric.") from exc
            if quantity_value <= 0 or amount_value < 0:
                raise StateError(f"Item {index}: quantity must be greater than zero and amount cannot be negative.")
            if tax_rate_value < 0 or tax_rate_value > 100:
                raise StateError(f"Item {index}: tax rate must be between 0 and 100.")
            parsed_items.append(
                InvoiceItemTemplate(
                    description.strip(),
                    quantity_value,
                    amount_value,
                    tax_rate_value,
                )
            )
        if not parsed_items:
            raise StateError("At least one invoice item is required.")

        clean_terms = [str(term).strip() for term in terms if str(term).strip()]
        identifier = template_id or self._id("tpl")
        template = InvoiceTemplate(
            id=identifier,
            name=clean_name,
            currency=clean_currency,
            days_until_due=due_days,
            memo=memo.strip(),
            footer=footer.strip(),
            automatic_tax=bool(automatic_tax),
            reuse_customer=bool(reuse_customer),
            items=parsed_items,
            invoice_title=invoice_title.strip() or "Invoice",
            invoice_subtitle=invoice_subtitle.strip(),
            invoice_type=normalized_type,
            customer_note=customer_note.strip(),
            terms=clean_terms,
        )
        self.invoice_templates[identifier] = template
        return template

    def delete_invoice_template(self, template_id: str) -> None:
        if any(task.invoice_template_id == template_id for task in self.tasks.values()):
            raise StateError("This invoice template is currently used by a task.")
        self.invoice_templates.pop(template_id, None)

    def create_task(
        self,
        provider_id: str,
        provider_name: str,
        account_ids: list[str],
        customer_list_id: str,
        invoice_template_id: str,
    ) -> Task:
        if not account_ids:
            raise StateError("Select at least one account.")
        customer_list = self.customer_lists.get(customer_list_id)
        if customer_list is None:
            raise StateError("Select a customer list.")
        if not customer_list.emails:
            raise StateError("The selected customer list has no email addresses.")
        invoice_template = self.invoice_templates.get(invoice_template_id)
        if invoice_template is None:
            raise StateError("Select an invoice template.")

        accounts: list[Account] = []
        for account_id in account_ids:
            account = self.accounts.get(account_id)
            if account is None:
                raise StateError("One of the selected accounts no longer exists.")
            if account.provider_id != provider_id:
                raise StateError("All selected accounts must belong to the selected provider.")
            if account.status != "Verified":
                raise StateError(f"Account '{account.name}' is not verified. Run a successful API Test before creating a task.")
            reserved_by = self.account_reservations.get(account_id)
            if reserved_by:
                task_name = self.tasks.get(reserved_by).name if reserved_by in self.tasks else reserved_by
                raise StateError(f"Account '{account.name}' is already assigned to {task_name}.")
            accounts.append(account)

        number = len(self.tasks) + 1
        task = Task(
            id=self._id("task"),
            name=f"Task {number}",
            provider_id=provider_id,
            provider_name=provider_name,
            account_ids=list(account_ids),
            account_names=[account.name for account in accounts],
            customer_list_id=customer_list.id,
            customer_list_name=customer_list.name,
            invoice_template_id=invoice_template.id,
            invoice_template_name=invoice_template.name,
            total=customer_list.count,
        )
        self.tasks[task.id] = task
        for account in accounts:
            self.account_reservations[account.id] = task.id
        return task

    def close_task(self, task_id: str) -> None:
        task = self.tasks.pop(task_id, None)
        if task is None:
            return
        for account_id in task.account_ids:
            if self.account_reservations.get(account_id) == task_id:
                self.account_reservations.pop(account_id, None)

    def set_task_status(self, task_id: str, status: str, message: str | None = None) -> Task:
        task = self.tasks[task_id]
        task.status = status
        if message is not None:
            task.last_message = message
        return task

    def set_task_progress(self, task_id: str, *, processed: int, success: int, failed: int) -> Task:
        task = self.tasks[task_id]
        task.processed = max(0, min(processed, task.total))
        task.success = max(0, success)
        task.failed = max(0, failed)
        return task
