from __future__ import annotations

import os
import unittest

# The CI installs PySide6 from the application requirements.  Offscreen keeps
# these lifecycle checks deterministic on headless Linux and Windows runners.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QRect, QTimer, Qt
    from PySide6.QtWidgets import QApplication, QDialog, QMenu, QMessageBox, QPushButton, QWidget

    from src.accounts.models import Account
    from src.core.provider_manager import ProviderManifest
    from src.core.state import AppState
    from src.customers.models import CustomerList, CustomerRecord
    from src.invoices.templates import InvoiceTemplate
    from src.ui.dialogs import NewTaskDialog, compact_message_box
    from src.ui.pages.accounts_page import AccountsPage
    from src.ui.pages.customer_lists_page import CustomerListsPage

    _PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    QApplication = QDialog = QMenu = QMessageBox = QPushButton = QWidget = QTimer = Qt = None  # type: ignore[assignment]
    Account = ProviderManifest = AppState = CustomerList = CustomerRecord = InvoiceTemplate = NewTaskDialog = AccountsPage = CustomerListsPage = None  # type: ignore[assignment]
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

    def test_status_cells_render_one_badge_without_raw_text_overlap(self):
        dialog = self._dialog()
        dialog.show()
        self.app.processEvents()

        for row in range(dialog.accounts.rowCount()):
            item = dialog.accounts.item(row, 3)
            host = dialog.accounts.cellWidget(row, 3)
            self.assertIsNotNone(item)
            self.assertIsNotNone(host)
            self.assertEqual(item.text(), "")
            raw = str(item.data(Qt.ItemDataRole.UserRole) or "")
            self.assertTrue(raw)
            # Locate the canonical badge by its shared status object name.
            badge = host.findChild(QWidget, "DataGridStatusSuccess") or host.findChild(QWidget, "DataGridStatusWarning")
            self.assertIsNotNone(badge)
            self.assertIn(raw, badge.text())

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
        badge = next(item for item in labels if item.text() == "✕ Not Installed")
        status_item = page.table.item(0, 2)
        self.assertEqual(status_item.text(), "")
        self.assertEqual(status_item.data(Qt.ItemDataRole.UserRole), "Not Installed")
        # The host contains centering stretches, so its aggregate sizeHint is not
        # the badge's clipping requirement. Verify the visible badge itself fits
        # inside the real status cell/host without forcing an oversized column.
        self.assertGreaterEqual(page.table.columnWidth(2), badge.sizeHint().width() + 4)
        self.app.processEvents()
        self.assertTrue(badge_host.rect().contains(badge.geometry()))

    def test_action_column_and_popup_geometry_stay_inside_accounts_window(self):
        page = self.page
        screen_rect = page.screen().availableGeometry()
        page.resize(min(1100, max(720, screen_rect.width() - 40)), min(900, max(640, screen_rect.height() - 40)))
        page_size_index = page.pager.page_size_combo.findData(25)
        page.pager.page_size_combo.setCurrentIndex(page_size_index)
        self.app.processEvents()

        self.assertEqual(page.table.horizontalHeaderItem(3).text(), "ACTION")
        self.assertGreaterEqual(page.table.columnWidth(3), 68)
        self.assertEqual(page.table.horizontalHeaderItem(2).textAlignment(), int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter))
        self.assertEqual(page.table.horizontalHeaderItem(3).textAlignment(), int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter))

        rows = (0, page.table.rowCount() // 2, page.table.rowCount() - 1)
        for row in rows:
            with self.subTest(row=row):
                page.table.scrollToItem(page.table.item(row, 0))
                self.app.processEvents()
                action_host = page.table.cellWidget(row, 3)
                action_button = next(button for button in action_host.findChildren(QPushButton) if button.text() == "⋯")
                menu = action_button.findChild(QMenu)
                self.assertIsNotNone(menu)

                self.assertGreaterEqual(action_button.x(), 0)
                self.assertLessEqual(action_button.x() + action_button.width(), action_host.width())

                safe = page._menu_safe_geometry(action_button)
                expected = page._bounded_menu_position(action_button, menu)
                expected_rect = QRect(expected, menu.sizeHint())
                self.assertTrue(safe.contains(expected_rect), (safe, expected_rect))
                observed: list[QRect] = []

                def inspect_and_close() -> None:
                    popup = QApplication.activePopupWidget()
                    if isinstance(popup, QMenu):
                        observed.append(popup.geometry())
                        popup.close()

                QTimer.singleShot(0, inspect_and_close)
                action_button.click()
                self.app.processEvents()
                self.assertEqual(len(observed), 1)
                self.assertTrue(safe.contains(observed[0]), (safe, observed[0]))

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
        self.assertTrue(all(page.table.item(row, 2).text() == "" for row in range(page.table.rowCount())))
        self.assertTrue(
            all(
                page.table.item(row, 2).data(Qt.ItemDataRole.UserRole) == "Not Verified"
                for row in range(page.table.rowCount())
            )
        )

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

@unittest.skipUnless(_PYSIDE6_AVAILABLE, "PySide6 runtime dependency is not installed")
class CustomerListsPageRuntimeInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.state = AppState()
        for index in range(1, 36):
            customers = []
            total = 62 if index == 1 else (index % 7)
            for customer_index in range(total):
                country = "US" if customer_index % 2 == 0 else "UK"
                customers.append(
                    CustomerRecord(
                        f"customer{index:02d}-{customer_index:03d}@example.com",
                        f"Customer {customer_index:03d}",
                        country,
                    )
                )
            item = CustomerList(id=f"list-{index:02d}", name=f"List {index:02d}", customers=customers)
            self.state.customer_lists[item.id] = item
        self.calls: list[tuple[str, str]] = []
        self.page = CustomerListsPage(
            self.state,
            lambda: self.calls.append(("new", "")),
            lambda list_id: self.calls.append(("upload", list_id)),
            lambda list_id: self.calls.append(("delete", list_id)),
        )
        self.page.resize(1100, 720)
        self.page.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()

    def test_compact_list_navigation_selection_search_filter_upload_and_pagination(self):
        page = self.page
        self.assertEqual(page.lists.count(), 35)
        self.assertGreater(page.lists.verticalScrollBar().maximum(), 0)
        self.assertEqual(page.selected_list_id, "list-01")
        self.assertEqual(page.customer_pager.total, 62)
        self.assertEqual(page.email_table.rowCount(), 10)
        self.assertEqual(
            [page.email_table.horizontalHeaderItem(index).text() for index in range(4)],
            ["#", "EMAIL", "NAME", "COUNTRY"],
        )

        first_item = page.lists.item(0)
        first_row = page.lists.itemWidget(first_item)
        count_badge = first_row.findChild(QWidget, "CustomerListCountBadge")
        self.assertIsNotNone(count_badge)
        self.assertEqual(count_badge.text(), "62")

        page.lists_toolbar.search.setText("List 20")
        self.app.processEvents()
        self.assertEqual(page.lists.count(), 1)
        self.assertEqual(page.selected_list_id, "list-20")
        page.lists_toolbar.search.clear()
        self.app.processEvents()

        state_filter = page.lists_toolbar.filters[0]
        state_filter.setCurrentIndex(state_filter.findData("empty"))
        self.app.processEvents()
        self.assertTrue(all(self.state.customer_lists[str(page.lists.item(i).data(Qt.ItemDataRole.UserRole))].count == 0 for i in range(page.lists.count())))
        state_filter.setCurrentIndex(state_filter.findData(""))
        self.app.processEvents()
        page._select_list("list-01")
        self.app.processEvents()

        country_filter = page.customer_toolbar.filters[0]
        country_filter.setCurrentIndex(country_filter.findData("UK"))
        self.app.processEvents()
        self.assertEqual(page.customer_pager.total, 31)
        page.customer_toolbar.search.setText("customer000")
        self.app.processEvents()
        self.assertLessEqual(page.customer_pager.total, 31)
        page.customer_toolbar.search.clear()
        country_filter.setCurrentIndex(country_filter.findData(""))
        self.app.processEvents()

        size_index = page.customer_pager.page_size_combo.findData(25)
        page.customer_pager.page_size_combo.setCurrentIndex(size_index)
        self.app.processEvents()
        self.assertEqual(page.email_table.rowCount(), 25)
        page.customer_pager.next.click()
        self.app.processEvents()
        self.assertEqual(page.customer_pager.page, 2)

        page.import_button.click()
        self.assertIn(("upload", "list-01"), self.calls)
        new_buttons = [item for item in page.findChildren(QPushButton) if item.text() in {"New List", "＋"}]
        self.assertEqual(len(new_buttons), 2)
        for control in new_buttons:
            control.click()
        self.assertEqual(self.calls.count(("new", "")), 2)

    def test_list_action_menu_is_row_scoped_and_bounded(self):
        page = self.page
        for index in (0, page.lists.count() // 2, page.lists.count() - 1):
            with self.subTest(index=index):
                item = page.lists.item(index)
                page.lists.scrollToItem(item)
                self.app.processEvents()
                row_widget = page.lists.itemWidget(item)
                action_button = next(control for control in row_widget.findChildren(QPushButton) if control.text() == "⋯")
                menu = action_button.findChild(QMenu)
                self.assertIsNotNone(menu)
                safe = page.window().frameGeometry().intersected(page.screen().availableGeometry())
                observed: list[QRect] = []

                def inspect_and_close() -> None:
                    popup = QApplication.activePopupWidget()
                    if isinstance(popup, QMenu):
                        observed.append(popup.geometry())
                        popup.close()

                QTimer.singleShot(0, inspect_and_close)
                action_button.click()
                self.app.processEvents()
                self.assertEqual(len(observed), 1)
                self.assertTrue(safe.contains(observed[0]), (safe, observed[0]))

        target_item = page.lists.item(0)
        target_id = str(target_item.data(Qt.ItemDataRole.UserRole))
        row_widget = page.lists.itemWidget(target_item)
        action_button = next(control for control in row_widget.findChildren(QPushButton) if control.text() == "⋯")
        menu = action_button.findChild(QMenu)
        delete_action = next(action for action in menu.actions() if action.text() == "Delete List")
        delete_action.trigger()
        self.app.processEvents()
        self.assertIn(("delete", target_id), self.calls)
        self.assertEqual(page.selected_list_id, target_id)

    def test_customer_lists_empty_state_and_resize_remain_stable(self):
        page = self.page
        page.lists_toolbar.search.setText("no-such-list")
        self.app.processEvents()
        self.assertEqual(page.lists.count(), 0)
        self.assertTrue(page.lists_empty.isVisible())
        self.assertFalse(page.import_button.isEnabled())
        page.lists_toolbar.search.clear()
        self.app.processEvents()
        self.assertGreater(page.lists.count(), 0)
        page.resize(900, 640)
        self.app.processEvents()
        self.assertGreater(page.lists.width(), 0)
        self.assertGreater(page.email_table.width(), page.lists.width())

