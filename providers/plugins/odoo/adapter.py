from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import re
from typing import Any
from urllib.parse import urlsplit

from src.core.provider_runtime import (
    ExternalRecipientResult,
    ExternalValidationIssue,
    NON_IDEMPOTENT_MUTATION,
    SAFE_READ,
    ProviderCapabilityProfile,
    ProviderRuntimeError,
)


PROVIDER_ID = "odoo"
ADAPTER_VERSION = "1.0.1"
USER_AGENT = "Invio-Odoo-Provider/1.0.1 Vib-Tools"


class Adapter:
    interface_version = 1
    provider_id = PROVIDER_ID
    adapter_version = ADAPTER_VERSION
    scheduling_policy = None
    profile = ProviderCapabilityProfile(
        provider_id=PROVIDER_ID,
        executable_capabilities=frozenset({"invoice", "send_invoice", "api_test"}),
        task_execution_enabled=True,
        task_unavailable_message="",
        invoice_types=frozenset({"INVOICE"}),
        currencies=None,
        supports_automatic_tax=False,
        supports_line_tax=False,
        supports_customer_reuse=True,
        supports_memo=True,
        supports_footer=False,
        supports_customer_note=False,
        supports_terms=False,
        required_customer_fields=("email", "name", "country"),
    )

    def test_account(self, context):
        base_url, database, username, api_key = self._account_values(context.credentials)
        endpoint = f"{base_url}/jsonrpc"
        uid = self._authenticate(context, endpoint, database, username, api_key)

        self._execute_kw(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            stage="account_move_access",
            operation_kind=SAFE_READ,
            model="account.move",
            method="search_read",
            args=[[]],
            kwargs={"fields": ["id", "name", "state"], "limit": 1},
        )
        wizard_fields = self._execute_kw(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            stage="send_wizard_contract",
            operation_kind=SAFE_READ,
            model="account.move.send.wizard",
            method="fields_get",
            args=[],
            kwargs={"attributes": ["type", "required", "readonly"]},
        )
        if not isinstance(wizard_fields, dict):
            raise ProviderRuntimeError(
                "Odoo account.move.send.wizard fields_get did not return a field mapping.",
                category="response",
                retryable=False,
            )
        required = {"move_id", "sending_methods", "sending_method_checkboxes", "mail_partner_ids"}
        missing = sorted(required.difference(wizard_fields))
        if missing:
            raise ProviderRuntimeError(
                "Odoo invoice send wizard is missing required field(s): " + ", ".join(missing),
                category="provider-contract",
                retryable=False,
            )
        return "Odoo API connection verified."

    def validate_task(self, context):
        issues: list[ExternalValidationIssue] = []
        template = context.template
        if str(template.invoice_type).strip().upper() != "INVOICE":
            issues.append(
                ExternalValidationIssue(
                    "odoo_invoice_type",
                    "Odoo provider supports customer invoices only.",
                    "Use Invoice Type INVOICE.",
                )
            )
        if str(template.invoice_title).strip() not in {"", "Invoice"}:
            issues.append(
                ExternalValidationIssue(
                    "odoo_invoice_title",
                    "Odoo assigns the posted customer-invoice presentation; a custom Invio invoice title is not mapped.",
                    "Use the default Invoice title for this Odoo Task.",
                )
            )
        if str(template.invoice_subtitle).strip():
            issues.append(
                ExternalValidationIssue(
                    "odoo_invoice_subtitle",
                    "Odoo provider does not map the Invio invoice subtitle field.",
                    "Leave Invoice Subtitle blank for this Odoo Task.",
                )
            )
        if not template.items:
            issues.append(
                ExternalValidationIssue(
                    "odoo_items",
                    "Odoo invoice requires at least one line item.",
                    "Add at least one invoice item.",
                )
            )
        for index, item in enumerate(template.items, start=1):
            if Decimal(item.quantity) <= 0:
                issues.append(
                    ExternalValidationIssue(
                        "odoo_quantity",
                        f"Odoo invoice item {index} must have a positive quantity.",
                        "Use a quantity greater than zero.",
                    )
                )
            if Decimal(item.unit_amount) < 0:
                issues.append(
                    ExternalValidationIssue(
                        "odoo_unit_amount",
                        f"Odoo invoice item {index} cannot use a negative unit amount in this adapter.",
                        "Use a zero or positive unit amount.",
                    )
                )
        return tuple(issues)

    def execute_recipient(self, context):
        base_url, database, username, api_key = self._account_values(context.credentials)
        endpoint = f"{base_url}/jsonrpc"
        uid = self._authenticate(context, endpoint, database, username, api_key)

        partner_id = 0
        if bool(context.template.reuse_customer):
            partners = self._execute_kw(
                context,
                endpoint=endpoint,
                database=database,
                uid=uid,
                api_key=api_key,
                stage="partner_lookup",
                operation_kind=SAFE_READ,
                model="res.partner",
                method="search_read",
                args=[[["email", "=ilike", context.customer.email]]],
                kwargs={"fields": ["id", "name", "email"], "limit": 1},
            )
            records = self._records(partners)
            if records:
                partner_id = self._positive_int(records[0].get("id"))
                if partner_id:
                    context.log(f"Odoo customer found for {context.customer.email} (partner {partner_id}).")

        if partner_id <= 0:
            country_id = self._resolve_country(
                context,
                endpoint=endpoint,
                database=database,
                uid=uid,
                api_key=api_key,
                country_code=context.customer.country,
            )
            partner_payload: dict[str, Any] = {
                "name": context.customer.name,
                "email": context.customer.email,
                "country_id": country_id,
            }
            partner_response = self._execute_kw_response(
                context,
                endpoint=endpoint,
                database=database,
                uid=uid,
                api_key=api_key,
                stage="partner_create",
                operation_kind=NON_IDEMPOTENT_MUTATION,
                model="res.partner",
                method="create",
                args=[partner_payload],
                kwargs={},
                provider_reference_key="result",
            )
            partner_id = self._positive_int(self._require_result(partner_response, "Odoo customer create"))
            if partner_id <= 0:
                raise ProviderRuntimeError(
                    "Odoo customer create did not return a valid partner id.",
                    category="response",
                    retryable=False,
                )
            context.log(f"Odoo customer created for {context.customer.email} (partner {partner_id}).")

        currency_id = self._resolve_currency(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            currency_code=context.template.currency,
        )
        today = date.today()
        due = today + timedelta(days=int(context.template.days_until_due))
        lines = [
            [
                0,
                0,
                {
                    "name": str(item.description).strip() or "Service",
                    "quantity": float(Decimal(item.quantity)),
                    "price_unit": float(Decimal(item.unit_amount)),
                },
            ]
            for item in context.template.items
        ]
        move_payload: dict[str, Any] = {
            "move_type": "out_invoice",
            "partner_id": partner_id,
            "invoice_date": today.isoformat(),
            "invoice_date_due": due.isoformat(),
            "currency_id": currency_id,
            "invoice_line_ids": lines,
        }
        memo = str(context.template.memo).strip()
        if memo:
            move_payload["narration"] = memo

        invoice_response = self._execute_kw_response(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            stage="invoice_create",
            operation_kind=NON_IDEMPOTENT_MUTATION,
            model="account.move",
            method="create",
            args=[move_payload],
            kwargs={},
            provider_reference_key="result",
        )
        invoice_id = self._positive_int(self._require_result(invoice_response, "Odoo invoice create"))
        if invoice_id <= 0:
            raise ProviderRuntimeError(
                "Odoo invoice create did not return a valid invoice id.",
                category="response",
                retryable=False,
            )
        context.log(f"Odoo draft invoice created (provider invoice {invoice_id}).")

        self._execute_kw(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            stage="invoice_post",
            operation_kind=NON_IDEMPOTENT_MUTATION,
            model="account.move",
            method="action_post",
            args=[[invoice_id]],
            kwargs={},
        )

        invoice_records = self._records(
            self._execute_kw(
                context,
                endpoint=endpoint,
                database=database,
                uid=uid,
                api_key=api_key,
                stage="invoice_verify_posted",
                operation_kind=SAFE_READ,
                model="account.move",
                method="read",
                args=[[invoice_id], ["id", "name", "state", "partner_id", "invoice_pdf_report_id"]],
                kwargs={},
            )
        )
        if not invoice_records or str(invoice_records[0].get("state", "")).strip().lower() != "posted":
            raise ProviderRuntimeError(
                "Odoo invoice did not verify as posted after action_post.",
                category="provider-state",
                retryable=False,
            )
        invoice_number = str(invoice_records[0].get("name", "")).strip()
        context.log(f"Odoo invoice posted{f' as {invoice_number}' if invoice_number else ''}.")

        before_message_ids = self._best_effort_message_ids(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            invoice_id=invoice_id,
            stage="mail_baseline",
        )

        send_context = {
            "active_model": "account.move",
            "active_id": invoice_id,
            "active_ids": [invoice_id],
            "default_move_id": invoice_id,
            "mail_notify_force_send": True,
        }
        wizard_payload = {
            "move_id": invoice_id,
            "sending_method_checkboxes": {"email": {"checked": True, "label": "Email"}},
            "mail_partner_ids": [[6, 0, [partner_id]]],
        }
        wizard_response = self._execute_kw_response(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            stage="send_wizard_create",
            operation_kind=NON_IDEMPOTENT_MUTATION,
            model="account.move.send.wizard",
            method="create",
            args=[wizard_payload],
            kwargs={"context": send_context},
            provider_reference_key="result",
        )
        wizard_id = self._positive_int(self._require_result(wizard_response, "Odoo invoice send wizard create"))
        if wizard_id <= 0:
            raise ProviderRuntimeError(
                "Odoo invoice send wizard create did not return a valid wizard id.",
                category="response",
                retryable=False,
            )

        wizard_records = self._records(
            self._execute_kw(
                context,
                endpoint=endpoint,
                database=database,
                uid=uid,
                api_key=api_key,
                stage="send_wizard_verify",
                operation_kind=SAFE_READ,
                model="account.move.send.wizard",
                method="read",
                args=[
                    [wizard_id],
                    ["move_id", "sending_methods", "sending_method_checkboxes", "mail_partner_ids", "alerts"],
                ],
                kwargs={"context": send_context},
            )
        )
        if not wizard_records:
            raise ProviderRuntimeError(
                "Odoo invoice send wizard could not be read before execution.",
                category="provider-state",
                retryable=False,
            )
        wizard = wizard_records[0]
        sending_methods = self._string_list(wizard.get("sending_methods"))
        mail_partner_ids = self._number_list(wizard.get("mail_partner_ids"))
        if "email" not in sending_methods:
            raise ProviderRuntimeError(
                "Odoo invoice send wizard did not select the email sending method.",
                category="provider-state",
                retryable=False,
            )
        if not mail_partner_ids:
            raise ProviderRuntimeError(
                "Odoo invoice send wizard did not resolve an email recipient.",
                category="provider-state",
                retryable=False,
            )
        alerts = wizard.get("alerts")
        if alerts:
            raise ProviderRuntimeError(
                "Odoo invoice send wizard reported a blocking alert before send.",
                category="provider-state",
                retryable=False,
            )

        self._execute_kw(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            stage="invoice_send",
            operation_kind=NON_IDEMPOTENT_MUTATION,
            model="account.move.send.wizard",
            method="action_send_and_print",
            args=[[wizard_id]],
            kwargs={"context": send_context},
        )

        evidence = self._inspect_email_evidence(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            invoice_id=invoice_id,
            before_message_ids=before_message_ids,
        )
        evidence_error = self._email_evidence_error(evidence)
        if evidence_error is not None:
            raise evidence_error
        context.log(
            f"Odoo invoice email requested for {context.customer.email}; provider evidence: {evidence['status']}."
        )
        if evidence["message"]:
            context.log(evidence["message"])

        return ExternalRecipientResult(
            provider_customer_id=str(partner_id),
            provider_invoice_id=str(invoice_id),
            final_stage="external_mutation:invoice_send",
        )

    @staticmethod
    def _account_values(credentials: dict[str, str]) -> tuple[str, str, str, str]:
        base_url = Adapter._normalize_base_url(credentials.get("base_url", ""))
        database = str(credentials.get("database", "")).strip()
        username = str(credentials.get("username", "")).strip()
        api_key = str(credentials.get("api_key", "")).strip()
        missing = [
            label
            for label, value in (("Database", database), ("Username / Email", username), ("API Key", api_key))
            if not value
        ]
        if missing:
            raise ProviderRuntimeError(
                "Odoo account is missing required credential field(s): " + ", ".join(missing),
                category="credentials",
                retryable=False,
            )
        return base_url, database, username, api_key

    @staticmethod
    def _normalize_base_url(value: str) -> str:
        raw = str(value).strip().rstrip("/")
        if not raw:
            raise ProviderRuntimeError("Odoo Base URL is required.", category="credentials", retryable=False)
        parsed = urlsplit(raw)
        if parsed.scheme.lower() != "https" or not parsed.hostname:
            raise ProviderRuntimeError(
                "Odoo Base URL must be an HTTPS origin such as https://your-company.odoo.com.",
                category="credentials",
                retryable=False,
            )
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ProviderRuntimeError(
                "Odoo Base URL must not contain userinfo, query parameters, or fragments.",
                category="credentials",
                retryable=False,
            )
        if parsed.path not in {"", "/"}:
            raise ProviderRuntimeError(
                "Odoo Base URL must be the instance origin only; do not include /jsonrpc or another path.",
                category="credentials",
                retryable=False,
            )
        return f"https://{parsed.netloc}"

    def _authenticate(self, context, endpoint: str, database: str, username: str, api_key: str) -> int:
        response = self._rpc_response(
            context,
            endpoint=endpoint,
            stage="authenticate",
            operation_kind=SAFE_READ,
            service="common",
            method="authenticate",
            args=[database, username, api_key, {}],
        )
        uid = self._positive_int(self._require_result(response, "Odoo authentication"))
        if uid <= 0:
            raise ProviderRuntimeError(
                "Odoo authentication failed or returned an empty UID.",
                category="authentication",
                retryable=False,
            )
        return uid

    def _execute_kw(
        self,
        context,
        *,
        endpoint: str,
        database: str,
        uid: int,
        api_key: str,
        stage: str,
        operation_kind: str,
        model: str,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> Any:
        response = self._execute_kw_response(
            context,
            endpoint=endpoint,
            database=database,
            uid=uid,
            api_key=api_key,
            stage=stage,
            operation_kind=operation_kind,
            model=model,
            method=method,
            args=args,
            kwargs=kwargs,
        )
        return self._require_result(response, f"Odoo {model}.{method}")

    def _execute_kw_response(
        self,
        context,
        *,
        endpoint: str,
        database: str,
        uid: int,
        api_key: str,
        stage: str,
        operation_kind: str,
        model: str,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any],
        provider_reference_key: str = "",
    ) -> dict[str, Any]:
        return self._rpc_response(
            context,
            endpoint=endpoint,
            stage=stage,
            operation_kind=operation_kind,
            service="object",
            method="execute_kw",
            args=[database, uid, api_key, model, method, args, kwargs],
            provider_reference_key=provider_reference_key,
        )

    def _rpc_response(
        self,
        context,
        *,
        endpoint: str,
        stage: str,
        operation_kind: str,
        service: str,
        method: str,
        args: list[Any],
        provider_reference_key: str = "",
    ) -> dict[str, Any]:
        request_kwargs: dict[str, Any] = {
            "stage": stage,
            "operation_kind": operation_kind,
            "method": "POST",
            "url": endpoint,
            "headers": {
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            "json_data": {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"service": service, "method": method, "args": args},
                "id": f"invio-odoo-{stage}",
            },
        }
        if provider_reference_key:
            request_kwargs["provider_reference_key"] = provider_reference_key
        response = context.request(**request_kwargs)
        if not isinstance(response, dict):
            raise ProviderRuntimeError(
                f"Odoo {stage} returned a non-object JSON-RPC response.",
                category="response",
                retryable=False,
            )
        if "error" in response and response.get("error"):
            raise ProviderRuntimeError(
                self._jsonrpc_error_message(response.get("error")),
                category="provider",
                retryable=False,
            )
        return response

    @staticmethod
    def _require_result(response: dict[str, Any], operation: str) -> Any:
        if "error" in response and response.get("error"):
            raise ProviderRuntimeError(
                Adapter._jsonrpc_error_message(response.get("error")),
                category="provider",
                retryable=False,
            )
        if "result" not in response:
            raise ProviderRuntimeError(
                f"{operation} did not return a JSON-RPC result.",
                category="response",
                retryable=False,
            )
        return response.get("result")

    @staticmethod
    def _jsonrpc_error_message(error: Any) -> str:
        if not isinstance(error, dict):
            return "Odoo JSON-RPC returned an unspecified provider error."
        data = error.get("data")
        data_message = str(data.get("message", "")).strip() if isinstance(data, dict) else ""
        message = data_message or str(error.get("message", "")).strip()
        return message or "Odoo JSON-RPC returned an unspecified provider error."

    def _resolve_country(
        self,
        context,
        *,
        endpoint: str,
        database: str,
        uid: int,
        api_key: str,
        country_code: str,
    ) -> int:
        code = str(country_code).strip().upper()
        records = self._records(
            self._execute_kw(
                context,
                endpoint=endpoint,
                database=database,
                uid=uid,
                api_key=api_key,
                stage="country_lookup",
                operation_kind=SAFE_READ,
                model="res.country",
                method="search_read",
                args=[[["code", "=", code]]],
                kwargs={"fields": ["id", "code", "name"], "limit": 1},
            )
        )
        country_id = self._positive_int(records[0].get("id")) if records else 0
        if country_id <= 0:
            raise ProviderRuntimeError(
                f"Odoo country {code} was not found.",
                category="provider-data",
                retryable=False,
            )
        return country_id

    def _resolve_currency(
        self,
        context,
        *,
        endpoint: str,
        database: str,
        uid: int,
        api_key: str,
        currency_code: str,
    ) -> int:
        code = str(currency_code).strip().upper()
        records = self._records(
            self._execute_kw(
                context,
                endpoint=endpoint,
                database=database,
                uid=uid,
                api_key=api_key,
                stage="currency_lookup",
                operation_kind=SAFE_READ,
                model="res.currency",
                method="search_read",
                args=[[["name", "=", code]]],
                kwargs={"fields": ["id", "name", "active"], "limit": 1},
            )
        )
        currency_id = self._positive_int(records[0].get("id")) if records else 0
        if currency_id <= 0:
            raise ProviderRuntimeError(
                f"Odoo currency {code} was not found.",
                category="provider-data",
                retryable=False,
            )
        return currency_id

    def _best_effort_message_ids(
        self,
        context,
        *,
        endpoint: str,
        database: str,
        uid: int,
        api_key: str,
        invoice_id: int,
        stage: str,
    ) -> set[int] | None:
        try:
            result = self._execute_kw(
                context,
                endpoint=endpoint,
                database=database,
                uid=uid,
                api_key=api_key,
                stage=stage,
                operation_kind=SAFE_READ,
                model="mail.message",
                method="search",
                args=[[["model", "=", "account.move"], ["res_id", "=", invoice_id]]],
                kwargs={"order": "id desc", "limit": 100},
            )
        except Exception as exc:
            context.log(f"Odoo mail evidence baseline unavailable: {exc}")
            return None
        return set(self._number_list(result))

    @staticmethod
    def _email_evidence_error(evidence: dict[str, str]) -> ProviderRuntimeError | None:
        status = str(evidence.get("status", "")).strip().upper()
        message = str(evidence.get("message", "")).strip()
        if status == "FAILED":
            normalized = message.casefold()
            daily_limit = re.search(r"\breached your daily limit of \d+ emails?\b", normalized) is not None
            if daily_limit:
                return ProviderRuntimeError(
                    "Odoo invoice email provider evidence reported failure: " + message,
                    category="provider-quota",
                    retryable=False,
                    halt_batch=True,
                    halt_code="daily-email-limit",
                    user_message=(
                        "Odoo daily email limit reached. No new recipients will be started in this Task. "
                        "Resolve the provider limit before using Resume Remaining."
                    ),
                )
            return ProviderRuntimeError(
                "Odoo invoice email provider evidence reported failure: " + (message or "Odoo reported an email failure state."),
                category="provider-mail",
                retryable=False,
            )
        if status == "UNVERIFIED":
            return ProviderRuntimeError(
                "Odoo invoice email outcome could not be verified after the send request: "
                + (message or "No conclusive provider mail evidence was available."),
                category="provider-mail-unverified",
                retryable=False,
                halt_batch=True,
                halt_code="mail-evidence-unverified",
                user_message=(
                    "Odoo invoice email outcome could not be verified. No new recipients will be started "
                    "until the provider outcome is reviewed."
                ),
            )
        return None

    def _inspect_email_evidence(
        self,
        context,
        *,
        endpoint: str,
        database: str,
        uid: int,
        api_key: str,
        invoice_id: int,
        before_message_ids: set[int] | None,
    ) -> dict[str, str]:
        if before_message_ids is None:
            return {
                "status": "UNVERIFIED",
                "message": "Odoo send wizard completed, but pre-send mail.message evidence was not readable.",
            }
        try:
            messages = self._records(
                self._execute_kw(
                    context,
                    endpoint=endpoint,
                    database=database,
                    uid=uid,
                    api_key=api_key,
                    stage="mail_message_after",
                    operation_kind=SAFE_READ,
                    model="mail.message",
                    method="search_read",
                    args=[[["model", "=", "account.move"], ["res_id", "=", invoice_id]]],
                    kwargs={
                        "fields": ["id", "message_type", "subject", "partner_ids", "attachment_ids"],
                        "order": "id desc",
                        "limit": 100,
                    },
                )
            )
        except Exception as exc:
            return {
                "status": "UNVERIFIED",
                "message": f"Odoo send wizard completed, but post-send mail.message evidence was not readable: {exc}",
            }
        new_message_ids = [
            self._positive_int(row.get("id"))
            for row in messages
            if self._positive_int(row.get("id")) > 0 and self._positive_int(row.get("id")) not in before_message_ids
        ]
        if not new_message_ids:
            return {
                "status": "UNVERIFIED",
                "message": "Odoo send wizard completed without a new attempt-bound mail.message record.",
            }

        try:
            notifications = self._records(
                self._execute_kw(
                    context,
                    endpoint=endpoint,
                    database=database,
                    uid=uid,
                    api_key=api_key,
                    stage="mail_notification_after",
                    operation_kind=SAFE_READ,
                    model="mail.notification",
                    method="search_read",
                    args=[[["mail_message_id", "in", new_message_ids], ["notification_type", "=", "email"]]],
                    kwargs={
                        "fields": [
                            "id",
                            "notification_status",
                            "failure_type",
                            "failure_reason",
                            "res_partner_id",
                            "mail_message_id",
                            "mail_mail_id",
                        ],
                        "order": "id desc",
                        "limit": 100,
                    },
                )
            )
            mails = self._records(
                self._execute_kw(
                    context,
                    endpoint=endpoint,
                    database=database,
                    uid=uid,
                    api_key=api_key,
                    stage="mail_mail_after",
                    operation_kind=SAFE_READ,
                    model="mail.mail",
                    method="search_read",
                    args=[[ ["mail_message_id", "in", new_message_ids] ]],
                    kwargs={
                        "fields": [
                            "id",
                            "state",
                            "failure_type",
                            "failure_reason",
                            "email_to",
                            "recipient_ids",
                            "mail_message_id",
                        ],
                        "order": "id desc",
                        "limit": 100,
                    },
                )
            )
        except Exception as exc:
            return {
                "status": "UNVERIFIED",
                "message": f"Odoo send wizard completed, but notification/mail evidence was not readable: {exc}",
            }

        notification_statuses = {
            str(row.get("notification_status", "")).strip().lower()
            for row in notifications
            if str(row.get("notification_status", "")).strip()
        }
        mail_states = {
            str(row.get("state", "")).strip().lower()
            for row in mails
            if str(row.get("state", "")).strip()
        }
        failure_states = {"bounce", "exception", "canceled", "cancel"}
        if notification_statuses.intersection(failure_states) or mail_states.intersection(failure_states):
            failure_messages = [
                str(row.get("failure_reason") or row.get("failure_type") or "").strip()
                for row in [*notifications, *mails]
            ]
            message = "; ".join(dict.fromkeys(value for value in failure_messages if value))
            return {"status": "FAILED", "message": message or "Odoo reported an email failure state."}
        if "sent" in notification_statuses or "sent" in mail_states:
            return {"status": "SENT", "message": "Odoo provider evidence reports the invoice email as sent."}
        if notification_statuses.intersection({"ready", "process", "pending"}) or "outgoing" in mail_states:
            return {"status": "QUEUED", "message": "Odoo provider evidence reports the invoice email as queued/processing."}
        return {
            "status": "UNVERIFIED",
            "message": "Odoo send wizard completed, but no terminal/queued mail evidence was available. Confirm the Odoo mail queue and recipient inbox.",
        }

    @staticmethod
    def _records(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [row for row in value if isinstance(row, dict)]

    @staticmethod
    def _positive_int(value: Any) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return 0
        return number if number > 0 else 0

    @staticmethod
    def _number_list(value: Any) -> list[int]:
        if not isinstance(value, list):
            return []
        result: list[int] = []
        for item in value:
            number = Adapter._positive_int(item)
            if number:
                result.append(number)
        return result

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]


def create_adapter():
    return Adapter()
