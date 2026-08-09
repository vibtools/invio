from __future__ import annotations

import uuid
from decimal import Decimal

from ...accounts.models import Account
from ...customers.models import CustomerList
from ...invoices.templates import InvoiceItemTemplate, InvoiceTemplate, normalize_invoice_currency
from ...tasks.models import Task
from ..storage import CredentialStore, CredentialStoreError, DomainStore, DomainStoreError, LoadedDomain


class StateError(ValueError):
    pass


class AppState:
    """Application domain state with optional durable P02 persistence services."""

    def __init__(
        self,
        *,
        domain_store: DomainStore | None = None,
        credential_store: CredentialStore | None = None,
        loaded: LoadedDomain | None = None,
    ) -> None:
        self._domain_store = domain_store
        self._credential_store = credential_store
        source = loaded or LoadedDomain()
        self.accounts: dict[str, Account] = dict(source.accounts)
        self.customer_lists: dict[str, CustomerList] = dict(source.customer_lists)
        self.invoice_templates: dict[str, InvoiceTemplate] = dict(source.invoice_templates)
        self.tasks: dict[str, Task] = dict(source.tasks)
        self.account_reservations: dict[str, str] = dict(source.account_reservations)
        self.recovery_warnings: list[str] = list(source.warnings)

    @staticmethod
    def _persistence_error(exc: Exception) -> StateError:
        return StateError(str(exc))

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _safe_verification_error(account: Account, message: str) -> str:
        safe = str(message).strip()
        for secret in sorted((value for value in account.credentials.values() if value), key=len, reverse=True):
            safe = safe.replace(secret, "***REDACTED***")
        return safe

    def add_account(
        self,
        provider_id: str,
        provider_name: str,
        name: str,
        mode: str,
        credentials: dict[str, str],
        status: str = "Ready",
        last_verification_at: str = "",
        verification_error_summary: str = "",
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
            last_verification_at=last_verification_at.strip(),
            verification_error_summary=verification_error_summary.strip(),
        )
        credential_ref = ""
        if self._credential_store is not None:
            try:
                credential_ref = self._credential_store.set_credentials(account.id, account.credentials)
            except CredentialStoreError as exc:
                raise self._persistence_error(exc) from exc
        if self._domain_store is not None:
            try:
                if not credential_ref:
                    raise DomainStoreError("Protected credential storage is required before an account can be persisted.")
                self._domain_store.save_account(account, credential_ref)
            except DomainStoreError as exc:
                cleanup_error: CredentialStoreError | None = None
                if credential_ref and self._credential_store is not None:
                    try:
                        self._credential_store.delete_credentials(credential_ref)
                    except CredentialStoreError as cleanup_exc:
                        cleanup_error = cleanup_exc
                if cleanup_error is not None:
                    raise StateError(
                        f"{exc} Protected credential cleanup also failed; no plaintext fallback was written."
                    ) from exc
                raise self._persistence_error(exc) from exc
        self.accounts[account.id] = account
        return account

    def _account_task_reference(self, account_id: str) -> Task | None:
        reserved_by = self.account_reservations.get(account_id)
        if reserved_by and reserved_by in self.tasks:
            return self.tasks[reserved_by]
        return next((task for task in self.tasks.values() if account_id in task.account_ids), None)

    def update_account(
        self,
        account_id: str,
        *,
        name: str,
        mode: str,
        credentials: dict[str, str],
        status: str,
        last_verification_at: str,
        verification_error_summary: str = "",
    ) -> Account:
        account = self.accounts.get(account_id)
        if account is None:
            raise StateError("Account was not found.")
        referenced_by = self._account_task_reference(account_id)
        if referenced_by is not None:
            raise StateError(
                f"Account '{account.name}' is assigned to {referenced_by.name}. Close that task before editing the account."
            )
        clean_name = name.strip()
        if not clean_name:
            raise StateError("Account name is required.")
        if status != "Verified":
            raise StateError("Account changes require a successful API Test before they can be saved.")

        candidate = Account(
            id=account.id,
            provider_id=account.provider_id,
            provider_name=account.provider_name,
            name=clean_name,
            mode=mode.strip() or "Default",
            status="Verified",
            credentials=dict(credentials),
            last_verification_at=last_verification_at.strip(),
            verification_error_summary=verification_error_summary.strip(),
        )

        safety_state = Account(
            id=account.id,
            provider_id=account.provider_id,
            provider_name=account.provider_name,
            name=account.name,
            mode=account.mode,
            status="Not Verified",
            credentials=dict(account.credentials),
            last_verification_at=account.last_verification_at,
            verification_error_summary="Account update did not complete; run API Test before using this account.",
        )

        old_protected: dict[str, str] | None = None
        credential_ref = CredentialStore.credential_ref(account.id)
        if self._credential_store is not None:
            try:
                old_protected = self._credential_store.get_credentials(credential_ref)
            except CredentialStoreError as exc:
                raise self._persistence_error(exc) from exc

        if self._domain_store is not None:
            try:
                # Persist a fail-closed marker before crossing the SQLite /
                # protected-credential boundary. If the process terminates
                # between stores, restart cannot resurrect an old Verified
                # status beside partially changed credentials.
                self._domain_store.update_account(safety_state)
            except DomainStoreError as exc:
                raise self._persistence_error(exc) from exc

        if self._credential_store is not None:
            try:
                self._credential_store.set_credentials(account.id, candidate.credentials)
            except CredentialStoreError as exc:
                rollback_error: Exception | None = None
                try:
                    if old_protected is None:
                        self._credential_store.delete_credentials(credential_ref)
                    else:
                        self._credential_store.set_credentials(account.id, old_protected)
                except CredentialStoreError as rollback_exc:
                    rollback_error = rollback_exc
                if rollback_error is None and self._domain_store is not None:
                    try:
                        self._domain_store.update_account(account)
                    except DomainStoreError as rollback_exc:
                        rollback_error = rollback_exc
                if rollback_error is not None:
                    self.accounts[account.id] = safety_state
                    raise StateError(
                        f"{exc} Account update rollback also failed; the account remains Not Verified."
                    ) from exc
                raise self._persistence_error(exc) from exc

        if self._domain_store is not None:
            try:
                self._domain_store.update_account(candidate)
            except DomainStoreError as exc:
                rollback_error: CredentialStoreError | None = None
                if self._credential_store is not None:
                    try:
                        if old_protected is None:
                            self._credential_store.delete_credentials(credential_ref)
                        else:
                            self._credential_store.set_credentials(account.id, old_protected)
                    except CredentialStoreError as rollback_exc:
                        rollback_error = rollback_exc
                if rollback_error is None:
                    try:
                        self._domain_store.update_account(account)
                    except DomainStoreError as rollback_exc:
                        self.accounts[account.id] = safety_state
                        raise StateError(
                            f"{exc} Account metadata rollback also failed; the account remains Not Verified."
                        ) from exc
                else:
                    self.accounts[account.id] = safety_state
                    raise StateError(
                        f"{exc} Protected credential rollback also failed; the account remains Not Verified."
                    ) from exc
                raise self._persistence_error(exc) from exc

        self.accounts[account.id] = candidate
        return candidate

    def record_account_verification(
        self,
        account_id: str,
        *,
        verified: bool,
        last_verification_at: str,
        error_summary: str = "",
    ) -> Account:
        account = self.accounts.get(account_id)
        if account is None:
            raise StateError("Account was not found.")
        status = "Verified" if verified else "Not Verified"
        safe_error = "" if verified else self._safe_verification_error(account, error_summary)
        timestamp = last_verification_at.strip()
        if not timestamp:
            raise StateError("Verification timestamp is required.")
        if self._domain_store is not None:
            try:
                self._domain_store.update_account_verification(
                    account.id,
                    status=status,
                    last_verification_at=timestamp,
                    verification_error_summary=safe_error,
                )
            except DomainStoreError as exc:
                # A real failed re-test is authoritative for the current
                # process even if durable storage is temporarily unavailable.
                # Fail closed in memory so a previously Verified account cannot
                # execute after a known verification failure. A successful
                # result never elevates state unless the durable write commits.
                if not verified:
                    account.status = "Not Verified"
                    account.last_verification_at = timestamp
                    account.verification_error_summary = safe_error
                raise self._persistence_error(exc) from exc
        account.status = status
        account.last_verification_at = timestamp
        account.verification_error_summary = safe_error
        return account

    def delete_account(self, account_id: str) -> None:
        account = self.accounts.get(account_id)
        if account is None:
            return
        referenced_by = self._account_task_reference(account_id)
        if referenced_by is not None:
            raise StateError(
                f"Account '{account.name}' is assigned to {referenced_by.name}. Close that task before deleting the account."
            )

        credential_ref = CredentialStore.credential_ref(account.id)
        old_protected: dict[str, str] | None = None
        if self._credential_store is not None:
            try:
                old_protected = self._credential_store.get_credentials(credential_ref)
                self._credential_store.delete_credentials(credential_ref)
            except CredentialStoreError as exc:
                raise self._persistence_error(exc) from exc

        if self._domain_store is not None:
            try:
                self._domain_store.delete_account(account.id)
            except DomainStoreError as exc:
                restore_error: CredentialStoreError | None = None
                if old_protected is not None and self._credential_store is not None:
                    try:
                        self._credential_store.set_credentials(account.id, old_protected)
                    except CredentialStoreError as restore_exc:
                        restore_error = restore_exc
                if restore_error is not None:
                    raise StateError(
                        f"{exc} Protected credential restore also failed; account deletion was not reported as successful."
                    ) from exc
                raise self._persistence_error(exc) from exc

        self.accounts.pop(account.id, None)

    def accounts_for_provider(self, provider_id: str, *, available_only: bool = False) -> list[Account]:
        accounts = [item for item in self.accounts.values() if item.provider_id == provider_id]
        if available_only:
            accounts = [item for item in accounts if item.id not in self.account_reservations]
        return sorted(accounts, key=lambda item: item.name.casefold())

    def create_customer_list(self, name: str) -> CustomerList:
        if not name.strip():
            raise StateError("Customer list name is required.")
        item = CustomerList(id=self._id("list"), name=name.strip())
        if self._domain_store is not None:
            try:
                self._domain_store.create_customer_list(item)
            except DomainStoreError as exc:
                raise self._persistence_error(exc) from exc
        self.customer_lists[item.id] = item
        return item

    def add_emails(self, list_id: str, emails: list[str]) -> int:
        customer_list = self.customer_lists.get(list_id)
        if customer_list is None:
            raise StateError("Customer list was not found.")
        existing = set(customer_list.emails)
        updated_emails = list(customer_list.emails)
        added = 0
        for email in emails:
            normalized = email.strip().lower()
            if normalized and normalized not in existing:
                updated_emails.append(normalized)
                existing.add(normalized)
                added += 1
        if added and self._domain_store is not None:
            candidate = CustomerList(id=customer_list.id, name=customer_list.name, emails=updated_emails)
            try:
                self._domain_store.replace_customer_emails(candidate)
            except DomainStoreError as exc:
                raise self._persistence_error(exc) from exc
        customer_list.emails = updated_emails
        return added

    def delete_customer_list(self, list_id: str) -> None:
        if any(task.customer_list_id == list_id for task in self.tasks.values()):
            raise StateError("This customer list is currently used by a task.")
        if self._domain_store is not None:
            try:
                self._domain_store.delete_customer_list(list_id)
            except DomainStoreError as exc:
                raise self._persistence_error(exc) from exc
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
        if self._domain_store is not None:
            try:
                self._domain_store.save_invoice_template(template)
            except DomainStoreError as exc:
                raise self._persistence_error(exc) from exc
        self.invoice_templates[identifier] = template
        return template

    def delete_invoice_template(self, template_id: str) -> None:
        if any(task.invoice_template_id == template_id for task in self.tasks.values()):
            raise StateError("This invoice template is currently used by a task.")
        if self._domain_store is not None:
            try:
                self._domain_store.delete_invoice_template(template_id)
            except DomainStoreError as exc:
                raise self._persistence_error(exc) from exc
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
        if self._domain_store is not None:
            try:
                self._domain_store.create_task_with_reservations(task)
            except DomainStoreError as exc:
                raise self._persistence_error(exc) from exc
        self.tasks[task.id] = task
        for account in accounts:
            self.account_reservations[account.id] = task.id
        return task

    def close_task(self, task_id: str) -> None:
        task = self.tasks.get(task_id)
        if task is None:
            return
        if self._domain_store is not None:
            try:
                self._domain_store.delete_task_and_release(task_id)
            except DomainStoreError as exc:
                raise self._persistence_error(exc) from exc
        self.tasks.pop(task_id, None)
        for account_id in task.account_ids:
            if self.account_reservations.get(account_id) == task_id:
                self.account_reservations.pop(account_id, None)

    def set_task_status(self, task_id: str, status: str, message: str | None = None) -> Task:
        task = self.tasks[task_id]
        previous_status = task.status
        previous_message = task.last_message
        task.status = status
        if message is not None:
            task.last_message = message
        if self._domain_store is not None:
            try:
                self._domain_store.update_task(task)
            except DomainStoreError as exc:
                task.status = previous_status
                task.last_message = previous_message
                raise self._persistence_error(exc) from exc
        return task

    def set_task_progress(self, task_id: str, *, processed: int, success: int, failed: int) -> Task:
        task = self.tasks[task_id]
        previous = (task.processed, task.success, task.failed)
        task.processed = max(0, min(processed, task.total))
        task.success = max(0, success)
        task.failed = max(0, failed)
        if self._domain_store is not None:
            try:
                self._domain_store.update_task(task)
            except DomainStoreError as exc:
                task.processed, task.success, task.failed = previous
                raise self._persistence_error(exc) from exc
        return task
