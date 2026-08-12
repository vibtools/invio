from __future__ import annotations

import json
import re
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path

from .ivx import (
    IVX_ADAPTER_FILENAME,
    IVX_LOGO_FILENAME,
    IVX_MARKER_FILENAME,
    IvxPackageError,
    extract_ivx,
    inspect_ivx,
    read_ivx_marker,
    write_ivx_marker,
)

_PROVIDER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")


CREDENTIAL_OWNERSHIP_USER_REQUIRED = "user_required"
CREDENTIAL_OWNERSHIP_USER_CHOICE = "user_choice"
CREDENTIAL_OWNERSHIP_GENERATED = "generated"
CREDENTIAL_OWNERSHIP_DISCOVERED = "discovered"
CREDENTIAL_OWNERSHIP_MANAGED = "managed"
CREDENTIAL_OWNERSHIPS = frozenset({
    CREDENTIAL_OWNERSHIP_USER_REQUIRED,
    CREDENTIAL_OWNERSHIP_USER_CHOICE,
    CREDENTIAL_OWNERSHIP_GENERATED,
    CREDENTIAL_OWNERSHIP_DISCOVERED,
    CREDENTIAL_OWNERSHIP_MANAGED,
})


@dataclass(frozen=True, slots=True)
class CredentialChoice:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class CredentialField:
    key: str
    label: str
    kind: str = "text"
    required: bool = True
    placeholder: str = ""
    ownership: str = CREDENTIAL_OWNERSHIP_USER_REQUIRED
    choices: tuple[CredentialChoice, ...] = field(default_factory=tuple)

    @property
    def quick_connect_visible(self) -> bool:
        return self.ownership == CREDENTIAL_OWNERSHIP_USER_REQUIRED


@dataclass(frozen=True, slots=True)
class BrowserAuthDeclaration:
    interface_version: int


@dataclass(frozen=True, slots=True)
class OnboardingDeclaration:
    interface_version: int


@dataclass(frozen=True, slots=True)
class ProviderManifest:
    id: str
    name: str
    version: str
    description: str
    credential_fields: tuple[CredentialField, ...] = field(default_factory=tuple)
    account_modes: tuple[str, ...] = field(default_factory=tuple)
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    source_path: Path | None = None
    runtime_adapter: RuntimeAdapterDeclaration | None = None
    browser_auth: BrowserAuthDeclaration | None = None
    onboarding: OnboardingDeclaration | None = None


@dataclass(frozen=True, slots=True)
class RuntimeAdapterDeclaration:
    interface_version: int
    adapter_version: str
    entrypoint: str


class ProviderManifestError(ValueError):
    pass


