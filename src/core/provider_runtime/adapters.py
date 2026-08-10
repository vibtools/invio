from __future__ import annotations

from dataclasses import dataclass

from ...invoices.templates import SUPPORTED_INVOICE_CURRENCY_SET
from ..provider_manager import CredentialField, ProviderManifest


@dataclass(frozen=True, slots=True)
class ProviderCapabilityProfile:
    """Provider-neutral execution/preflight contract used by Invio runtime gates."""

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
class ProviderSchedulingPolicy:
    """Internal P09 scheduling limits for an executable packaged provider."""

    requests_per_second_per_account: float
    burst_capacity: int
    account_cooldown_base_seconds: float
    account_cooldown_cap_seconds: float
    provider_cooldown_base_seconds: float
    provider_cooldown_cap_seconds: float
    account_rate_limit_reasons: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class ProviderAdapterContract:
    """Static binding between a packaged provider manifest and executable runtime handlers.

    Handler names are resolved on ``ProviderRuntime`` at call time. This keeps
    the packaged provider contract provider-neutral without importing or
    executing arbitrary Python from provider packages. A missing handler is an
    intentional fail-closed state, not an implicit capability.
    """

    provider_id: str
    manifest_contract: ProviderManifest
    profile: ProviderCapabilityProfile
    api_test_handler: str | None = None
    task_batch_handler: str | None = None
    api_test_unavailable_message: str = ""
    task_unavailable_message: str = ""
    scheduling_policy: ProviderSchedulingPolicy | None = None

    @property
    def supports_api_test(self) -> bool:
        return self.api_test_handler is not None and "api_test" in self.profile.executable_capabilities

    @property
    def supports_task_execution(self) -> bool:
        return (
            self.task_batch_handler is not None
            and self.profile.task_execution_enabled
            and {"invoice", "send_invoice"}.issubset(self.profile.executable_capabilities)
        )


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
    executable_capabilities=frozenset({"invoice", "send_invoice", "api_test"}),
    task_execution_enabled=True,
    task_unavailable_message="",
    invoice_types=frozenset({"INVOICE", "BOS"}),
    currencies=frozenset(SUPPORTED_INVOICE_CURRENCY_SET),
    supports_automatic_tax=False,
    supports_line_tax=True,
    supports_customer_reuse=False,
    supports_memo=True,
    supports_footer=True,
    supports_customer_note=True,
    supports_terms=True,
    required_customer_fields=("email", "name", "country"),
)

# The owner-supplied current Agiled Public API OpenAPI contract verifies Bearer
# authentication plus GET /public/v1/me and invoice CRUD under /public/v1.
# It does not publish an invoice email/send operation, and its generic
# MutationRequest does not define the field-level invoice mutation contract.
# API Test can therefore execute safely, while Task sending must remain
# fail-closed rather than guessing invoice fields or reusing the unrelated
# document-email endpoint.
_AGILED_PROFILE = ProviderCapabilityProfile(
    provider_id="agiled",
    executable_capabilities=frozenset({"api_test"}),
    task_execution_enabled=False,
    task_unavailable_message=(
        "Agiled Task sending is fail-closed because the current Agiled Public API OpenAPI contract exposes invoice "
        "CRUD but no invoice email/send operation and no field-level invoice mutation schema. No Agiled invoice "
        "request was made."
    ),
    invoice_types=frozenset({"INVOICE"}),
    currencies=frozenset(SUPPORTED_INVOICE_CURRENCY_SET),
    supports_automatic_tax=False,
    supports_line_tax=False,
    supports_customer_reuse=False,
    supports_memo=False,
    supports_footer=False,
    supports_customer_note=False,
    supports_terms=False,
    required_customer_fields=("email",),
)


_STRIPE_SCHEDULING_POLICY = ProviderSchedulingPolicy(
    requests_per_second_per_account=20.0,
    burst_capacity=1,
    account_cooldown_base_seconds=5.0,
    account_cooldown_cap_seconds=60.0,
    provider_cooldown_base_seconds=5.0,
    provider_cooldown_cap_seconds=60.0,
    account_rate_limit_reasons=frozenset(
        {
            "global-rate",
            "global-concurrency",
            "endpoint-rate",
            "endpoint-concurrency",
            "resource-specific",
        }
    ),
)


