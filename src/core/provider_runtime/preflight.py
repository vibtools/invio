from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable
from urllib.parse import urlsplit

from ...accounts.models import Account
from ...customers.models import CustomerRecord
from ...invoices.templates import InvoiceTemplate, SUPPORTED_INVOICE_CURRENCY_SET
from ...tasks.models import TASK_ASSIGNMENT_STRATEGY, TASK_SNAPSHOT_CAPTURED, Task
from ..provider_manager import ProviderManifest

CANONICAL_REFRENS_BASE_URL = "https://api.refrens.com"


@dataclass(frozen=True, slots=True)
class ProviderCapabilityProfile:
    provider_id: str
    executable_capabilities: frozenset[str]
    task_execution_enabled: bool
    task_unavailable_message: str
    invoice_types: frozenset[str]
    currencies: frozenset[str] | None
    supports_automatic_tax: bool
    supports_line_tax: bool
    supports_customer_reuse: bool
    supports_memo: bool
    supports_footer: bool
    supports_customer_note: bool
    supports_terms: bool
    required_customer_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreflightIssue:
    code: str
    message: str
    correction: str = ""

    @property
    def display_message(self) -> str:
        if not self.correction:
            return self.message
        return f"{self.message} {self.correction}"


@dataclass(frozen=True, slots=True)
class PreflightResult:
    issues: tuple[PreflightIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.issues

    @property
    def first_issue(self) -> PreflightIssue | None:
        return self.issues[0] if self.issues else None

    @property
    def message(self) -> str:
        issue = self.first_issue
        return issue.display_message if issue is not None else "Preflight passed."


_STRIPE_PROFILE = ProviderCapabilityProfile(
    provider_id="stripe",
    executable_capabilities=frozenset({"invoice", "send_invoice", "api_test"}),
    task_execution_enabled=True,
    task_unavailable_message="",
    invoice_types=frozenset({"INVOICE"}),
    currencies=frozenset(SUPPORTED_INVOICE_CURRENCY_SET),
    supports_automatic_tax=False,
    supports_line_tax=False,
    supports_customer_reuse=True,
    supports_memo=True,
    supports_footer=True,
    supports_customer_note=True,
    supports_terms=True,
    required_customer_fields=("email",),
)

_REFRENS_PROFILE = ProviderCapabilityProfile(
    provider_id="refrens",
    # The built-in Refrens API-test adapter is executable today. The normal
    # Task invoice/send pipeline remains deliberately disabled until P11.
    executable_capabilities=frozenset({"api_test"}),
    task_execution_enabled=False,
    task_unavailable_message=(
        "Refrens production Task sending is not enabled until P11. No invoice request was made."
    ),
    invoice_types=frozenset({"INVOICE", "BOS"}),
    currencies=None,
    supports_automatic_tax=False,
    supports_line_tax=True,
    supports_customer_reuse=False,
    supports_memo=True,
    supports_footer=True,
    supports_customer_note=True,
    supports_terms=True,
    required_customer_fields=("email", "name", "country"),
)

_BUILTIN_PROFILES = {
    _STRIPE_PROFILE.provider_id: _STRIPE_PROFILE,
    _REFRENS_PROFILE.provider_id: _REFRENS_PROFILE,
}


def capability_profile(provider_id: str) -> ProviderCapabilityProfile | None:
    return _BUILTIN_PROFILES.get(provider_id.strip().lower())


def executable_capabilities(provider_id: str) -> tuple[str, ...]:
    profile = capability_profile(provider_id)
    if profile is None:
        return ()
    order = ("invoice", "send_invoice", "api_test")
    return tuple(value for value in order if value in profile.executable_capabilities)


def effective_capabilities(manifest: ProviderManifest) -> tuple[str, ...]:
    runtime = set(executable_capabilities(manifest.id))
    return tuple(value for value in manifest.capabilities if value in runtime)


def _credential_contract(manifest: ProviderManifest) -> tuple[tuple[str, str, bool], ...]:
    return tuple((field.key, field.kind, field.required) for field in manifest.credential_fields)


def manifest_runtime_contract_matches(installed: ProviderManifest, packaged: ProviderManifest) -> bool:
    """Compare execution-relevant manifest declarations for a packaged runtime ID.

    Display-only name/version/description fields intentionally do not affect the
    executable runtime binding. Credential order is retained because it is also
    the deterministic credential-entry contract shown to the user.
    """

    return (
        installed.id == packaged.id
        and _credential_contract(installed) == _credential_contract(packaged)
        and tuple(installed.account_modes) == tuple(packaged.account_modes)
        and frozenset(installed.capabilities) == frozenset(packaged.capabilities)
    )


def canonical_refrens_base_url(value: str) -> str:
    raw = str(value).strip()
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Refrens API Base URL must be exactly https://api.refrens.com.") from exc
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "api.refrens.com"
        or port not in {None, 443}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Refrens API Base URL must be exactly https://api.refrens.com.")
    return CANONICAL_REFRENS_BASE_URL


def _provider_issues(
    *,
    provider_id: str,
    installed_manifest: ProviderManifest | None,
    packaged_manifest: ProviderManifest | None,
    injected_runner_available: bool,
) -> list[PreflightIssue]:
    issues: list[PreflightIssue] = []
    normalized = provider_id.strip().lower()
    if installed_manifest is None:
        return [
            PreflightIssue(
                "provider-not-installed",
                "The selected provider is not installed.",
                "Reinstall the provider before creating, starting or retrying this Task.",
            )
        ]

    if installed_manifest.id != normalized:
        return [
            PreflightIssue(
                "provider-id-mismatch",
                "The installed provider identity does not match the selected provider.",
                "Reinstall the correct provider package.",
            )
        ]

    if packaged_manifest is not None and not manifest_runtime_contract_matches(installed_manifest, packaged_manifest):
        return [
            PreflightIssue(
                "packaged-manifest-runtime-mismatch",
                f"Installed {packaged_manifest.name} manifest does not match the packaged {packaged_manifest.name} runtime contract.",
                f"Uninstall it and install the packaged {packaged_manifest.name} provider again.",
            )
        ]

    profile = capability_profile(normalized)
    if profile is None:
        if injected_runner_available:
            # P13 owns an executable external-provider capability contract. Keep
            # the existing injected-runner API usable without inventing
            # provider-specific tax/currency/customer semantics in P06.
            return issues
        return [
            PreflightIssue(
                "runtime-unavailable",
                f"No executable Task runtime is registered for provider '{installed_manifest.name}'.",
                "Use a provider with an executable runtime, or wait for the approved external runtime capability phase.",
            )
        ]

    effective = set(effective_capabilities(installed_manifest))
    if not profile.task_execution_enabled or not {"invoice", "send_invoice"}.issubset(effective):
        message = profile.task_unavailable_message or (
            f"{installed_manifest.name} does not have executable invoice/send capability in the current Invio runtime."
        )
        return [PreflightIssue("task-runtime-unavailable", message)]
    return issues


def _account_issues(accounts: Iterable[Account], manifest: ProviderManifest) -> list[PreflightIssue]:
    issues: list[PreflightIssue] = []
    accounts = tuple(accounts)
    if not accounts:
        return [PreflightIssue("account-missing", "Select at least one provider account.")]

    required_fields = tuple(field for field in manifest.credential_fields if field.required)
    allowed_modes = {mode.casefold(): mode for mode in manifest.account_modes}

    for account in accounts:
        if account.provider_id != manifest.id:
            issues.append(
                PreflightIssue(
                    "account-provider-mismatch",
                    f"Account '{account.name}' does not belong to {manifest.name}.",
                    "Select only accounts for the selected provider.",
                )
            )
            continue
        if account.status != "Verified":
            issues.append(
                PreflightIssue(
                    "account-not-verified",
                    f"Account '{account.name}' is not verified.",
                    "Run a successful API Test before executing this Task.",
                )
            )
        verification_timestamp = account.last_verification_at.strip()
        verification_timestamp_valid = False
        if verification_timestamp:
            try:
                parsed_timestamp = datetime.fromisoformat(verification_timestamp)
            except ValueError:
                parsed_timestamp = None
            verification_timestamp_valid = parsed_timestamp is not None and parsed_timestamp.tzinfo is not None
        if not verification_timestamp_valid:
            issues.append(
                PreflightIssue(
                    "account-verification-health-incomplete",
                    f"Account '{account.name}' does not have a complete verification-health record.",
                    "Re-test the account before executing this Task.",
                )
            )
        if account.verification_error_summary.strip():
            issues.append(
                PreflightIssue(
                    "account-verification-error",
                    f"Account '{account.name}' has a recorded verification error.",
                    "Re-test the account successfully before executing this Task.",
                )
            )
        if manifest.account_modes and account.mode.casefold() not in allowed_modes:
            issues.append(
                PreflightIssue(
                    "account-mode-unsupported",
                    f"Account '{account.name}' uses mode '{account.mode}', which is not declared by the installed provider manifest.",
                    "Edit and re-verify the account with a supported provider mode.",
                )
            )
        for field in required_fields:
            if not str(account.credentials.get(field.key, "")).strip():
                issues.append(
                    PreflightIssue(
                        "account-credential-missing",
                        f"Account '{account.name}' is missing required credential '{field.label}'.",
                        "Edit and re-verify the account before executing this Task.",
                    )
                )

        if manifest.id == "stripe":
            key = str(account.credentials.get("secret_key", "")).strip()
            if key and not key.startswith(("sk_test_", "sk_live_", "rk_test_", "rk_live_")):
                issues.append(
                    PreflightIssue(
                        "stripe-key-format",
                        f"Account '{account.name}' has an invalid Stripe secret/restricted key format.",
                        "Edit and re-verify the Stripe account.",
                    )
                )
            mode = account.mode.strip().casefold()
            if key and mode == "test" and "_test_" not in key:
                issues.append(
                    PreflightIssue(
                        "stripe-mode-key-mismatch",
                        f"Account '{account.name}' is Test mode but its configured Stripe key is not a test key.",
                        "Edit and re-verify the Stripe account.",
                    )
                )
            if key and mode == "live" and "_live_" not in key:
                issues.append(
                    PreflightIssue(
                        "stripe-mode-key-mismatch",
                        f"Account '{account.name}' is Live mode but its configured Stripe key is not a live key.",
                        "Edit and re-verify the Stripe account.",
                    )
                )

    return issues




def _endpoint_issues(accounts: Iterable[Account], manifest: ProviderManifest) -> list[PreflightIssue]:
    if manifest.id != "refrens":
        return []
    issues: list[PreflightIssue] = []
    for account in accounts:
        try:
            canonical_refrens_base_url(str(account.credentials.get("base_url", "")))
        except ValueError:
            issues.append(
                PreflightIssue(
                    "refrens-endpoint-untrusted",
                    f"Account '{account.name}' does not use the trusted Refrens API endpoint.",
                    f"Set API Base URL to {CANONICAL_REFRENS_BASE_URL} and re-test the account.",
                )
            )
    return issues


def _template_and_customer_issues(
    profile: ProviderCapabilityProfile | None,
    template: InvoiceTemplate,
    customers: Iterable[CustomerRecord],
) -> list[PreflightIssue]:
    if profile is None:
        return []

    issues: list[PreflightIssue] = []
    currency = template.currency.strip().upper()
    if profile.currencies is not None and currency not in profile.currencies:
        issues.append(
            PreflightIssue(
                "currency-unsupported",
                f"Currency '{currency or '(blank)'}' is not supported by the current {profile.provider_id.title()} Invio contract.",
                "Choose a supported invoice currency before executing this Task.",
            )
        )

    invoice_type = template.invoice_type.strip().upper()
    if invoice_type not in profile.invoice_types:
        if profile.provider_id == "stripe":
            correction = "Select Invoice instead of Bill of Supply."
        else:
            correction = "Choose an invoice type supported by the provider."
        issues.append(
            PreflightIssue(
                "invoice-type-unsupported",
                f"{profile.provider_id.title()}'s current Invio adapter does not support invoice type '{invoice_type or '(blank)'}'.",
                correction,
            )
        )

    if template.automatic_tax and not profile.supports_automatic_tax:
        if profile.provider_id == "stripe":
            correction = (
                "Disable Automatic Tax for this Task. Current Invio customer data/send contract cannot guarantee "
                "Stripe Tax location requirements before invoice creation."
            )
        else:
            correction = "Disable Automatic Tax for this provider."
        issues.append(
            PreflightIssue(
                "automatic-tax-unsupported",
                f"Automatic Tax is not supported by the current {profile.provider_id.title()} Invio contract.",
                correction,
            )
        )

    if not profile.supports_line_tax and any(Decimal(item.tax_rate) != 0 for item in template.items):
        correction = (
            "Set line tax to 0 before running this Task."
            if profile.provider_id == "stripe"
            else "Remove line tax values before executing this Task."
        )
        issues.append(
            PreflightIssue(
                "line-tax-unsupported",
                f"{profile.provider_id.title()}'s current Invio adapter does not apply template percentage line-tax values.",
                correction,
            )
        )

    if template.reuse_customer and not profile.supports_customer_reuse:
        issues.append(
            PreflightIssue(
                "customer-reuse-unsupported",
                f"Customer reuse is not supported by the current {profile.provider_id.title()} Invio contract.",
                "Disable customer reuse before executing this Task.",
            )
        )
    if template.memo.strip() and not profile.supports_memo:
        issues.append(PreflightIssue("memo-unsupported", "The selected provider does not support the template memo."))
    if template.footer.strip() and not profile.supports_footer:
        issues.append(PreflightIssue("footer-unsupported", "The selected provider does not support the template footer."))
    if template.customer_note.strip() and not profile.supports_customer_note:
        issues.append(PreflightIssue("customer-note-unsupported", "The selected provider does not support customer notes."))
    if template.terms and not profile.supports_terms:
        issues.append(PreflightIssue("terms-unsupported", "The selected provider does not support template terms."))

    customer_records = tuple(customers)
    if not customer_records:
        issues.append(PreflightIssue("customer-missing", "The immutable Task snapshot has no customers."))
        return issues

    for index, customer in enumerate(customer_records, start=1):
        missing: list[str] = []
        for field_name in profile.required_customer_fields:
            if not str(getattr(customer, field_name, "")).strip():
                missing.append(field_name)
        if missing:
            issues.append(
                PreflightIssue(
                    "customer-data-missing",
                    f"Customer {index} ({customer.email or 'no email'}) is missing provider-required data: {', '.join(missing)}.",
                    "Update the Customer List with explicit required data; Invio will not guess customer information.",
                )
            )
    return issues




def preflight_runtime_inputs(
    *,
    provider_id: str,
    template: InvoiceTemplate,
    customers: Iterable[CustomerRecord],
) -> PreflightResult:
    """Validate provider-specific immutable inputs without installation/network side effects."""
    profile = capability_profile(provider_id)
    return PreflightResult(tuple(_template_and_customer_issues(profile, template, customers)))


def preflight_candidate(
    *,
    provider_id: str,
    installed_manifest: ProviderManifest | None,
    packaged_manifest: ProviderManifest | None,
    accounts: Iterable[Account],
    template: InvoiceTemplate,
    customers: Iterable[CustomerRecord],
    injected_runner_available: bool = False,
) -> PreflightResult:
    issues = _provider_issues(
        provider_id=provider_id,
        installed_manifest=installed_manifest,
        packaged_manifest=packaged_manifest,
        injected_runner_available=injected_runner_available,
    )
    if installed_manifest is None:
        return PreflightResult(tuple(issues))

    account_values = tuple(accounts)
    issues.extend(_account_issues(account_values, installed_manifest))
    profile = capability_profile(provider_id)
    issues.extend(_template_and_customer_issues(profile, template, customers))
    issues.extend(_endpoint_issues(account_values, installed_manifest))
    return PreflightResult(tuple(issues))


def preflight_task(
    *,
    task: Task,
    installed_manifest: ProviderManifest | None,
    packaged_manifest: ProviderManifest | None,
    accounts: Iterable[Account],
    injected_runner_available: bool = False,
) -> PreflightResult:
    issues: list[PreflightIssue] = []
    execution = task.execution_snapshot
    if execution is None or execution.state != TASK_SNAPSHOT_CAPTURED:
        return PreflightResult(
            (PreflightIssue("snapshot-unavailable", "The Task does not have a captured immutable execution snapshot."),)
        )
    if execution.provider_id != task.provider_id:
        issues.append(PreflightIssue("snapshot-provider-mismatch", "The immutable Task snapshot provider does not match the Task provider."))
    if execution.assignment_strategy != TASK_ASSIGNMENT_STRATEGY:
        issues.append(PreflightIssue("snapshot-assignment-unsupported", "The immutable Task snapshot uses an unsupported account-assignment strategy."))
    if execution.account_ids != tuple(task.account_ids):
        issues.append(PreflightIssue("snapshot-account-mismatch", "The immutable Task snapshot account order does not match the Task binding."))
    if execution.template is None:
        issues.append(PreflightIssue("snapshot-template-missing", "The immutable Task snapshot has no invoice template."))
    elif execution.template.id != task.invoice_template_id:
        issues.append(PreflightIssue("snapshot-template-mismatch", "The immutable Task snapshot template does not match the Task binding."))
    if task.total != len(execution.customers):
        issues.append(PreflightIssue("snapshot-total-mismatch", "Task total does not match the immutable recipient snapshot."))
    if issues:
        return PreflightResult(tuple(issues))

    provider_result = _provider_issues(
        provider_id=task.provider_id,
        installed_manifest=installed_manifest,
        packaged_manifest=packaged_manifest,
        injected_runner_available=injected_runner_available,
    )
    issues.extend(provider_result)
    if installed_manifest is None:
        return PreflightResult(tuple(issues))

    account_values = tuple(accounts)
    issues.extend(_account_issues(account_values, installed_manifest))
    profile = capability_profile(task.provider_id)
    issues.extend(
        _template_and_customer_issues(
            profile,
            execution.template.to_template(),
            execution.customers,
        )
    )
    issues.extend(_endpoint_issues(account_values, installed_manifest))
    return PreflightResult(tuple(issues))
