from __future__ import annotations

import hashlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

from ...customers.models import CustomerRecord
from ...invoices.templates import InvoiceTemplate
from ..provider_manager import ProviderManager, ProviderManifest, ProviderManifestError
from .adapters import ProviderCapabilityProfile, ProviderSchedulingPolicy, registered_provider_ids

EXTERNAL_ADAPTER_INTERFACE_VERSION = 1

SAFE_READ = "SAFE_READ"
IDEMPOTENT_MUTATION = "IDEMPOTENT_MUTATION"
NON_IDEMPOTENT_MUTATION = "NON_IDEMPOTENT_MUTATION"
EXTERNAL_OPERATION_KINDS = frozenset({SAFE_READ, IDEMPOTENT_MUTATION, NON_IDEMPOTENT_MUTATION})

ADAPTER_STATUS_EXECUTABLE = "Executable"
ADAPTER_STATUS_MANIFEST_ONLY = "Manifest only"
ADAPTER_STATUS_MISSING = "Missing"
ADAPTER_STATUS_INCOMPATIBLE = "Incompatible"


@dataclass(frozen=True, slots=True)
class ExternalValidationIssue:
    code: str
    message: str
    correction: str = ""


@dataclass(frozen=True, slots=True)
class ExternalAccountTestContext:
    provider_id: str
    credentials: dict[str, str]
    mode: str
    request: Callable[..., dict[str, Any]]


@dataclass(frozen=True, slots=True)
class ExternalTaskValidationContext:
    provider_id: str
    template: InvoiceTemplate
    customers: tuple[CustomerRecord, ...]


@dataclass(frozen=True, slots=True)
class ExternalRecipientExecutionContext:
    provider_id: str
    task_id: str
    account_id: str
    account_name: str
    account_mode: str
    credentials: dict[str, str]
    customer: CustomerRecord
    template: InvoiceTemplate
    request: Callable[..., dict[str, Any]]
    log: Callable[[str], None]


@dataclass(frozen=True, slots=True)
class ExternalRecipientResult:
    provider_customer_id: str = ""
    provider_invoice_id: str = ""
    final_stage: str = ""


@runtime_checkable
class ExternalProviderAdapterV1(Protocol):
    interface_version: int
    provider_id: str
    adapter_version: str
    profile: ProviderCapabilityProfile
    scheduling_policy: ProviderSchedulingPolicy | None

    def test_account(self, context: ExternalAccountTestContext) -> str: ...

    def validate_task(self, context: ExternalTaskValidationContext): ...

    def execute_recipient(self, context: ExternalRecipientExecutionContext) -> ExternalRecipientResult: ...


@dataclass(frozen=True, slots=True)
class ExternalAdapterRegistration:
    provider_id: str
    status: str
    message: str = ""
    adapter: ExternalProviderAdapterV1 | None = None

    @property
    def executable(self) -> bool:
        return self.status == ADAPTER_STATUS_EXECUTABLE and self.adapter is not None


class ExternalAdapterError(ValueError):
    pass