_REFRENS_SCHEDULING_POLICY = ProviderSchedulingPolicy(
    # Owner-approved Invio safety ceiling. Refrens does not publish a numeric
    # API request-rate ceiling in the current official API documentation.
    requests_per_second_per_account=1.0,
    burst_capacity=1,
    account_cooldown_base_seconds=5.0,
    account_cooldown_cap_seconds=60.0,
    provider_cooldown_base_seconds=5.0,
    provider_cooldown_cap_seconds=60.0,
    account_rate_limit_reasons=frozenset(),
)


_STRIPE_MANIFEST_CONTRACT = ProviderManifest(
    id="stripe",
    name="Stripe",
    version="runtime",
    description="Built-in Stripe runtime contract.",
    credential_fields=(CredentialField("secret_key", "Secret key", "password", True),),
    account_modes=("Test", "Live"),
    capabilities=("invoice", "send_invoice", "api_test"),
)

_REFRENS_MANIFEST_CONTRACT = ProviderManifest(
    id="refrens",
    name="Refrens",
    version="runtime",
    description="Built-in Refrens runtime contract.",
    credential_fields=(
        CredentialField("base_url", "API Base URL", "text", True),
        CredentialField("url_key", "URL Key", "text", True),
        CredentialField("app_id", "App ID", "text", True),
        CredentialField("app_secret", "App Secret", "password", True),
    ),
    account_modes=("Default",),
    capabilities=("invoice", "send_invoice", "api_test"),
)

_AGILED_MANIFEST_CONTRACT = ProviderManifest(
    id="agiled",
    name="Agiled",
    version="runtime",
    description="Built-in Agiled API-test contract with Task sending fail-closed pending an official invoice-send schema.",
    credential_fields=(CredentialField("api_key", "API Key", "password", True),),
    account_modes=("Default",),
    capabilities=("invoice", "send_invoice", "api_test"),
)


_BUILTIN_ADAPTERS = {
    "stripe": ProviderAdapterContract(
        provider_id="stripe",
        manifest_contract=_STRIPE_MANIFEST_CONTRACT,
        profile=_STRIPE_PROFILE,
        api_test_handler="_test_stripe_account",
        task_batch_handler="_run_stripe_batch",
        scheduling_policy=_STRIPE_SCHEDULING_POLICY,
    ),
    "refrens": ProviderAdapterContract(
        provider_id="refrens",
        manifest_contract=_REFRENS_MANIFEST_CONTRACT,
        profile=_REFRENS_PROFILE,
        api_test_handler="_test_refrens_account",
        task_batch_handler="_run_refrens_batch",
        api_test_unavailable_message="No built-in Refrens API-test adapter is available.",
        scheduling_policy=_REFRENS_SCHEDULING_POLICY,
    ),
    "agiled": ProviderAdapterContract(
        provider_id="agiled",
        manifest_contract=_AGILED_MANIFEST_CONTRACT,
        profile=_AGILED_PROFILE,
        api_test_handler="_test_agiled_account",
        task_unavailable_message=_AGILED_PROFILE.task_unavailable_message,
    ),
}


def provider_adapter_contract(provider_id: str) -> ProviderAdapterContract | None:
    return _BUILTIN_ADAPTERS.get(provider_id.strip().lower())


def provider_capability_profile(provider_id: str) -> ProviderCapabilityProfile | None:
    adapter = provider_adapter_contract(provider_id)
    return adapter.profile if adapter is not None else None


def provider_runtime_manifest_contract(provider_id: str) -> ProviderManifest | None:
    adapter = provider_adapter_contract(provider_id)
    return adapter.manifest_contract if adapter is not None else None


def registered_provider_ids() -> tuple[str, ...]:
    return tuple(_BUILTIN_ADAPTERS)
