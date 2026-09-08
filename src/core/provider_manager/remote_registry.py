from __future__ import annotations

import hashlib
import json
import ssl
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import truststore as _truststore
except ImportError:  # pragma: no cover - required dependency is verified by distribution/Windows gates
    _truststore = None

DEFAULT_REGISTRY_BASE_URL = "https://invio.vib.tools"
_REQUEST_TIMEOUT = 20.0
_USER_AGENT = "Invio-Desktop-ProviderClient/1.0"


class RemoteRegistryError(Exception):
    """Raised when the online provider catalog cannot be fetched or a download is invalid."""


@dataclass(frozen=True, slots=True)
class RemoteProviderInfo:
    remote_id: int
    slug: str
    name: str
    version: str
    description: str
    author: str
    category: str
    download_url: str
    sha256: str | None
    logo_data_url: str | None = None


def _windows_native_tls_context() -> ssl.SSLContext | None:
    """Mirror ProviderRuntime's Windows-native TLS trust so registry HTTPS calls verify against the OS cert store."""
    if sys.platform != "win32" or _truststore is None:
        return None
    context = _truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    return context


def _get(url: str) -> bytes:
    if not url.casefold().startswith("https://"):
        raise RemoteRegistryError("Refusing to fetch a non-HTTPS provider registry URL.")
    request = Request(url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"})
    context = _windows_native_tls_context()
    try:
        if context is not None:
            with urlopen(request, timeout=_REQUEST_TIMEOUT, context=context) as response:  # noqa: S310 - HTTPS-only, verified above
                return response.read()
        with urlopen(request, timeout=_REQUEST_TIMEOUT) as response:  # noqa: S310 - HTTPS-only, verified above
            return response.read()
    except HTTPError as exc:
        raise RemoteRegistryError(f"Provider registry request failed ({exc.code}): {url}") from exc
    except URLError as exc:
        raise RemoteRegistryError(f"Could not reach the provider registry: {exc.reason}") from exc
    except (TimeoutError, ssl.SSLError) as exc:
        raise RemoteRegistryError(f"Provider registry request failed: {exc}") from exc


def fetch_catalog(base_url: str = DEFAULT_REGISTRY_BASE_URL) -> list[RemoteProviderInfo]:
    """Fetch the public provider catalog from the Invio website."""
    raw = _get(f"{base_url.rstrip('/')}/api/providers/public")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RemoteRegistryError("Provider registry returned an invalid response.") from exc

    items = payload.get("providers") or payload.get("plugins") or []
    if not isinstance(items, list):
        raise RemoteRegistryError("Provider registry returned an unexpected response shape.")

    catalog: list[RemoteProviderInfo] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("downloadUrl"):
            continue
        try:
            remote_id = int(item.get("id"))
        except (TypeError, ValueError):
            continue
        slug = str(item.get("slug", "")).strip()
        name = str(item.get("name", "")).strip()
        if not slug or not name:
            continue
        sha256 = item.get("zipSha256")
        catalog.append(
            RemoteProviderInfo(
                remote_id=remote_id,
                slug=slug,
                name=name,
                version=str(item.get("version") or "1.0.0").strip(),
                description=str(item.get("description") or "").strip(),
                author=str(item.get("author") or "").strip(),
                category=str(item.get("category") or "").strip(),
                download_url=str(item["downloadUrl"]),
                sha256=str(sha256).strip().lower() if sha256 else None,
                logo_data_url=_valid_logo_data_url(item.get("logoData")),
            )
        )
    return catalog


_MAX_LOGO_DATA_URL_LENGTH = 4 * 1024 * 1024  # ~3MB decoded; guards against a hostile/broken registry response


def _valid_logo_data_url(value: object) -> str | None:
    if not isinstance(value, str) or not value.startswith("data:image/"):
        return None
    if len(value) > _MAX_LOGO_DATA_URL_LENGTH:
        return None
    return value


def download_provider(
    info: RemoteProviderInfo, dest_dir: Path, base_url: str = DEFAULT_REGISTRY_BASE_URL
) -> Path:
    """Download a provider package to ``dest_dir``, verifying its checksum when the registry supplied one.

    Returns the path to the downloaded ``.ivx`` file. The caller is responsible for feeding it
    through ``ProviderManager.import_ivx``/``install_packaged`` for validation and installation.
    """
    url = info.download_url
    if url.startswith("/"):
        url = f"{base_url.rstrip('/')}{url}"
    data = _get(url)

    if info.sha256:
        digest = hashlib.sha256(data).hexdigest()
        if digest.lower() != info.sha256:
            raise RemoteRegistryError(
                f"Downloaded package for '{info.name}' failed integrity verification (checksum mismatch)."
            )

    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in info.slug.casefold()) or "provider"
    safe_version = "".join(ch if ch.isalnum() or ch in ".-_" else "-" for ch in info.version) or "0.0.0"
    target = dest_dir / f"{safe_slug}-{safe_version}.ivx"
    target.write_bytes(data)
    return target
