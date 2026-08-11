from __future__ import annotations

import os
import unittest

# The CI installs PySide6 from the application requirements.  Offscreen keeps
# these lifecycle checks deterministic on headless Linux and Windows runners.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QPushButton, QWidget

    from src.accounts.models import Account
    from src.core.provider_manager import ProviderManifest
    from src.core.state import AppState
    from src.customers.models import CustomerList
    from src.invoices.templates import InvoiceTemplate
    from src.ui.dialogs import NewTaskDialog, compact_message_box

    _PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    QApplication = QDialog = QMessageBox = QPushButton = QWidget = QTimer = Qt = None  # type: ignore[assignment]
    Account = ProviderManifest = AppState = CustomerList = InvoiceTemplate = NewTaskDialog = None  # type: ignore[assignment]
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


@unittest.skipUnless(_PYSIDE6_AVAILABLE, "PySide6 runtime dependency is not installed")
class NewTaskDialogRuntimeInteractionTests(unittest.TestCase):
    """Exercise the compact New Task modal without replacing its domain contract."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.state = AppState()
        for index in range(1, 13):
            account = Account(
                id=f"odoo-{index:02d}",
                provider_id="odoo",
                provider_name="Odoo",
                name=f"Odoo {index:02d}",
                mode="Default",
                status="Verified",
            )
            self.state.accounts[account.id] = account
        blocked = Account(
            id="odoo-blocked",
            provider_id="odoo",
            provider_name="Odoo",
            name="Odoo Blocked",
            mode="Default",
            status="Not Verified",
        )
        stripe = Account(
            id="stripe-01",
            provider_id="stripe",
            provider_name="Stripe",
            name="Stripe 01",
            mode="Test",
            status="Verified",
        )
        self.state.accounts[blocked.id] = blocked
        self.state.accounts[stripe.id] = stripe

        self.state.invoice_templates["tpl-1"] = InvoiceTemplate(
            id="tpl-1", name="Template A", currency="USD", days_until_due=7
        )
        self.state.invoice_templates["tpl-2"] = InvoiceTemplate(
            id="tpl-2", name="Template B", currency="EUR", days_until_due=14
        )
        self.state.customer_lists["list-1"] = CustomerList(
            id="list-1", name="Customers A", emails=["one@example.com"]
        )
        self.state.customer_lists["list-2"] = CustomerList(
            id="list-2", name="Customers B", emails=["two@example.com"]
        )
        self.providers = [
            ProviderManifest(id="odoo", name="Odoo", version="1.0.0", description="Odoo test provider"),
            ProviderManifest(id="stripe", name="Stripe", version="1.0.0", description="Stripe test provider"),
        ]

    def _dialog(self):
        return NewTaskDialog(self.state, self.providers)

    @staticmethod
    def _button(dialog, text: str):
        for item in dialog.findChildren(QPushButton):
            if item.text() == text:
                return item
        raise AssertionError(f"Button not found: {text}")

    def test_new_task_open_close_and_reopen_lifecycle(self):
        dialog = self._dialog()
        dialog.show()
        self.app.processEvents()
        self.assertTrue(dialog.isVisible())
        self.assertEqual(dialog.windowTitle(), "New Task")
        self.assertLessEqual(dialog.height(), 430)
        dialog.reject()
        self.app.processEvents()
        self.assertFalse(dialog.isVisible())

        dialog.show()
        self.app.processEvents()
        self.assertTrue(dialog.isVisible())
        dialog.reject()
        dialog.deleteLater()

    def test_provider_filter_search_and_account_scrolling_remain_functional(self):
        dialog = self._dialog()
        dialog.show()
        self.app.processEvents()
        self.assertEqual(dialog.provider_combo.currentData(), "odoo")
        self.assertEqual(dialog.accounts.rowCount(), 10)
        self.assertGreater(dialog.accounts.verticalScrollBar().maximum(), 0)

        dialog.accounts_toolbar.search.setText("Odoo 11")
        self.app.processEvents()
        self.assertEqual(dialog.accounts.rowCount(), 1)
        self.assertEqual(dialog.accounts.item(0, 1).text(), "Odoo 11")

        dialog.accounts_toolbar.search.clear()
        unavailable_index = dialog.accounts_toolbar.filters[0].findData("unavailable")
        dialog.accounts_toolbar.filters[0].setCurrentIndex(unavailable_index)
        self.app.processEvents()
        self.assertEqual(dialog.accounts.rowCount(), 1)
        self.assertEqual(dialog.accounts.item(0, 1).text(), "Odoo Blocked")

        all_index = dialog.accounts_toolbar.filters[0].findData("")
        dialog.accounts_toolbar.filters[0].setCurrentIndex(all_index)
        stripe_index = dialog.provider_combo.findData("stripe")
        dialog.provider_combo.setCurrentIndex(stripe_index)
        self.app.processEvents()
        self.assertEqual(dialog.accounts.rowCount(), 1)
        self.assertEqual(dialog.accounts.item(0, 1).text(), "Stripe 01")
        dialog.reject()
        dialog.deleteLater()

    def test_account_template_customer_selection_and_create_payload_are_preserved(self):
        dialog = self._dialog()
        dialog.show()
        self.app.processEvents()
        dialog.accounts.item(0, 0).setCheckState(Qt.CheckState.Checked)
        dialog.invoice_template.setCurrentIndex(1)
        dialog.customer_list.setCurrentIndex(1)
        self.app.processEvents()

        expected_account = str(dialog.accounts.item(0, 0).data(Qt.ItemDataRole.UserRole))
        self.assertEqual(dialog.selected_account_ids(), [expected_account])
        self._button(dialog, "Create Task").click()
        self.app.processEvents()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(
            dialog.payload(),
            {
                "provider_id": "odoo",
                "provider_name": "Odoo",
                "account_ids": [expected_account],
                "invoice_template_id": "tpl-2",
                "customer_list_id": "list-2",
            },
        )
        dialog.deleteLater()

    def test_cancel_rejects_without_task_payload_side_effect(self):
        dialog = self._dialog()
        dialog.show()
        self.app.processEvents()
        self._button(dialog, "Cancel").click()
        self.app.processEvents()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        dialog.deleteLater()


if __name__ == "__main__":
    unittest.main()
