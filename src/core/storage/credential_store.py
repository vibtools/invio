from __future__ import annotations

import json
from typing import Any, Protocol

SERVICE_NAME = "Vib Tools Invio"
ACCOUNT_USERNAME_PREFIX = "account:"


class CredentialStoreError(RuntimeError):
    """Raised when protected provider credentials cannot be stored or read safely."""


class CredentialStoreUnavailable(CredentialStoreError):
    """Raised when no usable protected OS credential backend is available."""


class _KeyringLike(Protocol):
    def get_password(self, service_name: str, username: str) -> str | None: ...

    def set_password(self, service_name: str, username: str, password: str) -> None: ...

    def delete_password(self, service_name: str, username: str) -> None: ...


class CredentialStore:
    """Store provider credentials only in an OS-protected keyring backend.

    The normal domain database stores only an opaque credential reference. This
    class intentionally has no plaintext-file fallback.
    """

    def __init__(self, backend: _KeyringLike | None = None) -> None:
        self._backend = backend

    @staticmethod
    def credential_ref(account_id: str) -> str:
        return f"{ACCOUNT_USERNAME_PREFIX}{account_id}"

    @classmethod
    def _is_approved_os_backend(cls, backend: object) -> bool:
        module_name = backend.__class__.__module__
        class_name = backend.__class__.__name__
        qualified = f"{module_name}.{class_name}"
        approved = {
            "keyring.backends.Windows.WinVaultKeyring",
            "keyring.backends.macOS.Keyring",
            "keyring.backends.kwallet.DBusKeyring",
            "keyring.backends.SecretService.Keyring",
            "keyring.backends.libsecret.Keyring",
        }
        if qualified in approved:
            return True
        if qualified == "keyring.backends.chainer.ChainerBackend":
            try:
                chained = list(getattr(backend, "backends"))
            except Exception:
                return False
            return bool(chained) and all(cls._is_approved_os_backend(item) for item in chained)
        return False

    def _keyring(self) -> _KeyringLike:
        if self._backend is not None:
            return self._backend
        try:
            import keyring
            from keyring.errors import KeyringError
        except Exception as exc:  # dependency/import failure must fail closed
            raise CredentialStoreUnavailable("Protected credential storage is unavailable.") from exc

        try:
            backend = keyring.get_keyring()
            priority = float(getattr(backend, "priority", 0))
            if priority <= 0 or not self._is_approved_os_backend(backend):
                raise CredentialStoreUnavailable("No approved OS-protected credential backend is available.")
        except CredentialStoreUnavailable:
            raise
        except KeyringError as exc:
            raise CredentialStoreUnavailable("Protected credential storage could not be initialized.") from exc
        except Exception as exc:
            raise CredentialStoreUnavailable("Protected credential storage could not be initialized.") from exc
        return keyring

    def set_credentials(self, account_id: str, credentials: dict[str, str]) -> str:
        reference = self.credential_ref(account_id)
        payload = json.dumps({str(key): str(value) for key, value in credentials.items()}, sort_keys=True, separators=(",", ":"))
        backend = self._keyring()
        try:
            backend.set_password(SERVICE_NAME, reference, payload)
        except Exception as exc:
            raise CredentialStoreError("Provider credentials could not be saved to protected storage.") from exc
        return reference

    def get_credentials(self, reference: str) -> dict[str, str] | None:
        backend = self._keyring()
        try:
            payload = backend.get_password(SERVICE_NAME, reference)
        except Exception as exc:
            raise CredentialStoreError("Provider credentials could not be read from protected storage.") from exc
        if payload is None:
            return None
        try:
            decoded: Any = json.loads(payload)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CredentialStoreError("Protected provider credentials are unreadable.") from exc
        if not isinstance(decoded, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in decoded.items()):
            raise CredentialStoreError("Protected provider credentials have an invalid format.")
        return dict(decoded)

    def delete_credentials(self, reference: str, *, missing_ok: bool = True) -> None:
        backend = self._keyring()
        try:
            backend.delete_password(SERVICE_NAME, reference)
        except Exception as exc:
            if missing_ok and exc.__class__.__name__ == "PasswordDeleteError":
                return
            raise CredentialStoreError("Provider credentials could not be removed from protected storage.") from exc
