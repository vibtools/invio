from __future__ import annotations

import os
import unittest

# The CI installs PySide6 from the application requirements.  Offscreen keeps
# these lifecycle checks deterministic on headless Linux and Windows runners.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QWidget

    from src.ui.dialogs import compact_message_box

    _PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    QApplication = QDialog = QMessageBox = QWidget = QTimer = None  # type: ignore[assignment]
    compact_message_box = None  # type: ignore[assignment]
    _PYSIDE6_AVAILABLE = False


@unittest.skipUnless(_PYSIDE6_AVAILABLE, "PySide6 runtime dependency is not installed")
class QMessageBoxRuntimeInteractionTests(unittest.TestCase):
    """Exercise the real Qt/Shiboken QMessageBox lifecycle used by Invio."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _run_box(
        self,
        *,
        parent,
        title: str,
        icon,
        buttons,
        click_button,
        default_button=None,
    ):
        observed: list[tuple[bool, bool, bool]] = []

        def click_visible_box() -> None:
            modal = QApplication.activeModalWidget()
            if not isinstance(modal, QMessageBox):
                return
            observed.append(
                (
                    modal.testOption(QMessageBox.Option.DontUseNativeDialog),
                    bool(modal.property("customChrome")),
                    modal.layout() is not None,
                )
            )
            target = modal.button(click_button)
            if target is not None:
                target.click()

        # compact_message_box() enters a nested Qt event loop via exec().
        # The timer therefore interacts with the actual visible QMessageBox.
        QTimer.singleShot(0, click_visible_box)
        result = compact_message_box(
            parent,
            title,
            "Runtime interaction verification",
            icon=icon,
            buttons=buttons,
            default_button=default_button,
        )

        self.assertEqual(result, click_button)
        self.assertEqual(observed, [(True, True, True)])

    def test_information_message_box_executes_and_closes(self):
        parent = QWidget()
        self._run_box(
            parent=parent,
            title="Information",
            icon=QMessageBox.Icon.Information,
            buttons=QMessageBox.StandardButton.Ok,
            click_button=QMessageBox.StandardButton.Ok,
        )
        parent.deleteLater()

    def test_warning_message_box_with_dialog_parent_executes_and_closes(self):
        parent = QDialog()
        self._run_box(
            parent=parent,
            title="Warning",
            icon=QMessageBox.Icon.Warning,
            buttons=QMessageBox.StandardButton.Ok,
            click_button=QMessageBox.StandardButton.Ok,
        )
        parent.deleteLater()

    def test_critical_message_box_without_parent_executes_and_closes(self):
        self._run_box(
            parent=None,
            title="Critical",
            icon=QMessageBox.Icon.Critical,
            buttons=QMessageBox.StandardButton.Ok,
            click_button=QMessageBox.StandardButton.Ok,
        )

    def test_question_message_box_returns_yes_and_can_reopen(self):
        for title in ("Question One", "Question Two"):
            self._run_box(
                parent=QWidget(),
                title=title,
                icon=QMessageBox.Icon.Question,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                click_button=QMessageBox.StandardButton.Yes,
                default_button=QMessageBox.StandardButton.No,
            )


if __name__ == "__main__":
    unittest.main()
