from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from .core.paths import RuntimeResourceError, application_root, asset_path, validate_runtime_resources
from .core.storage import CredentialStore, CredentialStoreError, DomainStoreError
from .ui.dialogs import compact_message_box
from .ui.main_window import MainWindow
from .ui.styles import app_qss


def project_root() -> Path:
    return application_root()


def _set_windows_app_user_model_id() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VibTools.Invio")
    except Exception:
        # Window/executable icons still work when Windows does not expose the API.
        return


def _application_icon() -> QIcon:
    for filename in ("app.png", "app.ico"):
        path = asset_path("icons", filename)
        if path.is_file():
            icon = QIcon(str(path))
            if not icon.isNull():
                return icon
    return QIcon()


def _run_p14_compiled_credential_smoke() -> int | None:
    """Exercise the production CredentialStore only for the explicit P14 build smoke."""
    if os.environ.get("INVIO_P14_COMPILED_CREDENTIAL_SMOKE") != "1":
        return None

    store = CredentialStore()
    account_id = f"p14-compiled-{uuid.uuid4().hex}"
    expected = {"secret_key": "p14-compiled-secret"}
    reference: str | None = None
    result = 0
    try:
        reference = store.set_credentials(account_id, expected)
        if store.get_credentials(reference) != expected:
            result = 87
    except CredentialStoreError:
        result = 86
    finally:
        if reference is not None:
            try:
                store.delete_credentials(reference, missing_ok=True)
            except CredentialStoreError:
                result = 88
    return result


def _run_p14_compiled_tls_smoke() -> int | None:
    """Verify the packaged Windows TLS backend without making a network request."""
    if os.environ.get("INVIO_P14_COMPILED_TLS_SMOKE") != "1":
        return None
    if sys.platform != "win32":
        return 89
    import ssl

    from .core.provider_runtime.runtime import ProviderRuntimeError, _windows_native_tls_context

    try:
        context = _windows_native_tls_context()
    except ProviderRuntimeError:
        return 90
    if context.verify_mode != ssl.CERT_REQUIRED:
        return 91
    if not context.check_hostname:
        return 92
    if context.__class__.__module__.split(".", 1)[0] != "truststore":
        return 93
    return 0


def main() -> int:
    credential_smoke = _run_p14_compiled_credential_smoke()
    if credential_smoke is not None:
        return credential_smoke
    tls_smoke = _run_p14_compiled_tls_smoke()
    if tls_smoke is not None:
        return tls_smoke

    _set_windows_app_user_model_id()
    app = QApplication(sys.argv)
    app.setApplicationName("Invio")
    app.setOrganizationName("Vib Tools")
    app.setStyle("Fusion")
    app.setStyleSheet(app_qss())
    icon = _application_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    try:
        validate_runtime_resources()
        window = MainWindow(project_root())
    except DomainStoreError as exc:
        compact_message_box(
            None,
            "Invio Operational Storage",
            f"Invio could not start because its operational storage is unavailable or unsafe to use. No operational database was overwritten.\n\n{exc}",
            icon=QMessageBox.Icon.Critical,
        )
        return 1
    except RuntimeResourceError as exc:
        compact_message_box(None, "Invio Runtime Resources", str(exc), icon=QMessageBox.Icon.Critical)
        return 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