class ExternalAdapterRegistry:
    """Discover and validate explicitly trusted external provider adapters.

    Adapters execute in-process with Invio's permissions. This registry provides
    deterministic discovery/validation and fail-closed status reporting; it is
    not a security sandbox.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.manager = ProviderManager(self.project_root)
        self._registrations: dict[str, ExternalAdapterRegistration] = {}
        self.reload_installed()

    @staticmethod
    def _module_name(manifest: ProviderManifest, adapter_path: Path) -> str:
        digest = hashlib.sha256(str(adapter_path.resolve()).encode("utf-8")).hexdigest()[:16]
        return f"_invio_external_{manifest.id}_{digest}"

    @staticmethod
    def _validate_profile(manifest: ProviderManifest, adapter: Any) -> ProviderCapabilityProfile:
        profile = getattr(adapter, "profile", None)
        if not isinstance(profile, ProviderCapabilityProfile):
            raise ExternalAdapterError("Adapter profile must be ProviderCapabilityProfile.")
        if profile.provider_id != manifest.id:
            raise ExternalAdapterError("Adapter profile provider_id does not match the manifest provider id.")
        declared = frozenset(manifest.capabilities)
        if profile.executable_capabilities != declared:
            raise ExternalAdapterError(
                "Adapter executable capabilities must exactly match the manifest capability declaration."
            )
        sending = {"invoice", "send_invoice"}.issubset(declared)
        if sending and "api_test" not in declared:
            raise ExternalAdapterError(
                "External providers with invoice/send_invoice capability must also declare executable api_test."
            )
        if sending != bool(profile.task_execution_enabled):
            raise ExternalAdapterError(
                "Adapter task_execution_enabled does not match its invoice/send_invoice capability contract."
            )
        return profile

    @classmethod
    def validate_adapter(cls, manifest: ProviderManifest, adapter_path: Path) -> ExternalProviderAdapterV1:
        declaration = manifest.runtime_adapter
        if declaration is None:
            raise ExternalAdapterError("Manifest does not declare runtime_adapter.")
        if declaration.interface_version != EXTERNAL_ADAPTER_INTERFACE_VERSION:
            raise ExternalAdapterError(
                f"Unsupported external adapter interface version {declaration.interface_version}; "
                f"Invio requires {EXTERNAL_ADAPTER_INTERFACE_VERSION}."
            )
        if declaration.entrypoint != "create_adapter":
            raise ExternalAdapterError("External adapter entrypoint must be create_adapter.")
        path = Path(adapter_path)
        if path.name != "adapter.py" and not path.name.endswith("_adapter.py"):
            raise ExternalAdapterError("External adapter file must be adapter.py before installation.")
        if not path.is_file():
            raise ExternalAdapterError("External adapter file is missing.")
        if manifest.id in registered_provider_ids():
            raise ExternalAdapterError(f"Provider ID '{manifest.id}' is reserved by a packaged integration.")

        module_name = cls._module_name(manifest, path)
        previous_sys_path = list(sys.path)
        sys.modules.pop(module_name, None)
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ExternalAdapterError("External adapter module could not be loaded.")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            except BaseException as exc:
                raise ExternalAdapterError(
                    f"External adapter import failed: {type(exc).__name__}: {exc}"
                ) from exc
            if sys.path != previous_sys_path:
                raise ExternalAdapterError("External adapter modified sys.path during import; loading was rejected.")
            entrypoint = getattr(module, declaration.entrypoint, None)
            if not callable(entrypoint):
                raise ExternalAdapterError("External adapter create_adapter entrypoint is missing or not callable.")
            try:
                adapter = entrypoint()
            except BaseException as exc:
                raise ExternalAdapterError(
                    f"External adapter create_adapter failed: {type(exc).__name__}: {exc}"
                ) from exc
            if sys.path != previous_sys_path:
                raise ExternalAdapterError("External adapter modified sys.path during create_adapter; loading was rejected.")
        finally:
            sys.path[:] = previous_sys_path
            sys.modules.pop(module_name, None)

        if int(getattr(adapter, "interface_version", -1)) != EXTERNAL_ADAPTER_INTERFACE_VERSION:
            raise ExternalAdapterError("Adapter-reported interface_version does not match Invio interface v1.")
        if str(getattr(adapter, "provider_id", "")).strip().lower() != manifest.id:
            raise ExternalAdapterError("Adapter provider_id does not match manifest provider id.")
        if str(getattr(adapter, "adapter_version", "")).strip() != declaration.adapter_version:
            raise ExternalAdapterError("Adapter version does not match runtime_adapter.adapter_version.")
        profile = cls._validate_profile(manifest, adapter)
        scheduling = getattr(adapter, "scheduling_policy", None)
        if scheduling is not None and not isinstance(scheduling, ProviderSchedulingPolicy):
            raise ExternalAdapterError("Adapter scheduling_policy must be ProviderSchedulingPolicy or None.")
        if scheduling is not None and scheduling.burst_capacity != 1:
            raise ExternalAdapterError("External scheduling_policy burst_capacity must be 1.")

        if "api_test" in profile.executable_capabilities and not callable(getattr(adapter, "test_account", None)):
            raise ExternalAdapterError("Adapter declares api_test but test_account is not callable.")
        if profile.task_execution_enabled:
            if not callable(getattr(adapter, "validate_task", None)):
                raise ExternalAdapterError("Executable Task adapter validate_task is not callable.")
            if not callable(getattr(adapter, "execute_recipient", None)):
                raise ExternalAdapterError("Executable Task adapter execute_recipient is not callable.")
        return adapter

    def validate_source(self, manifest: ProviderManifest, adapter_path: Path) -> None:
        self.validate_adapter(manifest, adapter_path)

    def reload_installed(self) -> None:
        registrations: dict[str, ExternalAdapterRegistration] = {}
        try:
            installed = self.manager.list_installed()
        except ProviderManifestError:
            installed = []
        for manifest in installed:
            if self.manager.get_packaged(manifest.id) is not None:
                continue
            declaration = manifest.runtime_adapter
            if declaration is None:
                registrations[manifest.id] = ExternalAdapterRegistration(
                    manifest.id,
                    ADAPTER_STATUS_MANIFEST_ONLY,
                    "Manifest installed without an executable runtime adapter.",
                )
                continue
            adapter_path = self.manager.external_adapter_path(manifest.id)
            if not adapter_path.is_file():
                registrations[manifest.id] = ExternalAdapterRegistration(
                    manifest.id,
                    ADAPTER_STATUS_MISSING,
                    "Manifest declares executable adapter code but the installed adapter file is missing.",
                )
                continue
            try:
                adapter = self.validate_adapter(manifest, adapter_path)
            except (ExternalAdapterError, ProviderManifestError) as exc:
                registrations[manifest.id] = ExternalAdapterRegistration(
                    manifest.id,
                    ADAPTER_STATUS_INCOMPATIBLE,
                    str(exc),
                )
            else:
                registrations[manifest.id] = ExternalAdapterRegistration(
                    manifest.id,
                    ADAPTER_STATUS_EXECUTABLE,
                    "External runtime adapter interface v1 validated.",
                    adapter,
                )
        self._registrations = registrations

    def registration(self, provider_id: str) -> ExternalAdapterRegistration | None:
        return self._registrations.get(provider_id.strip().lower())

    def adapter(self, provider_id: str) -> ExternalProviderAdapterV1 | None:
        registration = self.registration(provider_id)
        return registration.adapter if registration is not None and registration.executable else None

    def status(self, provider_id: str) -> ExternalAdapterRegistration:
        normalized = provider_id.strip().lower()
        registration = self.registration(normalized)
        if registration is not None:
            return registration
        return ExternalAdapterRegistration(
            normalized,
            ADAPTER_STATUS_MANIFEST_ONLY,
            "No executable external adapter is registered.",
        )
