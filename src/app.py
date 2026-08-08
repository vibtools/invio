from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Invio")
    app.setOrganizationName("Vib Tools")
    app.setStyle("Fusion")
    window = MainWindow(project_root())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
