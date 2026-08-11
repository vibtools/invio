from __future__ import annotations

import os
import unittest

# The CI installs PySide6 from the application requirements.  Offscreen keeps
# these lifecycle checks deterministic on headless Linux and Windows runners.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtWidgets import QApplication, QDialog, QMenu, QMessageBox, QPushButton, QWidget

    from src.accounts.models import Account
    from src.core.provider_manager import ProviderManifest
    from src.core.state import AppState
    from src.customers.models import CustomerList
    from src.invoices.templates import InvoiceTemplate
    from src.ui.dialogs import NewTaskDialog, compact_message_box
    from src.ui.pages.accounts_page import AccountsPage

    _PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    QApplication = QDialog = QMenu = QMessageBox = QPushButton = QWidget = QTimer = Qt = None  # type: ignore[assignment]
    Account = ProviderManifest = AppState = CustomerList = InvoiceTemplate = NewTaskDialog = AccountsPage = None  # type: ignore[assignment]
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


@unittest.skipUnless(_PYSIDE6_AVAILABLE, "PySide6 runtime dependency is not installed")
class AccountsPageRuntimeInteractionTests(unittest.TestCase):
    """Exercise the v1.48.5 flat Accounts table through the real Qt widget layer."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.state = AppState()
        for index in range(1, 206):
            status = "Verified" if index % 3 else "Not Verified"
            account = Account(
                id=f"odoo-{index:03d}",
                provider_id="odoo",
                provider_name="Odoo",
                name=f"Odoo-client{index:03d}",
                mode="Default",
                status=status,
                last_verification_at="2026-08-11T18:57:00+00:00",
            )
            self.state.accounts[account.id] = account
        refrens = Account(
            id="refrens-main",
            provider_id="refrens",
            provider_name="Refrens",
            name="Refrens-main",
            mode="Default",
            status="Verified",
        )
        agiled = Account(
            id="agiled-main",
            provider_id="agiled",
            provider_name="Agiled",
            name="Agiled-main",
            mode="Default",
            status="Verified",
        )
        self.state.accounts[refrens.id] = refrens
        self.state.accounts[agiled.id] = agiled
        self.providers = type(
            "ProvidersStub",
            (),
            {
                "list_installed": lambda _self: [
                    ProviderManifest(id="odoo", name="Odoo", version="1.0.0", description="Odoo"),
                    ProviderManifest(id="refrens", name="Refrens", version="1.0.3", description="Refrens"),
                ]
            },
        )()
        self.calls: list[tuple[str, str]] = []
        self.page = AccountsPage(
            self.state,
            self.providers,
            lambda: self.calls.append(("add", "")),
            lambda account_id: self.calls.append(("edit", account_id)),
            lambda account_id: self.calls.append(("retest", account_id)),
            lambda account_id: self.calls.append(("delete", account_id)),
        )
        self.page.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()

    def test_flat_table_semantic_status_and_scalable_pagination(self):
        page = self.page
        self.assertEqual(page.table.columnCount(), 4)
        self.assertEqual(
            [page.table.horizontalHeaderItem(index).text() for index in range(4)],
            ["ACCOUNT", "PROVIDER", "STATUS", "ACTION"],
        )
        self.assertEqual(page.pager.total, 207)
        self.assertEqual(page.table.rowCount(), 10)

        page_size_index = page.pager.page_size_combo.findData(25)
        page.pager.page_size_combo.setCurrentIndex(page_size_index)
        self.app.processEvents()
        self.assertEqual(page.table.rowCount(), 25)
        page.pager.next.click()
        self.app.processEvents()
        self.assertEqual(page.pager.page, 2)
        self.assertEqual(page.table.rowCount(), 25)

        page.toolbar.search.setText("Agiled-main")
        self.app.processEvents()
        self.assertEqual(page.table.rowCount(), 1)
        self.assertEqual(page.table.item(0, 0).text(), "Agiled-main")
        badge_host = page.table.cellWidget(0, 2)
        labels = badge_host.findChildren(type(page.empty))
        self.assertTrue(any(item.text() == "! Not Installed" for item in labels))

    def test_provider_status_filters_and_row_action_menu_preserve_callbacks(self):
        page = self.page
        provider_index = page.toolbar.filters[0].findData("refrens")
        page.toolbar.filters[0].setCurrentIndex(provider_index)
        self.app.processEvents()
        self.assertEqual(page.table.rowCount(), 1)
        self.assertEqual(page.table.item(0, 0).text(), "Refrens-main")

        page.toolbar.filters[0].setCurrentIndex(page.toolbar.filters[0].findData("odoo"))
        page.toolbar.filters[1].setCurrentIndex(page.toolbar.filters[1].findData("Not Verified"))
        self.app.processEvents()
        self.assertGreater(page.pager.total, 0)
        self.assertTrue(all(page.table.item(row, 2).text() == "Not Verified" for row in range(page.table.rowCount())))

        page.toolbar.search.clear()
        page.toolbar.filters[0].setCurrentIndex(page.toolbar.filters[0].findData("refrens"))
        page.toolbar.filters[1].setCurrentIndex(page.toolbar.filters[1].findData(""))
        self.app.processEvents()
        action_host = page.table.cellWidget(0, 3)
        action_button = next(button for button in action_host.findChildren(QPushButton) if button.text() == "⋯")
        menu = action_button.findChild(QMenu)
        self.assertIsNotNone(menu)
        for action in menu.actions():
            if action.text() == "Edit":
                action.trigger()
            elif action.text() == "Re-test":
                action.trigger()
            elif action.text() == "Delete":
                action.trigger()
        self.assertEqual(
            self.calls,
            [("edit", "refrens-main"), ("retest", "refrens-main"), ("delete", "refrens-main")],
        )


if __name__ == "__main__":
    unittest.main()
