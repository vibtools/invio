from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("P14 Windows native smoke must run on Windows.")

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    temp_root = Path(tempfile.mkdtemp(prefix="invio-p14-win-"))
    os.environ["APPDATA"] = str(temp_root / "appdata")

    from PySide6.QtWidgets import QApplication

    from src.core.paths import application_root, validate_runtime_resources
    from src.core.provider_manager import ProviderManager
    from src.core.provider_runtime.runtime import _windows_native_tls_context
    from src.core.storage import CredentialStore
    from src.core.worker_manager import WorkerManager
    from src.tasks.models import Task
    from src.ui.main_window import MainWindow
    from src.ui.tokens import NAV_ITEMS

    validate_runtime_resources()
    root = application_root()
    if os.environ.get("INVIO_P14_EXPECT_INSTALLED") == "1" and "site-packages" not in root.as_posix().lower():
        raise SystemExit(f"Expected installed-wheel resource root, got {root}")
    import ssl

    tls_context = _windows_native_tls_context()
    if tls_context.verify_mode != ssl.CERT_REQUIRED or not tls_context.check_hostname:
        raise SystemExit("Windows native TLS trust context is not fail-closed.")
    if tls_context.__class__.__module__.split(".", 1)[0] != "truststore":
        raise SystemExit(f"Unexpected Windows TLS backend: {tls_context.__class__.__module__}")

    manager = ProviderManager(root)
    packaged = {item.id for item in manager.list_available()}
    if packaged != {"stripe", "refrens", "agiled"}:
        raise SystemExit(f"Unexpected packaged providers: {sorted(packaged)}")

    store = CredentialStore()
    account_id = "p14-native-" + uuid.uuid4().hex
    reference = store.set_credentials(account_id, {"secret_key": "p14-native-secret"})
    try:
        if store.get_credentials(reference) != {"secret_key": "p14-native-secret"}:
            raise SystemExit("Windows protected-keyring round trip failed.")
    finally:
        store.delete_credentials(reference, missing_ok=True)

    app = QApplication.instance() or QApplication([])

    # Native WorkerManager smoke: prove three active Tasks own three distinct QThreads.
    import threading
    import time
    from PySide6.QtCore import QEventLoop, QTimer

    worker_manager = WorkerManager()
    started_threads: set[int] = set()
    start_lock = threading.Lock()
    release = threading.Event()
    finished: set[str] = set()

    def runner(context):
        with start_lock:
            started_threads.add(threading.get_ident())
        if not release.wait(10):
            raise RuntimeError("P14 concurrency release timeout")

    tasks = [
        Task(id=f"p14-native-{index}", name=f"Native {index}", provider_id="stripe", provider_name="Stripe", account_ids=[], customer_list_id="", customer_list_name="")
        for index in range(3)
    ]
    worker_manager.finished.connect(lambda task_id, _status: finished.add(task_id))
    for task in tasks:
        worker_manager.start(task, runner)

    loop = QEventLoop()
    poll = QTimer()
    poll.setInterval(20)
    def poll_workers():
        if len(started_threads) == 3:
            release.set()
        if len(finished) == 3:
            loop.quit()
    poll.timeout.connect(poll_workers)
    poll.start()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)
    timeout.start(15000)
    loop.exec()
    poll.stop()
    if len(started_threads) != 3 or len(finished) != 3:
        raise SystemExit(f"Three-Task native QThread smoke failed: threads={len(started_threads)}, finished={len(finished)}")

    window = MainWindow(root)
    try:
        expected = [name for name, _icon in NAV_ITEMS]
        if list(window.pages) != expected:
            raise SystemExit(f"Unexpected page inventory: {list(window.pages)}")
        for name in expected:
            window.navigate(name)
            app.processEvents()
    finally:
        window.close()
        app.processEvents()
    print("P14 Windows native PySide6/keyring/resource smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
