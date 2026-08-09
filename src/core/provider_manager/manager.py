from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

_PROVIDER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")


@dataclass(frozen=True, slots=True)
class CredentialField:
    key: str
    label: str
    kind: str = "text"
    required: bool = True
    placeholder: str = ""


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


class ProviderManifestError(ValueError):
    pass


class ProviderManager:
    """Manifest-driven provider package and installation-state manager.

    This manager never imports or executes provider code. Installation means a
    validated manifest is copied to ``providers/registry``. Provider execution
    remains isolated behind separately registered task runners.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.packages_dir = self.project_root / "providers" / "packages"
        self.registry_dir = self.project_root / "providers" / "registry"
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
            if not key or not label or kind not in {"text", "password"}:
                raise ProviderManifestError("Credential fields require key, label and a text/password kind.")
            fields.append(
                CredentialField(
                    key=key,
                    label=label,
                    kind=kind,
                    required=bool(item.get("required", True)),
                    placeholder=str(item.get("placeholder", "")),
                )
            )

        modes = tuple(str(value).strip() for value in raw.get("account_modes", []) if str(value).strip())
        capabilities = tuple(str(value).strip() for value in raw.get("capabilities", []) if str(value).strip())
        return ProviderManifest(
            id=provider_id,
            name=name,
            version=version,
            description=description,
            credential_fields=tuple(fields),
            account_modes=modes,
            capabilities=capabilities,
            source_path=path,
        )

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
        """Return the canonical packaged manifest for a provider ID, if present."""
        wanted = provider_id.strip().lower()
        return next((item for item in self.list_available() if item.id == wanted), None)

    def install_packaged(self, provider_id: str) -> ProviderManifest:
        manifest = next((item for item in self.list_available() if item.id == provider_id), None)
        if manifest is None or manifest.source_path is None:
            raise ProviderManifestError(f"Provider package '{provider_id}' was not found.")
        target = self.registry_dir / f"{manifest.id}.json"
        shutil.copyfile(manifest.source_path, target)
        return self._parse_manifest(target)

    def load_external(self, path: str | Path) -> ProviderManifest:
        source = Path(path)
        manifest = self._parse_manifest(source)
        packaged = self.get_packaged(manifest.id)
        if packaged is not None:
            raise ProviderManifestError(
                f"Provider ID '{manifest.id}' is reserved by the packaged {packaged.name} integration. "
                f"Install the packaged provider instead."
            )
        target = self.registry_dir / f"{manifest.id}.json"
        shutil.copyfile(source, target)
        return self._parse_manifest(target)

    def uninstall(self, provider_id: str) -> ProviderManifest:
        manifest = self.get_installed(provider_id)
        if manifest is None:
            raise ProviderManifestError(f"Provider '{provider_id}' is not installed.")
        target = self.registry_dir / f"{manifest.id}.json"
        try:
            target.unlink()
        except OSError as exc:
            raise ProviderManifestError(f"Could not uninstall provider '{manifest.name}'.") from exc
        return manifest
