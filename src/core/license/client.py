from __future__ import annotations

import json
import ssl
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from ..storage import CredentialStore, CredentialStoreError

try:
    import truststore as _truststore
except ImportError:  # pragma: no cover - required dependency is verified by distribution/Windows gates
    _truststore = None

DEFAULT_LICENSE_BASE_URL = "https://invio.vib.tools"
CLIENT_VERSION = "1.0.0.1.50.1"
USER_AGENT = f"Invio/{CLIENT_VERSION} Vib-Tools"
_REQUEST_TIMEOUT = 20.0
_HWID_ACCOUNT_ID = "license-device-id"

# Invio license server's RSA public key (invio.vib.tools). Signed activation/
# validation payloads are verified against this key before Invio trusts them,
# so a compromised or spoofed network path cannot forge a valid license.
INVIO_LICENSE_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwGEz9s8ClgO5fTcwAaMe
CTt1kCqg3YTyeg5GXwsFh6j7DtvaMAscHeht5mQvKGEiITEK4BeA1oZWIf8+OKfV
/M1AwDeqaWTPlJlO4h2x5HFJJPQpTJXZ5+03Zj3zAhRVGphTrvbQw0fIKkB6G1c7
lbthOQzttDg5l5bBOt/BDepXddcUELgz9fBVS83lGkVrVbqgsJIWZS0+bsJS5+ML
IKivKZ6CH/MgJhqrrRVqmJlsU3opaR15+KKps6hhNL3ZIO0zcu0HHKFuqEtWbAfo
CKf/cS06G1sQfXRvNKlHnYK1eDjQ7xHGWP9MycAqUMXjUxS8wjcOa8SKpw1gHRs4
WQIDAQAB
-----END PUBLIC KEY-----
"""


class LicenseError(Exception):
    """Raised when a license request fails or a server response cannot be trusted."""

    def __init__(
        self, message: str, *, allowed_providers: tuple[str, ...] = (), network_error: bool = False,
    ) -> None:
        super().__init__(message)
        self.allowed_providers = allowed_providers
        # True only when the server could not be reached at all (DNS/timeout/TLS/connection
        # failure). Callers use this to distinguish "inconclusive, try again later" from an
        # explicit server rejection (banned/expired/hwid mismatch/not found), so a routine
        # offline re-check never revokes a still-valid cached license just because the
        # network was briefly unavailable.
        self.network_error = network_error


@dataclass(frozen=True, slots=True)
class LicenseRecord:
    license_key: str
    provider_id: str
    status: str
    hwid: str
    expires_at: str
    payload_json: str
    signature: str


def _windows_native_tls_context() -> ssl.SSLContext | None:
    if sys.platform != "win32" or _truststore is None:
        return None
    context = _truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    return context


def get_or_create_device_id() -> str:
    """Return a stable per-installation device identifier used as the license HWID.

    Rather than fingerprinting physical hardware (MAC address, disk serial, etc. -
    all spoofable and platform-specific), Invio generates a random identifier once
    and persists it in the same OS-protected keyring backend used for account
    credentials. This is stable across restarts for a given OS user profile.
    """
    store = CredentialStore()
    reference = store.credential_ref(_HWID_ACCOUNT_ID)
    try:
        existing = store.get_credentials(reference)
    except CredentialStoreError:
        existing = None
    if existing and existing.get("device_id"):
        return existing["device_id"]
    device_id = uuid.uuid4().hex
    try:
        store.set_credentials(_HWID_ACCOUNT_ID, {"device_id": device_id})
    except CredentialStoreError as exc:
        raise LicenseError("A device identifier could not be saved to protected storage.") from exc
    return device_id


def _load_public_key() -> RSAPublicKey:
    key = serialization.load_pem_public_key(INVIO_LICENSE_PUBLIC_KEY_PEM.encode("ascii"))
    if not isinstance(key, RSAPublicKey):
        raise LicenseError("Invio license public key is not an RSA key.")
    return key


def _canonical_payload_bytes(payload: dict[str, object]) -> bytes:
    # Must byte-for-byte match the server's JSON.stringify(payload, Object.keys(payload).sort()):
    # alphabetically-sorted keys, no extra whitespace.
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_signature(payload: dict[str, object], signature_b64: str) -> bool:
    import base64

    try:
        signature = base64.b64decode(signature_b64, validate=True)
    except (ValueError, TypeError):
        return False
    try:
        _load_public_key().verify(
            signature,
            _canonical_payload_bytes(payload),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except InvalidSignature:
        return False
    except Exception:
        return False
    return True


def _post_json(url: str, body: dict[str, object]) -> tuple[int, dict[str, object]]:
    if not url.casefold().startswith("https://"):
        raise LicenseError("Refusing to contact a non-HTTPS license server URL.")
    data = json.dumps(body).encode("utf-8")
    request = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "X-Invio-Client-Version": CLIENT_VERSION,
            "X-Invio-Hwid": str(body.get("hwid", "")),
        },
    )
    context = _windows_native_tls_context()
    try:
        opener = (lambda: urlopen(request, timeout=_REQUEST_TIMEOUT, context=context)) if context is not None \
            else (lambda: urlopen(request, timeout=_REQUEST_TIMEOUT))
        with opener() as response:  # noqa: S310 - HTTPS-only, verified above
            raw = response.read()
            status = response.status
    except HTTPError as exc:
        raw = exc.read()
        status = exc.code
    except URLError as exc:
        raise LicenseError(f"Could not reach the license server: {exc.reason}", network_error=True) from exc
    except (TimeoutError, ssl.SSLError) as exc:
        raise LicenseError(f"License server request failed: {exc}", network_error=True) from exc
    try:
        parsed = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LicenseError("License server returned an invalid response.") from exc
    if not isinstance(parsed, dict):
        raise LicenseError("License server returned an unexpected response.")
    return status, parsed


def _raise_for_error(status: int, parsed: dict[str, object]) -> None:
    message = str(parsed.get("error") or f"License server request failed (HTTP {status}).")
    allowed = parsed.get("allowed_providers")
    allowed_tuple = tuple(str(item) for item in allowed) if isinstance(allowed, list) else ()
    raise LicenseError(message, allowed_providers=allowed_tuple)


def activate_license(
    license_key: str,
    provider_id: str,
    *,
    base_url: str = DEFAULT_LICENSE_BASE_URL,
) -> LicenseRecord:
    """Activate a license key for a specific provider against the Invio license server.

    Raises LicenseError on any failure (not found, expired, banned, wrong provider,
    device mismatch, network failure, or a response whose signature does not verify).
    """
    device_id = get_or_create_device_id()
    status, parsed = _post_json(
        f"{base_url.rstrip('/')}/api/activate",
        {"license_key": license_key.strip(), "plugin_slug": provider_id.strip(), "hwid": device_id},
    )
    if status != 200 or not parsed.get("success"):
        _raise_for_error(status, parsed)

    payload = parsed.get("data")
    signature = parsed.get("signature")
    if not isinstance(payload, dict) or not isinstance(signature, str) or not signature:
        raise LicenseError("License server response was missing its signed payload.")
    if not verify_signature(payload, signature):
        raise LicenseError("License server response failed signature verification and cannot be trusted.")

    record = LicenseRecord(
        license_key=str(payload.get("license_key", license_key)),
        provider_id=provider_id,
        status=str(payload.get("status", "")),
        hwid=str(payload.get("hwid", device_id)),
        expires_at=str(payload.get("expires_at", "")),
        payload_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
        signature=signature,
    )
    _store_local_license(record)
    return record


def validate_license(
    license_key: str,
    hwid: str,
    *,
    base_url: str = DEFAULT_LICENSE_BASE_URL,
) -> LicenseRecord:
    """Re-check a license key's current status against the license server.

    Unlike `is_provider_licensed`, this always makes a network call, so it is how an
    admin-side ban/expiry/HWID-reset ever reaches an already-activated desktop. Raises
    LicenseError on any failure; `LicenseError.network_error` is True only when the
    server could not be reached at all (see LicenseError), False when the server
    explicitly rejected the license or the response could not be trusted.
    """
    status, parsed = _post_json(
        f"{base_url.rstrip('/')}/api/validate",
        {"license_key": license_key.strip(), "hwid": hwid},
    )
    if status != 200 or not parsed.get("success"):
        _raise_for_error(status, parsed)

    payload = parsed.get("data")
    signature = parsed.get("signature")
    if not isinstance(payload, dict) or not isinstance(signature, str) or not signature:
        raise LicenseError("License server response was missing its signed payload.")
    if not verify_signature(payload, signature):
        raise LicenseError("License server response failed signature verification and cannot be trusted.")

    return LicenseRecord(
        license_key=str(payload.get("license_key", license_key)),
        provider_id="",
        status=str(payload.get("status", "")),
        hwid=str(payload.get("hwid", hwid)),
        expires_at=str(payload.get("expires_at", "")),
        payload_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
        signature=signature,
    )


def revalidate_license(provider_id: str, *, base_url: str = DEFAULT_LICENSE_BASE_URL) -> bool:
    """Re-check the locally cached license for `provider_id` against the license server.

    This is what propagates an admin-side ban/expiry/HWID reset to an already-activated
    desktop: `is_provider_licensed` alone never touches the network, so without a
    periodic call to this function a revoked license would keep working locally forever.

    - No local license cached: returns False immediately (no network call).
    - Server reachable and confirms the license: local cache is refreshed with the
      latest signed payload (picks up any extended/changed expiry too) and this
      returns the freshly-computed `is_provider_licensed` result.
    - Server reachable but explicitly rejects the license (banned, expired, not found,
      HWID no longer matches) or returns an untrustworthy response: the local cache is
      cleared and this returns False.
    - Server unreachable (network_error): the local cache is left untouched (fail open
      on connectivity so Invio remains usable offline between periodic re-checks) and
      this returns whatever `is_provider_licensed` currently reports.
    """
    record = get_local_license(provider_id)
    if record is None:
        return False
    try:
        fresh = validate_license(record.license_key, record.hwid, base_url=base_url)
    except LicenseError as exc:
        if exc.network_error:
            return is_provider_licensed(provider_id)
        clear_local_license(provider_id)
        return False
    _store_local_license(
        LicenseRecord(
            license_key=fresh.license_key,
            provider_id=provider_id,
            status=fresh.status,
            hwid=fresh.hwid,
            expires_at=fresh.expires_at,
            payload_json=fresh.payload_json,
            signature=fresh.signature,
        )
    )
    return is_provider_licensed(provider_id)


def get_local_license(provider_id: str) -> LicenseRecord | None:
    store = CredentialStore()
    reference = store.credential_ref(_license_account_id(provider_id))
    try:
        data = store.get_credentials(reference)
    except CredentialStoreError:
        return None
    if not data:
        return None
    try:
        payload = json.loads(data.get("payload_json", "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or not verify_signature(payload, data.get("signature", "")):
        return None
    return LicenseRecord(
        license_key=data.get("license_key", ""),
        provider_id=provider_id,
        status=data.get("status", ""),
        hwid=data.get("hwid", ""),
        expires_at=data.get("expires_at", ""),
        payload_json=data.get("payload_json", "{}"),
        signature=data.get("signature", ""),
    )


def is_provider_licensed(provider_id: str) -> bool:
    """Whether ``provider_id`` currently has a locally-verified, unexpired, active license.

    This is a purely local/offline check (no network call): it re-verifies the
    signed payload saved at activation time against the embedded public key,
    and checks that payload's own expires_at against the current time. It is
    the single gate `ExternalAdapterRegistry` uses to decide whether an
    externally-installed provider's adapter is allowed to register as
    executable - an unlicensed provider is treated exactly like a missing or
    incompatible adapter (usable by nothing: not Accounts, not Tasks).
    """
    record = get_local_license(provider_id)
    if record is None or record.status != "active":
        return False
    try:
        expires_at = datetime.fromisoformat(record.expires_at.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)


def clear_local_license(provider_id: str) -> None:
    store = CredentialStore()
    reference = store.credential_ref(_license_account_id(provider_id))
    try:
        store.delete_credentials(reference, missing_ok=True)
    except CredentialStoreError:
        pass


def _license_account_id(provider_id: str) -> str:
    return f"license:{provider_id.strip().lower()}"


def _store_local_license(record: LicenseRecord) -> None:
    store = CredentialStore()
    try:
        store.set_credentials(
            _license_account_id(record.provider_id),
            {
                "license_key": record.license_key,
                "status": record.status,
                "hwid": record.hwid,
                "expires_at": record.expires_at,
                "payload_json": record.payload_json,
                "signature": record.signature,
            },
        )
    except CredentialStoreError as exc:
        raise LicenseError("The activated license could not be saved to protected storage.") from exc
