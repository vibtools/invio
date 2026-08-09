from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from .core.storage import DomainStoreError
from .ui.main_window import MainWindow


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Invio")
    app.setOrganizationName("Vib Tools")
    app.setStyle("Fusion")
    try:
        window = MainWindow(project_root())
    except DomainStoreError as exc:
        QMessageBox.critical(
            None,
            "Invio Operational Storage",
            f"Invio could not start because its operational storage is unavailable or unsafe to use. No operational database was overwritten.\n\n{exc}",
        )
        return 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