class ProviderManager:
    """Manifest-driven provider package and installation-state manager.

    This manager parses and installs provider declarations but does not itself
    import provider code. P13 executable bundles are validated by an explicit
    runtime validator before their manifest/adapter files are atomically copied
    into ``providers/registry``.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.packages_dir = self.project_root / "providers" / "packages"
        self.registry_dir = self.project_root / "providers" / "registry"
        self.ivx_staging_dir = self.project_root / "providers" / ".staging"
        self.registry_dir.mkdir(parents=True, exist_ok=True)

    def _parse_manifest(self, path: Path) -> ProviderManifest:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProviderManifestError(f"Invalid provider manifest: {path.name}") from exc

        provider_id = str(raw.get("id", "")).strip().lower()
        name = str(raw.get("name", "")).strip()
        version = str(raw.get("version", "")).strip()
        description = str(raw.get("description", "")).strip()
        if not _PROVIDER_ID_RE.fullmatch(provider_id):
            raise ProviderManifestError("Provider id must use lowercase letters, digits, hyphens or underscores.")
        if not name or not version:
            raise ProviderManifestError("Provider name and version are required.")

        fields: list[CredentialField] = []
        for item in raw.get("credential_fields", []):
            key = str(item.get("key", "")).strip()
            label = str(item.get("label", "")).strip()
            kind = str(item.get("kind", "text")).strip().lower()
            ownership = str(item.get("ownership", CREDENTIAL_OWNERSHIP_USER_REQUIRED)).strip().lower()
            if not key or not label or kind not in {"text", "password"}:
                raise ProviderManifestError("Credential fields require key, label and a text/password kind.")
            if ownership not in CREDENTIAL_OWNERSHIPS:
                raise ProviderManifestError(
                    "Credential field ownership must be user_required, user_choice, generated, discovered or managed."
                )
            raw_choices = item.get("choices", [])
            if not isinstance(raw_choices, list):
                raise ProviderManifestError("Credential field choices must be an array when provided.")
            choices: list[CredentialChoice] = []
            seen_choice_values: set[str] = set()
            for choice in raw_choices:
                if not isinstance(choice, dict):
                    raise ProviderManifestError("Credential field choices require label/value objects.")
                choice_label = str(choice.get("label", "")).strip()
                choice_value = str(choice.get("value", "")).strip()
                if not choice_label or not choice_value or choice_value in seen_choice_values:
                    raise ProviderManifestError("Credential field choices require non-empty labels and unique non-empty values.")
                seen_choice_values.add(choice_value)
                choices.append(CredentialChoice(choice_label, choice_value))
            if choices and kind != "text":
                raise ProviderManifestError("Credential field choices are supported only for text fields.")
            fields.append(
                CredentialField(
                    key=key,
                    label=label,
                    kind=kind,
                    required=bool(item.get("required", True)),
                    placeholder=str(item.get("placeholder", "")),
                    ownership=ownership,
                    choices=tuple(choices),
                )
            )

        modes = tuple(str(value).strip() for value in raw.get("account_modes", []) if str(value).strip())
        capabilities = tuple(str(value).strip() for value in raw.get("capabilities", []) if str(value).strip())
        runtime_adapter = None
        runtime_raw = raw.get("runtime_adapter")
        if runtime_raw is not None:
            if not isinstance(runtime_raw, dict):
                raise ProviderManifestError("runtime_adapter must be an object when provided.")
            try:
                interface_version = int(runtime_raw.get("interface_version"))
            except (TypeError, ValueError) as exc:
                raise ProviderManifestError("runtime_adapter.interface_version must be an integer.") from exc
            adapter_version = str(runtime_raw.get("adapter_version", "")).strip()
            entrypoint = str(runtime_raw.get("entrypoint", "")).strip()
            if interface_version < 1 or not adapter_version or entrypoint != "create_adapter":
                raise ProviderManifestError(
                    "runtime_adapter requires interface_version >= 1, adapter_version and entrypoint 'create_adapter'."
                )
            runtime_adapter = RuntimeAdapterDeclaration(interface_version, adapter_version, entrypoint)

        browser_auth = None
        browser_raw = raw.get("browser_auth")
        if browser_raw is not None:
            if not isinstance(browser_raw, dict):
                raise ProviderManifestError("browser_auth must be an object when provided.")
            try:
                browser_interface_version = int(browser_raw.get("interface_version"))
            except (TypeError, ValueError) as exc:
                raise ProviderManifestError("browser_auth.interface_version must be an integer.") from exc
            if browser_interface_version != 1:
                raise ProviderManifestError("browser_auth.interface_version must be 1 for the current Invio host contract.")
            if runtime_adapter is None:
                raise ProviderManifestError("browser_auth requires an executable runtime_adapter.")
            browser_auth = BrowserAuthDeclaration(browser_interface_version)

        onboarding = None
        onboarding_raw = raw.get("onboarding")
        if onboarding_raw is not None:
            if not isinstance(onboarding_raw, dict):
                raise ProviderManifestError("onboarding must be an object when provided.")
            try:
                onboarding_interface_version = int(onboarding_raw.get("interface_version"))
            except (TypeError, ValueError) as exc:
                raise ProviderManifestError("onboarding.interface_version must be an integer.") from exc
            if onboarding_interface_version != 1:
                raise ProviderManifestError("onboarding.interface_version must be 1 for the current Invio host contract.")
            if runtime_adapter is None:
                raise ProviderManifestError("onboarding requires an executable runtime_adapter.")
            onboarding = OnboardingDeclaration(onboarding_interface_version)
        return ProviderManifest(
            id=provider_id,
            name=name,
            version=version,
            description=description,
            credential_fields=tuple(fields),
            account_modes=modes,
            capabilities=capabilities,
            source_path=path,
            runtime_adapter=runtime_adapter,
            browser_auth=browser_auth,
            onboarding=onboarding,
        )

    def inspect_manifest(self, path: str | Path) -> ProviderManifest:
        """Parse a provider manifest without installing or executing provider code."""
        return self._parse_manifest(Path(path))

    @staticmethod
    def _manifests_equal(left: ProviderManifest, right: ProviderManifest) -> bool:
        return replace(left, source_path=None) == replace(right, source_path=None)

    def package_root(self, provider_id: str) -> Path:
        return self.packages_dir / provider_id.strip().lower()

    def is_imported_package(self, provider_id: str) -> bool:
        return read_ivx_marker(self.package_root(provider_id)) is not None

    def provider_logo_path(self, provider_id: str) -> Path | None:
        package = self.package_root(provider_id)
        if read_ivx_marker(package) is None:
            return None
        logo = package / IVX_LOGO_FILENAME
        return logo if logo.is_file() else None

    def inspect_ivx_manifest(self, path: str | Path) -> ProviderManifest:
        try:
            inspection = inspect_ivx(path)
        except IvxPackageError as exc:
            raise ProviderManifestError(str(exc)) from exc
        self.ivx_staging_dir.mkdir(parents=True, exist_ok=True)
        probe: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".json", prefix=".ivx-manifest-", dir=self.ivx_staging_dir, delete=False
            ) as handle:
                handle.write(inspection.manifest_bytes)
                probe = Path(handle.name)
            manifest = self._parse_manifest(probe)
        finally:
            if probe is not None:
                try:
                    probe.unlink(missing_ok=True)
                except OSError:
                    pass
        if manifest.runtime_adapter is not None and not inspection.has_adapter:
            raise ProviderManifestError("Executable IVX provider package is missing root-level adapter.py.")
        return replace(manifest, source_path=Path(path))

    def import_ivx(self, path: str | Path) -> ProviderManifest:
        """Validate and atomically import an IVX package without executing adapter code."""
        source = Path(path)
        try:
            inspection = inspect_ivx(source)
        except IvxPackageError as exc:
            raise ProviderManifestError(str(exc)) from exc

        candidate = self.inspect_ivx_manifest(source)
        target = self.package_root(candidate.id)
        if target.exists() and read_ivx_marker(target) is None:
            try:
                protected = self._parse_manifest(target / "provider.json")
                protected_name = protected.name
            except Exception:
                protected_name = candidate.id
            raise ProviderManifestError(
                f"Provider ID '{candidate.id}' is reserved by the packaged {protected_name} integration. "
                "IVX import cannot replace built-in provider packages."
            )

        token = uuid.uuid4().hex
        session_root = self.ivx_staging_dir / token
        staged_package = session_root / "package"
        backup = session_root / "rollback"
        moved_old = False
        moved_new = False
        self.ivx_staging_dir.mkdir(parents=True, exist_ok=True)
        try:
            extract_ivx(inspection, staged_package)
            staged_manifest = self._parse_manifest(staged_package / "provider.json")
            if not self._manifests_equal(candidate, staged_manifest):
                raise ProviderManifestError("IVX provider manifest changed while the package was staged; import was cancelled.")
            if staged_manifest.runtime_adapter is not None and not (staged_package / IVX_ADAPTER_FILENAME).is_file():
                raise ProviderManifestError("Executable IVX provider package is missing root-level adapter.py.")
            # Loading an IVX package must never import/execute adapter.py. Existing
            # P13 trusted-code validation remains exclusively at the Install step.
            write_ivx_marker(staged_package, inspection=inspection)

            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                os.replace(target, backup)
                moved_old = True
            os.replace(staged_package, target)
            moved_new = True
        except (ProviderManifestError, IvxPackageError) as exc:
            if moved_old and not moved_new and backup.exists() and not target.exists():
                try:
                    os.replace(backup, target)
                except OSError as rollback_exc:
                    raise ProviderManifestError(
                        f"IVX import failed and the previous package could not be restored safely: {rollback_exc}"
                    ) from exc
            if isinstance(exc, ProviderManifestError):
                raise
            raise ProviderManifestError(str(exc)) from exc
        except OSError as exc:
            try:
                if moved_new and target.exists():
                    shutil.rmtree(target)
                if moved_old and backup.exists():
                    os.replace(backup, target)
            except OSError as rollback_exc:
                raise ProviderManifestError(
                    f"IVX import failed and rollback could not be completed safely: {rollback_exc}"
                ) from exc
            raise ProviderManifestError(f"Could not import IVX provider '{candidate.name}'.") from exc
        finally:
            shutil.rmtree(session_root, ignore_errors=True)
        imported = self._parse_manifest(target / "provider.json")
        return imported

    def _find_package_manifests(self) -> list[Path]:
        if not self.packages_dir.exists():
            return []
        return sorted(self.packages_dir.glob("*/provider.json"))

    def list_available(self) -> list[ProviderManifest]:
        manifests: list[ProviderManifest] = []
        for path in self._find_package_manifests():
            manifests.append(self._parse_manifest(path))
        return manifests

    def list_installed(self) -> list[ProviderManifest]:
        manifests: list[ProviderManifest] = []
        for path in sorted(self.registry_dir.glob("*.json")):
            manifests.append(self._parse_manifest(path))
        return manifests

    def installed_ids(self) -> set[str]:
        return {manifest.id for manifest in self.list_installed()}

    def get_installed(self, provider_id: str) -> ProviderManifest | None:
        wanted = provider_id.strip().lower()
        return next((item for item in self.list_installed() if item.id == wanted), None)

    def get_packaged(self, provider_id: str) -> ProviderManifest | None:
        """Return only a host-shipped packaged manifest, not an imported IVX package.

        Existing runtime/preflight code uses this method to distinguish built-in
        providers from external executable providers. Keeping imported IVX
        packages out of this result preserves that frozen execution boundary.
        """
        wanted = provider_id.strip().lower()
        item = next((entry for entry in self.list_available() if entry.id == wanted), None)
        if item is None or self.is_imported_package(wanted):
            return None
        return item

    def get_available(self, provider_id: str) -> ProviderManifest | None:
        wanted = provider_id.strip().lower()
        return next((item for item in self.list_available() if item.id == wanted), None)

    def install_packaged(
        self,
        provider_id: str,
        *,
        allow_executable: bool = False,
        adapter_validator=None,
    ) -> ProviderManifest:
        manifest = self.get_available(provider_id)
        if manifest is None or manifest.source_path is None:
            raise ProviderManifestError(f"Provider package '{provider_id}' was not found.")
        if self.is_imported_package(manifest.id):
            return self.load_external(
                manifest.source_path,
                allow_executable=allow_executable,
                adapter_validator=adapter_validator,
            )
        target = self.registry_dir / f"{manifest.id}.json"
        shutil.copyfile(manifest.source_path, target)
        return self._parse_manifest(target)

    def external_adapter_path(self, provider_id: str) -> Path:
        return self.registry_dir / f"{provider_id.strip().lower()}_adapter.py"

    def load_external(
        self,
        path: str | Path,
        *,
        allow_executable: bool = False,
        adapter_validator=None,
    ) -> ProviderManifest:
        source = Path(path)
        manifest = self._parse_manifest(source)
        packaged = self.get_packaged(manifest.id)
        if packaged is not None:
            raise ProviderManifestError(
                f"Provider ID '{manifest.id}' is reserved by the packaged {packaged.name} integration. "
                f"Install the packaged provider instead."
            )

        adapter_source: Path | None = None
        if manifest.runtime_adapter is not None:
            if not allow_executable:
                raise ProviderManifestError(
                    "This provider declares executable adapter code. Explicit trusted-code approval is required before loading it."
                )
            adapter_source = source.with_name("adapter.py")
            if not adapter_source.is_file():
                raise ProviderManifestError("Executable provider bundle is missing sibling adapter.py.")
            if adapter_validator is None:
                raise ProviderManifestError("Executable provider adapter validation is unavailable.")

        target_manifest = self.registry_dir / f"{manifest.id}.json"
        target_adapter = self.external_adapter_path(manifest.id)
        token = uuid.uuid4().hex
        staged_manifest = self.registry_dir / f".{manifest.id}.{token}.json.tmp"
        # Keep a Python filename suffix while staging so the exact bytes that
        # will be installed can be imported/validated before registry replace.
        staged_adapter = self.registry_dir / f".{manifest.id}.{token}_adapter.py"
        backup_manifest = self.registry_dir / f".{manifest.id}.{token}.json.rollback"
        backup_adapter = self.registry_dir / f".{manifest.id}.{token}.adapter.rollback"
        had_manifest = target_manifest.exists()
        had_adapter = target_adapter.exists()
        try:
            shutil.copyfile(source, staged_manifest)
            staged = self._parse_manifest(staged_manifest)
            if (
                staged.id != manifest.id
                or staged.name != manifest.name
                or staged.version != manifest.version
                or staged.description != manifest.description
                or staged.credential_fields != manifest.credential_fields
                or staged.account_modes != manifest.account_modes
                or staged.capabilities != manifest.capabilities
                or staged.runtime_adapter != manifest.runtime_adapter
                or staged.browser_auth != manifest.browser_auth
                or staged.onboarding != manifest.onboarding
            ):
                raise ProviderManifestError("Provider manifest changed while it was being staged; load was cancelled.")
            staged_packaged = self.get_packaged(staged.id)
            if staged_packaged is not None:
                raise ProviderManifestError(
                    f"Provider ID '{staged.id}' is reserved by the packaged {staged_packaged.name} integration. "
                    f"Install the packaged provider instead."
                )

            if adapter_source is not None:
                shutil.copyfile(adapter_source, staged_adapter)
                staged_manifest_bytes = staged_manifest.read_bytes()
                staged_adapter_bytes = staged_adapter.read_bytes()
                try:
                    adapter_validator(staged, staged_adapter)
                except ProviderManifestError:
                    raise
                except Exception as exc:
                    raise ProviderManifestError(f"External provider adapter is incompatible: {exc}") from exc
                if (
                    staged_manifest.read_bytes() != staged_manifest_bytes
                    or staged_adapter.read_bytes() != staged_adapter_bytes
                ):
                    raise ProviderManifestError(
                        "External provider staged manifest/adapter changed during validation; load was cancelled."
                    )

            if had_manifest:
                shutil.copyfile(target_manifest, backup_manifest)
            if had_adapter:
                shutil.copyfile(target_adapter, backup_adapter)

            if adapter_source is not None:
                os.replace(staged_adapter, target_adapter)
            elif target_adapter.exists():
                target_adapter.unlink()
            os.replace(staged_manifest, target_manifest)
        except ProviderManifestError:
            raise
        except OSError as exc:
            try:
                if backup_manifest.exists():
                    os.replace(backup_manifest, target_manifest)
                elif not had_manifest:
                    target_manifest.unlink(missing_ok=True)
                if backup_adapter.exists():
                    os.replace(backup_adapter, target_adapter)
                elif not had_adapter:
                    target_adapter.unlink(missing_ok=True)
            except OSError as rollback_exc:
                raise ProviderManifestError(
                    f"External provider installation failed and rollback could not be completed safely: {rollback_exc}"
                ) from exc
            raise ProviderManifestError(f"Could not load external provider '{manifest.name}'.") from exc
        finally:
            for temporary in (staged_manifest, staged_adapter, backup_manifest, backup_adapter):
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
        return self._parse_manifest(target_manifest)

    def uninstall(self, provider_id: str) -> ProviderManifest:
        manifest = self.get_installed(provider_id)
        if manifest is None:
            raise ProviderManifestError(f"Provider '{provider_id}' is not installed.")
        target = self.registry_dir / f"{manifest.id}.json"
        adapter = self.external_adapter_path(manifest.id)
        external = self.get_packaged(manifest.id) is None
        token = uuid.uuid4().hex
        staged_manifest = self.registry_dir / f".{manifest.id}.{token}.uninstall.json.tmp"
        staged_adapter = self.registry_dir / f".{manifest.id}.{token}.uninstall_adapter.py.tmp"
        manifest_moved = False
        adapter_moved = False
        try:
            os.replace(target, staged_manifest)
            manifest_moved = True
            if external and adapter.exists():
                os.replace(adapter, staged_adapter)
                adapter_moved = True
        except OSError as exc:
            try:
                if adapter_moved and staged_adapter.exists():
                    os.replace(staged_adapter, adapter)
                if manifest_moved and staged_manifest.exists():
                    os.replace(staged_manifest, target)
            except OSError as rollback_exc:
                raise ProviderManifestError(
                    f"Could not uninstall provider '{manifest.name}', and rollback could not be completed safely: "
                    f"{rollback_exc}"
                ) from exc
            raise ProviderManifestError(f"Could not uninstall provider '{manifest.name}'.") from exc
        finally:
            # Once both active registry names have been moved away successfully,
            # cleanup is best-effort. A transient filesystem lock must not turn
            # a completed logical uninstall into a half-installed provider.
            for temporary in (staged_adapter, staged_manifest):
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
        return manifest
