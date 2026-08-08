from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from ..core.provider_manager import ProviderManager, ProviderManifestError
from ..core.provider_runtime import ProviderRuntime, ProviderRuntimeError
from ..core.settings import AppSettings, SettingsError, SettingsManager, WindowState
from ..core.state import AppState, StateError
from ..core.worker_manager import TaskRunner, WorkerManager
from ..customers.importers import import_emails
from .dialogs import AddAccountDialog, InvoiceTemplateDialog, NewCustomerListDialog, NewTaskDialog, compact_message_box
from .pages import (
    AccountsPage,
    CustomerListsPage,
    DashboardPage,
    InvoiceTemplatesPage,
    LogsPage,
    ProvidersPage,
    ReportsPage,
    SettingsPage,
    TasksPage,
)
from .styles import app_qss
from .tokens import CONST, NAV_ITEMS
from .widgets import hbox, label, status_badge, token_chip, vbox

_KEY_MASK = re.compile(r"\b(?:sk|rk)_(?:test|live)_[A-Za-z0-9_\-]+\b", re.I)


class MainWindow(QMainWindow):
    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = Path(project_root)
        self.settings_manager = SettingsManager()
        self.app_settings = self.settings_manager.settings
        self.state = AppState()
        self.providers = ProviderManager(self.project_root)
        self.provider_runtime = ProviderRuntime()
        self.worker_manager = WorkerManager(self)
        self.task_runners: dict[str, TaskRunner] = {}
        self.pages: dict[str, QWidget] = {}
        self.page_indexes: dict[str, int] = {}
        self.nav_buttons: dict[str, QPushButton] = {}

        self.setWindowTitle("Invio — Vib Tools")
        self.setMinimumSize(CONST.min_window_width, CONST.min_window_height)
        self.resize(CONST.default_window_width, CONST.default_window_height)
        self._restore_window_geometry()
        self.setStyleSheet(app_qss())

        self._build_shell()
        self._build_status_bar()
        self._connect_workers()
        self._apply_app_settings()
        self.navigate(self.settings_manager.startup_page())
        self.log("Invio v1.0.0.1.5 started.")
        if self.settings_manager.load_warning:
            self.log(self.settings_manager.load_warning)

    def register_task_runner(self, provider_id: str, runner: TaskRunner) -> None:
        """Backend integration point: inject a provider task runner by provider id."""
        self.task_runners[provider_id] = runner

    def _build_shell(self) -> None:
        root_widget = QWidget()
        root_widget.setObjectName("AppRoot")
        root = QVBoxLayout(root_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("PageViewport")
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)
        self.setCentralWidget(root_widget)
        self._register_pages()

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("WindowHeader")
        layout = hbox(header, (12, 0, 12, 0), 5)
        layout.addWidget(status_badge("VT", "info"))
        layout.addWidget(label("Invio", "WindowTitle", False))
        self.breadcrumb = label("Home / Accounts", "Breadcrumb", False)
        self.breadcrumb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.breadcrumb, 1)
        layout.addWidget(token_chip("Vib Tools"))
        self.viewport_chip = token_chip("Medium")
        layout.addWidget(self.viewport_chip)
        return header

    def _icon_for(self, key: str):
        style = QApplication.style()
        mapping = {
            "dashboard": QStyle.StandardPixmap.SP_ComputerIcon,
            "accounts": QStyle.StandardPixmap.SP_DirHomeIcon,
            "invoice": QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "customers": QStyle.StandardPixmap.SP_FileDialogListView,
            "tasks": QStyle.StandardPixmap.SP_BrowserReload,
            "providers": QStyle.StandardPixmap.SP_DriveNetIcon,
            "reports": QStyle.StandardPixmap.SP_FileIcon,
            "logs": QStyle.StandardPixmap.SP_MessageBoxInformation,
            "settings": QStyle.StandardPixmap.SP_FileDialogContentsView,
        }
        return style.standardIcon(mapping.get(key, QStyle.StandardPixmap.SP_FileIcon))

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        layout = vbox(sidebar, (8, 8, 8, 8), 4)
        layout.addWidget(label("Invio", "SidebarTitle", False))
        layout.addWidget(label("Vib Tools • Invoice Automation", "Caption", False))

        nav_host = QWidget()
        nav_host.setObjectName("SidebarNavHost")
        nav_layout = vbox(nav_host, (0, 8, 0, 0), 2)
        for page_name, icon_key in NAV_ITEMS:
            item = QPushButton(page_name)
            item.setObjectName("NavItem")
            item.setCheckable(True)
            item.setAutoExclusive(True)
            item.setIcon(self._icon_for(icon_key))
            item.clicked.connect(lambda _checked=False, name=page_name: self.navigate(name))
            self.nav_buttons[page_name] = item
            nav_layout.addWidget(item)
        nav_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("MinimalScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(nav_host)
        layout.addWidget(scroll, 1)

        separator = QFrame()
        separator.setObjectName("Divider")
        layout.addWidget(separator)
        layout.addWidget(label("Vib Tools • Production", "Caption", False))
        return sidebar

    def _register_pages(self) -> None:
        self.dashboard_page = DashboardPage(self.state, self.providers, self.new_task)
        self.accounts_page = AccountsPage(self.state, self.providers, self.add_account)
        self.invoice_page = InvoiceTemplatesPage(self.state, self.new_template, self.edit_template, self.delete_template)
        self.customer_page = CustomerListsPage(self.state, self.new_customer_list, self.import_customer_emails, self.delete_customer_list)
        self.tasks_page = TasksPage(
            self.state,
            self.new_task,
            self.start_task,
            self.pause_task,
            self.resume_task,
            self.stop_task,
            self.retry_task,
            self.close_task,
        )
        self.providers_page = ProvidersPage(self.providers, self.install_provider, self.uninstall_provider, self.load_provider)
        self.reports_page = ReportsPage(self.state, self.export_report)
        self.logs_page = LogsPage(self.clear_logs, self.export_logs)
        self.settings_page = SettingsPage(self.app_settings, self.save_app_settings)

        ordered = [
            ("Dashboard", self.dashboard_page),
            ("Accounts", self.accounts_page),
            ("Invoice Templates", self.invoice_page),
            ("Customer Lists", self.customer_page),
            ("Tasks", self.tasks_page),
            ("Providers", self.providers_page),
            ("Reports", self.reports_page),
            ("Live Logs", self.logs_page),
            ("Settings", self.settings_page),
        ]
        for index, (name, page) in enumerate(ordered):
            self.pages[name] = page
            self.page_indexes[name] = index
            self.stack.addWidget(page)

    def _build_status_bar(self) -> None:
        self.status_label = QLabel("Viewing: Accounts")
        self.statusBar().addWidget(self.status_label, 1)
        self.runtime_status = QLabel("Production • v1.0.0.1.5")
        self.statusBar().addPermanentWidget(self.runtime_status)

    def _connect_workers(self) -> None:
        self.worker_manager.progress_changed.connect(self._worker_progress)
        self.worker_manager.status_changed.connect(self._worker_status)
        self.worker_manager.log_message.connect(lambda task_id, message: self.log(f"{task_id}: {message}"))
        self.worker_manager.finished.connect(self._worker_finished)

    def navigate(self, name: str) -> None:
        if name not in self.page_indexes:
            return
        self.stack.setCurrentIndex(self.page_indexes[name])
        self.breadcrumb.setText(f"Home / {name}")
        self.status_label.setText(f"Viewing: {name}")
        if name in self.nav_buttons:
            self.nav_buttons[name].setChecked(True)
        if name == "Dashboard":
            self.dashboard_page.refresh()
        elif name == "Accounts":
            self.accounts_page.refresh()
        elif name == "Invoice Templates":
            self.invoice_page.refresh()
        elif name == "Customer Lists":
            self.customer_page.refresh()
        elif name == "Tasks":
            self.tasks_page.refresh()
        elif name == "Providers":
            self.providers_page.refresh()
        elif name == "Reports":
            self.reports_page.refresh()
        self.settings_manager.record_last_page(name)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        width = self.width()
        if width < CONST.compact_breakpoint:
            text = "Compact"
        elif width < CONST.medium_breakpoint:
            text = "Medium"
        else:
            text = "Large"
        if hasattr(self, "viewport_chip"):
            self.viewport_chip.setText(text)
        super().resizeEvent(event)

    def _restore_window_geometry(self) -> None:
        state = self.settings_manager.window_state()
        if state is None:
            return
        saved_screen = QApplication.screenAt(QPoint(state.x, state.y))
        screen = saved_screen or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        width = min(max(CONST.min_window_width, state.width), max(CONST.min_window_width, available.width()))
        height = min(max(CONST.min_window_height, state.height), max(CONST.min_window_height, available.height()))
        self.resize(width, height)
        if saved_screen is not None:
            max_x = max(available.left(), available.right() - width + 1)
            max_y = max(available.top(), available.bottom() - height + 1)
            self.move(
                min(max(state.x, available.left()), max_x),
                min(max(state.y, available.top()), max_y),
            )

    def _apply_app_settings(self) -> None:
        if hasattr(self, "logs_page"):
            self.logs_page.configure(
                auto_scroll=self.app_settings.auto_scroll_logs,
                max_entries=self.app_settings.max_log_entries,
            )

    def save_app_settings(self, settings: AppSettings) -> tuple[bool, str]:
        try:
            self.app_settings = self.settings_manager.update(settings)
        except SettingsError as exc:
            self._message("Settings", str(exc), QMessageBox.Icon.Warning)
            return False, str(exc)
        self._apply_app_settings()
        current_index = self.stack.currentIndex() if hasattr(self, "stack") else -1
        for page_name, page_index in self.page_indexes.items():
            if page_index == current_index:
                self.settings_manager.record_last_page(page_name)
                break
        if hasattr(self, "settings_page"):
            self.settings_page.load_settings(self.app_settings)
        self.log("Application settings saved.")
        return True, "Settings saved and applied."

    def _dialog_directory(self) -> str:
        return self.settings_manager.dialog_directory()

    def _save_dialog_path(self, default_name: str) -> str:
        directory = self._dialog_directory()
        return str(Path(directory) / default_name) if directory else default_name

    def _remember_dialog_path(self, selected_path: str) -> None:
        if selected_path:
            self.settings_manager.record_last_folder(selected_path)

    def _message(self, title: str, text: str, icon: QMessageBox.Icon = QMessageBox.Icon.Information) -> None:
        compact_message_box(self, title, text, icon=icon)

    def _question(self, title: str, text: str) -> QMessageBox.StandardButton:
        return compact_message_box(
            self,
            title,
            text,
            icon=QMessageBox.Icon.Question,
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default_button=QMessageBox.StandardButton.No,
        )

    def log(self, message: str) -> None:
        safe = _KEY_MASK.sub(lambda match: f"{match.group(0)[:10]}…***MASKED***", str(message))
        if self.app_settings.show_log_timestamps:
            rendered = f"{datetime.now().strftime('%H:%M:%S')} | {safe}"
        else:
            rendered = safe
        if hasattr(self, "logs_page"):
            self.logs_page.append(rendered)

    def _refresh_dashboard(self) -> None:
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.refresh()

    # Provider workflow -------------------------------------------------
    def install_provider(self, provider_id: str) -> None:
        try:
            provider = self.providers.install_packaged(provider_id)
        except ProviderManifestError as exc:
            self._message("Provider", str(exc), QMessageBox.Icon.Warning)
            return
        self.log(f"Provider installed: {provider.name} v{provider.version}")
        self.providers_page.refresh()
        self.accounts_page.refresh()
        self._refresh_dashboard()

    def uninstall_provider(self, provider_id: str) -> None:
        provider = self.providers.get_installed(provider_id)
        if provider is None:
            self._message("Provider", "This provider is not installed.", QMessageBox.Icon.Warning)
            return
        answer = self._question(
            "Uninstall Provider",
            f"Uninstall {provider.name}? Existing accounts and tasks are kept in the current session, but this provider will no longer be available for new account or task selection until it is installed again.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            removed = self.providers.uninstall(provider_id)
        except ProviderManifestError as exc:
            self._message("Provider", str(exc), QMessageBox.Icon.Warning)
            return
        self.log(f"Provider uninstalled: {removed.name} v{removed.version}")
        self.providers_page.refresh()
        self.accounts_page.refresh()
        self._refresh_dashboard()

    def load_provider(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Provider Manifest", self._dialog_directory(), "Provider Manifest (*.json);;JSON (*.json)")
        if not path:
            return
        self._remember_dialog_path(path)
        try:
            provider = self.providers.load_external(path)
        except ProviderManifestError as exc:
            self._message("Provider", str(exc), QMessageBox.Icon.Warning)
            return
        self.log(f"External provider manifest loaded: {provider.name} v{provider.version}")
        self.providers_page.refresh()
        self.accounts_page.refresh()
        self._refresh_dashboard()

    # Accounts ----------------------------------------------------------
    def add_account(self) -> None:
        providers = self.providers.list_installed()
        if not providers:
            self._message("Accounts", "Install or load a provider from the Providers page first.", QMessageBox.Icon.Warning)
            return
        dialog = AddAccountDialog(providers, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        try:
            account = self.state.add_account(**dialog.payload())
        except StateError as exc:
            self._message("Accounts", str(exc), QMessageBox.Icon.Warning)
            return
        self.log(f"Account added: {account.provider_name}/{account.name} ({account.mode}).")
        self.accounts_page.refresh()
        self._refresh_dashboard()

    # Invoice templates ------------------------------------------------
    def new_template(self) -> None:
        dialog = InvoiceTemplateDialog(parent=self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            try:
                template = self.state.save_invoice_template(**dialog.payload())
            except StateError as exc:
                self._message("Invoice Template", str(exc), QMessageBox.Icon.Warning)
                return
            self.log(f"Invoice template created: {template.name}")
            self.invoice_page.refresh()
            self._refresh_dashboard()

    def edit_template(self, template_id: str) -> None:
        template = self.state.invoice_templates.get(template_id)
        if not template:
            return
        dialog = InvoiceTemplateDialog(template, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            try:
                template = self.state.save_invoice_template(**dialog.payload())
            except StateError as exc:
                self._message("Invoice Template", str(exc), QMessageBox.Icon.Warning)
                return
            self.log(f"Invoice template updated: {template.name}")
            self.invoice_page.refresh()
            self._refresh_dashboard()

    def delete_template(self, template_id: str) -> None:
        template = self.state.invoice_templates.get(template_id)
        if not template:
            return
        if self.app_settings.confirm_delete_template:
            answer = self._question("Delete Template", f"Delete invoice template '{template.name}'?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        try:
            self.state.delete_invoice_template(template_id)
        except StateError as exc:
            self._message("Invoice Template", str(exc), QMessageBox.Icon.Warning)
            return
        self.log(f"Invoice template deleted: {template.name}")
        self.invoice_page.refresh()
        self._refresh_dashboard()

    # Customer lists ---------------------------------------------------
    def new_customer_list(self) -> None:
        dialog = NewCustomerListDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        try:
            item = self.state.create_customer_list(dialog.list_name())
        except StateError as exc:
            self._message("Customer List", str(exc), QMessageBox.Icon.Warning)
            return
        self.log(f"Customer list created: {item.name}")
        self.customer_page.refresh(item.id)
        self._refresh_dashboard()

    def import_customer_emails(self, list_id: str) -> None:
        customer_list = self.state.customer_lists.get(list_id)
        if not customer_list:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload Customer Emails",
            self._dialog_directory(),
            "Customer Files (*.csv *.tsv *.xlsx *.xlsm *.txt);;All Files (*)",
        )
        if not path:
            return
        self._remember_dialog_path(path)
        try:
            emails, warnings = import_emails(path)
            added = self.state.add_emails(list_id, emails)
        except (OSError, ValueError) as exc:
            self._message("Customer List", f"Import failed: {exc}", QMessageBox.Icon.Warning)
            return
        self.log(f"Imported {added} email(s) into customer list '{customer_list.name}'.")
        self.customer_page.refresh(list_id)
        self._refresh_dashboard()
        if warnings:
            self._message("Customer List", "\n".join(warnings), QMessageBox.Icon.Warning)

    def delete_customer_list(self, list_id: str) -> None:
        item = self.state.customer_lists.get(list_id)
        if not item:
            return
        if self.app_settings.confirm_delete_customer_list:
            answer = self._question("Delete Customer List", f"Delete customer list '{item.name}'?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        try:
            self.state.delete_customer_list(list_id)
        except StateError as exc:
            self._message("Customer List", str(exc), QMessageBox.Icon.Warning)
            return
        self.log(f"Customer list deleted: {item.name}")
        self.customer_page.refresh()
        self._refresh_dashboard()

    # Tasks ------------------------------------------------------------
    def new_task(self) -> None:
        providers = self.providers.list_installed()
        if not providers:
            self._message("Task", "Install or load a provider first.", QMessageBox.Icon.Warning)
            return
        if not self.state.accounts:
            self._message("Task", "Add at least one provider account first.", QMessageBox.Icon.Warning)
            return
        if not self.state.invoice_templates:
            self._message("Task", "Create an invoice template first.", QMessageBox.Icon.Warning)
            return
        if not self.state.customer_lists:
            self._message("Task", "Create a customer list first.", QMessageBox.Icon.Warning)
            return
        dialog = NewTaskDialog(self.state, providers, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        try:
            task = self.state.create_task(**dialog.payload())
        except StateError as exc:
            self._message("Task", str(exc), QMessageBox.Icon.Warning)
            return
        self.log(
            f"{task.name} created with provider {task.provider_name}, template '{task.invoice_template_name}', "
            f"{len(task.account_ids)} account(s), list '{task.customer_list_name}'."
        )
        self.tasks_page.refresh()
        self.accounts_page.refresh()
        self.reports_page.refresh()
        self._refresh_dashboard()

    def _runner_for_task(self, task_id: str, *, retry_failed: bool = False) -> tuple[object | None, TaskRunner | None, str]:
        task = self.state.tasks.get(task_id)
        if not task:
            return None, None, "Task was not found."
        injected = self.task_runners.get(task.provider_id)
        if injected is not None:
            return task, injected, ""
        try:
            runner = self.provider_runtime.make_task_runner(task, self.state, retry_failed=retry_failed)
        except ProviderRuntimeError as exc:
            return task, None, str(exc)
        return task, runner, ""

    def start_task(self, task_id: str) -> None:
        task, runner, error = self._runner_for_task(task_id)
        if task is None:
            return
        if runner is None:
            message = error or "No task runner is available for this provider."
            self.state.set_task_status(task_id, "Ready", message)
            self.tasks_page.refresh_task(task_id)
            self.log(f"{task.name}: start blocked: {message}")
            self._message("Provider Unavailable", f"{message} No invoice was sent.", QMessageBox.Icon.Warning)
            self._refresh_dashboard()
            return
        self.worker_manager.start(task, runner)

    def pause_task(self, task_id: str) -> None:
        self.worker_manager.pause(task_id)

    def resume_task(self, task_id: str) -> None:
        self.worker_manager.resume(task_id)

    def stop_task(self, task_id: str) -> None:
        self.worker_manager.stop(task_id)

    def retry_task(self, task_id: str) -> None:
        task, runner, error = self._runner_for_task(task_id, retry_failed=True)
        if task is None:
            return
        if runner is None:
            message = error or "Retry cannot start because no task runner is available for this provider."
            self.log(f"{task.name}: retry blocked: {message}")
            self._message("Provider Unavailable", message, QMessageBox.Icon.Warning)
            return
        self.worker_manager.start(task, runner)

    def close_task(self, task_id: str) -> None:
        task = self.state.tasks.get(task_id)
        if not task:
            return
        if self.worker_manager.is_running(task_id):
            self._message("Task", "Stop the task before closing it.", QMessageBox.Icon.Warning)
            return
        if self.app_settings.confirm_close_task:
            answer = self._question("Close Task", f"Close {task.name} and release its selected accounts?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.state.close_task(task_id)
        self.provider_runtime.clear_task(task_id)
        self.log(f"{task.name} closed; reserved accounts released.")
        self.tasks_page.refresh()
        self.accounts_page.refresh()
        self.reports_page.refresh()
        self._refresh_dashboard()

    def _worker_status(self, task_id: str, status: str, message: str) -> None:
        if task_id in self.state.tasks:
            self.state.set_task_status(task_id, status, message)
            self.tasks_page.refresh_task(task_id)
            self.reports_page.refresh()
            self._refresh_dashboard()

    def _worker_progress(self, task_id: str, processed: int, success: int, failed: int, message: str) -> None:
        if task_id in self.state.tasks:
            self.state.set_task_progress(task_id, processed=processed, success=success, failed=failed)
            self.state.set_task_status(task_id, self.state.tasks[task_id].status, message)
            self.tasks_page.refresh_task(task_id)
            self.reports_page.refresh()
            self._refresh_dashboard()

    def _worker_finished(self, task_id: str, status: str) -> None:
        if task_id in self.state.tasks:
            task = self.state.tasks[task_id]
            if status == "Failed" and task.failed:
                message = f"{task.failed} recipient(s) failed. Review Live Logs and use Retry Failed."
            else:
                message = f"Worker finished with status: {status}"
            self.state.set_task_status(task_id, status, message)
            self.tasks_page.refresh_task(task_id)
            self.reports_page.refresh()
            self._refresh_dashboard()
            self.log(f"{task.name}: worker finished with {status}.")

    # Reports / logs ---------------------------------------------------
    def export_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Task Report", self._save_dialog_path("invio_task_report.csv"), "CSV (*.csv)")
        if not path:
            return
        self._remember_dialog_path(path)
        with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Task", "Provider", "Invoice Template", "Accounts", "Customer List", "Total", "Success", "Failed", "Remaining", "Status"])
            for task in self.state.tasks.values():
                writer.writerow(
                    [
                        task.name,
                        task.provider_name,
                        task.invoice_template_name,
                        "; ".join(task.account_names),
                        task.customer_list_name,
                        task.total,
                        task.success,
                        task.failed,
                        task.remaining,
                        task.status,
                    ]
                )
        self.log(f"Report exported: {Path(path).name}")

    def clear_logs(self) -> None:
        if self.app_settings.confirm_clear_logs:
            answer = self._question("Clear Live Logs", "Clear all log entries currently shown?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.logs_page.clear()
        self.log("Log view cleared.")

    def export_logs(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Logs", self._save_dialog_path("invio_logs.txt"), "Text (*.txt)")
        if not path:
            return
        self._remember_dialog_path(path)
        Path(path).write_text(self.logs_page.viewer.toPlainText(), encoding="utf-8")

    def closeEvent(self, event) -> None:  # type: ignore[override]
        active = [task_id for task_id in self.state.tasks if self.worker_manager.is_running(task_id)]
        if active:
            if self.app_settings.confirm_exit_active_tasks:
                answer = self._question("Exit Invio", "Active task worker threads are running. Stop them and exit?")
                if answer != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
            self.worker_manager.stop_all()

        geometry = self.normalGeometry() if self.isMaximized() else self.geometry()
        self.settings_manager.record_window_state(
            WindowState(geometry.x(), geometry.y(), geometry.width(), geometry.height())
        )
        event.accept()
