from __future__ import annotations

import csv
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

from ..core.observability import StructuredLogEvent, atomic_write_csv, atomic_write_text, redact_sensitive_text
from ..core.provider_manager import ProviderManager, ProviderManifest, ProviderManifestError
from ..core.provider_runtime import (
    ProviderRuntime,
    ProviderRuntimeError,
    effective_capabilities,
    executable_capabilities,
    manifest_runtime_contract_matches,
    preflight_candidate,
    preflight_task,
)
from ..core.settings import AppSettings, SettingsError, SettingsManager, WindowState
from ..core.storage import CredentialStore, DomainStore, DomainStoreError
from ..core.state import AppState, StateError
from ..core.worker_manager import TaskRunner, WorkerManager
from ..customers.importers import import_customers
from ..tasks.models import LEGACY_SNAPSHOT_MESSAGE, Task
from ..tasks.state_machine import (
    CONTINUATION_UNAVAILABLE_MESSAGE,
    EXTERNAL_CONTINUATION_UNAVAILABLE_MESSAGE,
    NO_FAILED_RECIPIENTS_MESSAGE,
    NO_REMAINING_RECIPIENTS_MESSAGE,
    WORKER_NOT_ACTIVE_MESSAGE,
    TaskAction,
    TaskActionPolicy,
    TaskExecutionMode,
    reconcile_worker_terminal_status,
    require_task_action,
    task_action_policy,
)
from .dialogs import AccountRetestDialog, AddAccountDialog, InvoiceTemplateDialog, NewCustomerListDialog, NewTaskDialog, compact_message_box
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


class MainWindow(QMainWindow):
    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = Path(project_root)
        self.settings_manager = SettingsManager()
        self.app_settings = self.settings_manager.settings
        self.domain_store = DomainStore(self.settings_manager.path.with_name("domain.sqlite3"))
        self.credential_store = CredentialStore()
        loaded_domain = self.domain_store.load(self.credential_store)
        self.state = AppState(
            domain_store=self.domain_store,
            credential_store=self.credential_store,
            loaded=loaded_domain,
        )
        self.providers = ProviderManager(self.project_root)
        self.provider_runtime = ProviderRuntime(domain_store=self.domain_store, project_root=self.project_root)
        self.worker_manager = WorkerManager(self)
        self.task_runners: dict[str, TaskRunner] = {}
        self.pages: dict[str, QWidget] = {}
        self.page_indexes: dict[str, int] = {}
        self.nav_buttons: dict[str, QPushButton] = {}
        self._persistence_faulted_tasks: set[str] = set()
        self._shutdown_pending = False
        self._last_report_load_error = ""

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
        self.log("Invio v1.0.0.1.35 started.")
        if self.settings_manager.load_warning:
            self.log(self.settings_manager.load_warning)
        for warning in self.state.recovery_warnings:
            self.log(warning)

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
        self.accounts_page = AccountsPage(
            self.state, self.providers, self.add_account, self.edit_account, self.retest_account, self.delete_account
        )
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
            self._task_action_policy,
        )
        self.providers_page = ProvidersPage(
            self.providers,
            self.install_provider,
            self.uninstall_provider,
            self.load_provider,
            self._runtime_capabilities_for_provider,
            self._runtime_adapter_status_for_provider,
        )
        self.reports_page = ReportsPage(
            self.state,
            self.export_report,
            self._load_recipient_report,
            self.export_recipient_report,
            self.clear_delivery_history,
        )
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
        self.runtime_status = QLabel("Production • v1.0.0.1.35")
        self.statusBar().addPermanentWidget(self.runtime_status)

    def _connect_workers(self) -> None:
        self.worker_manager.progress_changed.connect(self._worker_progress)
        self.worker_manager.status_changed.connect(self._worker_status)
        self.worker_manager.log_message.connect(self._worker_plain_log)
        self.worker_manager.structured_log_message.connect(self._worker_structured_log)
        self.worker_manager.finished.connect(self._worker_finished)
        self.worker_manager.all_stopped.connect(self._complete_pending_shutdown)

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

    def _provider_secret_values(self) -> tuple[str, ...]:
        values: set[str] = set()
        sensitive_keys = {"secret_key", "app_secret", "api_key", "access_token", "token", "password"}
        for account in self.state.accounts.values():
            manifest = None
            try:
                manifest = self.providers.get_installed(account.provider_id) or self.providers.get_packaged(account.provider_id)
            except ProviderManifestError:
                manifest = None
            password_fields = {
                field.key for field in manifest.credential_fields if field.kind == "password"
            } if manifest is not None else set()
            for key, value in account.credentials.items():
                if value and (key in sensitive_keys or key in password_fields):
                    values.add(str(value))
        return tuple(sorted(values, key=len, reverse=True))

    def log(
        self,
        message: str,
        *,
        severity: str = "INFO",
        category: str = "APPLICATION",
        task_id: str = "",
        extra_secrets: tuple[str, ...] = (),
    ) -> None:
        event = StructuredLogEvent(severity=severity, category=category, message=str(message), task_id=task_id)
        safe_message = redact_sensitive_text(
            event.message,
            secret_values=(*self._provider_secret_values(), *extra_secrets),
            mask_emails=True,
        )
        safe_event = StructuredLogEvent(
            severity=event.severity,
            category=event.category,
            message=safe_message,
            task_id=event.task_id,
        )
        task_ref = safe_event.task_id or "-"
        body = f"{safe_event.severity:<7} | {safe_event.category:<8} | {task_ref} | {safe_event.message}"
        rendered = f"{datetime.now().strftime('%H:%M:%S')} | {body}" if self.app_settings.show_log_timestamps else body
        if hasattr(self, "logs_page"):
            self.logs_page.append_event(safe_event, rendered)

    def _worker_plain_log(self, task_id: str, message: str) -> None:
        severity = "ERROR" if str(message).startswith("Worker error:") else "INFO"
        self.log(message, severity=severity, category="TASK", task_id=task_id)

    def _worker_structured_log(self, task_id: str, severity: str, category: str, message: str) -> None:
        self.log(message, severity=severity, category=category, task_id=task_id)

    def _load_recipient_report(self):
        try:
            records = self.domain_store.recipient_delivery_report()
        except DomainStoreError as exc:
            message = str(exc)
            if message != self._last_report_load_error:
                self._last_report_load_error = message
                self.log(
                    f"Recipient delivery history could not be read: {message}",
                    severity="ERROR",
                    category="STORAGE",
                )
            return ()
        self._last_report_load_error = ""
        return records

    def _refresh_dashboard(self) -> None:
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.refresh()

    # Provider workflow -------------------------------------------------
    def _runtime_capabilities_for_provider(self, provider: ProviderManifest) -> tuple[str, ...]:
        try:
            packaged = self.providers.get_packaged(provider.id)
        except ProviderManifestError:
            return ()
        if packaged is not None:
            if not manifest_runtime_contract_matches(provider, packaged):
                return ()
            return effective_capabilities(provider)
        if provider.id in self.task_runners:
            return ("registered_task_runner",)
        runtime_values = self.provider_runtime.runtime_capabilities(provider.id)
        return runtime_values

    def _runtime_adapter_status_for_provider(self, provider: ProviderManifest) -> tuple[str, str]:
        try:
            packaged = self.providers.get_packaged(provider.id)
        except ProviderManifestError as exc:
            return "Incompatible", str(exc)
        if packaged is not None:
            if not manifest_runtime_contract_matches(provider, packaged):
                return "Incompatible", "Installed packaged manifest does not match the built-in runtime contract."
            capabilities = effective_capabilities(provider)
            return ("Executable", "Built-in packaged runtime adapter validated.") if capabilities else (
                "Manifest only", "Packaged provider intentionally has no executable runtime capability."
            )
        return self.provider_runtime.external_adapter_status(provider.id)

    def _provider_manifest_contract_error(self, provider: ProviderManifest) -> str:
        try:
            packaged = self.providers.get_packaged(provider.id)
        except ProviderManifestError as exc:
            return f"Packaged provider contract could not be read: {exc}"
        if packaged is not None and not manifest_runtime_contract_matches(provider, packaged):
            return (
                f"Installed {packaged.name} manifest does not match the packaged {packaged.name} runtime contract. "
                f"Uninstall it and install the packaged {packaged.name} provider again."
            )
        if packaged is None and provider.runtime_adapter is not None:
            status, message = self.provider_runtime.external_adapter_status(provider.id)
            if status != "Executable":
                return f"External provider runtime adapter is {status.lower()}: {message}"
        return ""

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
        try:
            provider = self.providers.get_installed(provider_id)
        except ProviderManifestError as exc:
            self._message("Provider", str(exc), QMessageBox.Icon.Warning)
            return
        if provider is None:
            self._message("Provider", "This provider is not installed.", QMessageBox.Icon.Warning)
            return

        active_tasks = [
            task for task in self.state.tasks.values()
            if task.provider_id == provider_id and self.worker_manager.is_running(task.id)
        ]
        try:
            packaged = self.providers.get_packaged(provider_id)
        except ProviderManifestError as exc:
            self._message("Provider", str(exc), QMessageBox.Icon.Warning)
            return
        if packaged is None and provider.runtime_adapter is not None:
            referenced = [task for task in self.state.tasks.values() if task.provider_id == provider_id]
            if referenced:
                names = ", ".join(task.name for task in referenced)
                self._message(
                    "Provider",
                    f"Close all Tasks that reference executable external provider {provider.name} before uninstalling it. "
                    f"Referenced: {names}.",
                    QMessageBox.Icon.Warning,
                )
                return
        if active_tasks:
            names = ", ".join(task.name for task in active_tasks)
            self._message(
                "Provider",
                f"Stop the active task before uninstalling {provider.name}. Active: {names}.",
                QMessageBox.Icon.Warning,
            )
            return

        answer = self._question(
            "Uninstall Provider",
            f"Uninstall {provider.name}? Existing accounts, protected credentials, tasks and reservations will remain saved, but this provider cannot be used to edit/re-test accounts or start/retry tasks until it is installed again.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            removed = self.providers.uninstall(provider_id)
        except ProviderManifestError as exc:
            self._message("Provider", str(exc), QMessageBox.Icon.Warning)
            return
        self.provider_runtime.reload_external_adapters()
        self.log(f"Provider uninstalled: {removed.name} v{removed.version}")
        self.providers_page.refresh()
        self.accounts_page.refresh()
        self.tasks_page.refresh()
        self._refresh_dashboard()

    def load_provider(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Provider Manifest",
            self._dialog_directory(),
            "Provider Manifest (*.json);;JSON (*.json)",
        )
        if not path:
            return
        try:
            candidate = self.providers.inspect_manifest(path)
        except ProviderManifestError as exc:
            self._message("Provider", str(exc), QMessageBox.Icon.Warning)
            return

        allow_executable = candidate.runtime_adapter is not None
        existing = self.providers.get_installed(candidate.id)
        adapter_contract_changes = bool(
            allow_executable or (existing is not None and existing.runtime_adapter is not None)
        )
        if adapter_contract_changes:
            referenced = [task for task in self.state.tasks.values() if task.provider_id == candidate.id]
            if referenced:
                names = ", ".join(task.name for task in referenced)
                self._message(
                    "Provider",
                    f"Close all Tasks that reference external provider {candidate.name} before loading, replacing, "
                    f"or removing its executable adapter contract. Referenced: {names}.",
                    QMessageBox.Icon.Warning,
                )
                return
        if allow_executable:
            answer = self._question(
                "Load Executable Provider",
                f"{candidate.name} includes executable Python adapter code. It will run in-process with Invio's "
                "application permissions and is not sandboxed. Load only code you trust. Continue?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        try:
            provider = self.providers.load_external(
                path,
                allow_executable=allow_executable,
                adapter_validator=self.provider_runtime.validate_external_adapter if allow_executable else None,
            )
        except ProviderManifestError as exc:
            self._message("Provider", str(exc), QMessageBox.Icon.Warning)
            return
        self.provider_runtime.reload_external_adapters()
        self._remember_dialog_path(path)
        status, message = self._runtime_adapter_status_for_provider(provider)
        self.log(
            f"External provider loaded: {provider.name} v{provider.version}; runtime adapter {status}. {message}",
            severity="INFO" if status in {"Executable", "Manifest only"} else "WARNING",
            category="APPLICATION",
        )
        self.providers_page.refresh()
        self.accounts_page.refresh()
        self._refresh_dashboard()

    # Accounts ----------------------------------------------------------
    def add_account(self) -> None:
        installed = self.providers.list_installed()
        if not installed:
            self._message("Accounts", "Install or load a provider from the Providers page first.", QMessageBox.Icon.Warning)
            return
        providers: list[ProviderManifest] = []
        blocked_messages: list[str] = []
        for provider in installed:
            error = self._provider_manifest_contract_error(provider)
            if error:
                blocked_messages.append(error)
            else:
                providers.append(provider)
        if not providers:
            self._message("Provider Contract", blocked_messages[0], QMessageBox.Icon.Warning)
            return
        dialog = AddAccountDialog(providers, self, provider_runtime=self.provider_runtime, log_callback=self.log)
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

    def _account_task_reference(self, account_id: str):
        task_id = self.state.account_reservations.get(account_id)
        if task_id and task_id in self.state.tasks:
            return self.state.tasks[task_id]
        return next((task for task in self.state.tasks.values() if account_id in task.account_ids), None)

    def edit_account(self, account_id: str) -> None:
        account = self.state.accounts.get(account_id)
        if account is None:
            return
        referenced_by = self._account_task_reference(account_id)
        if referenced_by is not None:
            self._message(
                "Accounts",
                f"Account '{account.name}' is assigned to {referenced_by.name}. Close that task before editing the account.",
                QMessageBox.Icon.Warning,
            )
            return
        try:
            provider = self.providers.get_installed(account.provider_id)
        except ProviderManifestError as exc:
            self._message("Accounts", str(exc), QMessageBox.Icon.Warning)
            return
        if provider is None:
            self._message(
                "Accounts",
                "Reinstall this provider before editing or re-testing the account.",
                QMessageBox.Icon.Warning,
            )
            return
        contract_error = self._provider_manifest_contract_error(provider)
        if contract_error:
            self._message("Provider Contract", contract_error, QMessageBox.Icon.Warning)
            return

        dialog = AddAccountDialog(
            [provider], self, provider_runtime=self.provider_runtime, log_callback=self.log, account=account
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        payload = dialog.payload()
        try:
            updated = self.state.update_account(
                account.id,
                name=payload["name"],
                mode=payload["mode"],
                credentials=payload["credentials"],
                status=payload["status"],
                last_verification_at=payload["last_verification_at"],
                verification_error_summary=payload["verification_error_summary"],
            )
        except StateError as exc:
            self._message("Accounts", str(exc), QMessageBox.Icon.Warning)
            return
        if updated.status == "Verified":
            self.provider_runtime.reset_account_health(updated.id, provider_id=updated.provider_id)
        self.log(f"Account updated and verified: {updated.provider_name}/{updated.name} ({updated.mode}).")
        self.accounts_page.refresh()
        self._refresh_dashboard()

    def retest_account(self, account_id: str) -> None:
        account = self.state.accounts.get(account_id)
        if account is None:
            return
        try:
            provider = self.providers.get_installed(account.provider_id)
        except ProviderManifestError as exc:
            self._message("Accounts", str(exc), QMessageBox.Icon.Warning)
            return
        if provider is None:
            self._message(
                "Accounts",
                "Reinstall this provider before editing or re-testing the account.",
                QMessageBox.Icon.Warning,
            )
            return
        contract_error = self._provider_manifest_contract_error(provider)
        if contract_error:
            self._message("Provider Contract", contract_error, QMessageBox.Icon.Warning)
            return
        if not self.provider_runtime.supports_api_test(account.provider_id):
            self._message(
                "API Test Unavailable",
                "This provider has no executable API-test adapter in the current Invio runtime.",
                QMessageBox.Icon.Warning,
            )
            return
        referenced_by = self._account_task_reference(account_id)
        if referenced_by is not None and self.worker_manager.is_running(referenced_by.id):
            self._message(
                "Accounts",
                f"Stop {referenced_by.name} before re-testing account '{account.name}'.",
                QMessageBox.Icon.Warning,
            )
            return

        dialog = AccountRetestDialog(
            account, self, provider_runtime=self.provider_runtime, log_callback=self.log
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        try:
            updated = self.state.record_account_verification(
                account.id,
                verified=dialog.verified,
                last_verification_at=dialog.last_verification_at,
                error_summary=dialog.result_message,
            )
        except StateError as exc:
            self.accounts_page.refresh()
            self.tasks_page.refresh()
            self._refresh_dashboard()
            self._message("Operational Storage", str(exc), QMessageBox.Icon.Warning)
            self.log(f"{account.provider_name}/{account.name}: API Re-test result could not be saved: {exc}")
            return

        if updated.status == "Verified":
            self.provider_runtime.reset_account_health(updated.id, provider_id=updated.provider_id)
        self.accounts_page.refresh()
        self.tasks_page.refresh()
        self._refresh_dashboard()
        if updated.status == "Verified":
            self._message("API Test", f"{updated.provider_name}/{updated.name} is verified.")
        else:
            self._message(
                "API Test Failed",
                updated.verification_error_summary or "Provider API verification failed.",
                QMessageBox.Icon.Warning,
            )

    def delete_account(self, account_id: str) -> None:
        account = self.state.accounts.get(account_id)
        if account is None:
            return
        answer = self._question(
            "Delete Account",
            f"Delete account '{account.name}' and remove its protected provider credentials?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.state.delete_account(account.id)
        except StateError as exc:
            self._message("Accounts", str(exc), QMessageBox.Icon.Warning)
            return
        self.log(f"Account deleted: {account.provider_name}/{account.name}.")
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
        """Import customer data while preserving the historical callback name."""
        customer_list = self.state.customer_lists.get(list_id)
        if not customer_list:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload Customers",
            self._dialog_directory(),
            "Customer Files (*.csv *.tsv *.xlsx *.xlsm *.txt);;All Files (*)",
        )
        if not path:
            return
        self._remember_dialog_path(path)
        try:
            imported = import_customers(path)
            merged = self.state.add_customers(list_id, imported.records, source_rows=imported.record_rows)
        except (OSError, ValueError, StateError) as exc:
            self._message("Customer List", f"Import failed: {exc}", QMessageBox.Icon.Warning)
            return

        invalid_count = len(imported.issues)
        conflict_count = len(merged.conflicts)
        duplicate_count = imported.duplicates_skipped + merged.duplicates_skipped
        self.log(
            f"Customer import for '{customer_list.name}': added={merged.added}, enriched={merged.enriched}, "
            f"duplicates={duplicate_count}, invalid/conflict={invalid_count + conflict_count}."
        )
        self.customer_page.refresh(list_id)
        self._refresh_dashboard()

        summary = [
            f"Added: {merged.added}",
            f"Enriched: {merged.enriched}",
            f"Duplicates skipped: {duplicate_count}",
            f"Invalid/conflicting rows: {invalid_count + conflict_count}",
        ]
        issue_lines = [issue.display() for issue in imported.issues] + merged.conflicts
        if issue_lines:
            preview_limit = 8
            summary.append("")
            summary.extend(issue_lines[:preview_limit])
            remaining = len(issue_lines) - preview_limit
            if remaining > 0:
                summary.append(f"... and {remaining} more issue(s).")
        icon = QMessageBox.Icon.Warning if issue_lines else QMessageBox.Icon.Information
        self._message("Customer Import", "\n".join(summary), icon)

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
        payload = dialog.payload()
        try:
            installed_provider = self.providers.get_installed(payload["provider_id"])
            packaged_provider = self.providers.get_packaged(payload["provider_id"])
        except ProviderManifestError as exc:
            self._message("Preflight Failed", f"Provider contract could not be read: {exc}", QMessageBox.Icon.Warning)
            return
        accounts = [self.state.accounts[account_id] for account_id in payload["account_ids"] if account_id in self.state.accounts]
        template = self.state.invoice_templates.get(payload["invoice_template_id"])
        customer_list = self.state.customer_lists.get(payload["customer_list_id"])
        if template is None or customer_list is None:
            self._message("Preflight Failed", "The selected Task inputs are no longer available.", QMessageBox.Icon.Warning)
            return
        injected_runner_available = payload["provider_id"] in self.task_runners
        runtime_profile = None if injected_runner_available else self.provider_runtime.capability_profile(payload["provider_id"])
        additional_issues = () if injected_runner_available else self.provider_runtime.external_task_validation_issues(
            payload["provider_id"], template, customer_list.customers
        )
        result = preflight_candidate(
            provider_id=payload["provider_id"],
            installed_manifest=installed_provider,
            packaged_manifest=packaged_provider,
            accounts=accounts,
            template=template,
            customers=customer_list.customers,
            injected_runner_available=injected_runner_available,
            runtime_profile=runtime_profile,
            additional_issues=additional_issues,
        )
        if not result.passed:
            self.log(f"New Task preflight blocked: {result.message}")
            self._message("Preflight Failed", result.message, QMessageBox.Icon.Warning)
            return
        try:
            task = self.state.create_task(**payload)
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

    def _task_continuation_message(self, task: Task, summary=None) -> str:
        if task.provider_id in self.task_runners:
            return EXTERNAL_CONTINUATION_UNAVAILABLE_MESSAGE
        if summary is not None and summary.continuation_safe:
            if (
                self.provider_runtime.external_adapter(task.provider_id) is not None
                and task.status == "Stopped"
                and summary.uncertain_recipients
                and not summary.pending_recipients
                and not summary.failed_recipients
            ):
                return (
                    "Only uncertain external-provider mutation outcomes remain. Automatic Resume is disabled to "
                    "prevent blind replay of provider operations whose outcome cannot be proven safely."
                )
            if (
                task.provider_id == "refrens"
                and task.status == "Stopped"
                and summary.uncertain_recipients
                and not summary.pending_recipients
                and not summary.failed_recipients
            ):
                return (
                    "Only uncertain Refrens provider outcomes remain. Automatic Resume is disabled because the "
                    "approved Refrens contract does not provide a provider idempotency key for safe replay."
                )
            if task.status == "Stopped" and not summary.resume_remaining_available:
                return NO_REMAINING_RECIPIENTS_MESSAGE
            if task.status == "Failed" and not summary.retry_failed_available and not summary.pending_recipients:
                return NO_FAILED_RECIPIENTS_MESSAGE
        return CONTINUATION_UNAVAILABLE_MESSAGE

    def _task_action_policy(self, task: Task) -> TaskActionPolicy:
        summary = self.provider_runtime.delivery_summary(task)
        built_in_continuation = task.provider_id not in self.task_runners
        safe_resume_available = bool(summary is not None and summary.resume_remaining_available)
        if task.provider_id == "refrens" and summary is not None:
            safe_resume_available = bool(summary.pending_recipients or summary.failed_recipients)
        if self.provider_runtime.external_adapter(task.provider_id) is not None and summary is not None:
            safe_resume_available = bool(summary.pending_recipients or summary.failed_recipients)
        resume_available = bool(
            built_in_continuation and summary is not None and safe_resume_available
        )
        retry_available = bool(
            built_in_continuation and summary is not None and summary.retry_failed_available
        )
        return task_action_policy(
            task,
            resume_remaining_available=resume_available,
            retry_failed_available=retry_available,
            continuation_unavailable_message=self._task_continuation_message(task, summary),
            active_worker_available=self.worker_manager.is_running(task.id),
        )

    def _require_task_action(self, task: Task, action: TaskAction) -> TaskExecutionMode | None:
        summary = self.provider_runtime.delivery_summary(task)
        built_in_continuation = task.provider_id not in self.task_runners
        safe_resume_available = bool(summary is not None and summary.resume_remaining_available)
        if task.provider_id == "refrens" and summary is not None:
            safe_resume_available = bool(summary.pending_recipients or summary.failed_recipients)
        if self.provider_runtime.external_adapter(task.provider_id) is not None and summary is not None:
            safe_resume_available = bool(summary.pending_recipients or summary.failed_recipients)
        resume_available = bool(
            built_in_continuation and summary is not None and safe_resume_available
        )
        retry_available = bool(
            built_in_continuation and summary is not None and summary.retry_failed_available
        )
        return require_task_action(
            task,
            action,
            resume_remaining_available=resume_available,
            retry_failed_available=retry_available,
            continuation_unavailable_message=self._task_continuation_message(task, summary),
        )

    def _require_active_worker(self, task: Task) -> None:
        if not self.worker_manager.is_running(task.id):
            raise ValueError(WORKER_NOT_ACTIVE_MESSAGE)

    def _task_action_blocked(self, task: Task, action: str, message: str) -> None:
        self.log(f"{task.name}: {action} blocked: {message}")
        self._message("Task Action Unavailable", message, QMessageBox.Icon.Warning)
        self.tasks_page.refresh_task(task.id)

    def _runner_for_task(
        self,
        task_id: str,
        *,
        retry_failed: bool = False,
        resume_remaining: bool = False,
    ) -> tuple[object | None, TaskRunner | None, str]:
        task = self.state.tasks.get(task_id)
        if not task:
            return None, None, "Task was not found."
        if self.worker_manager.is_running(task_id):
            return task, None, "A Task worker is already active; duplicate execution is not allowed."
        if not task.has_immutable_execution_snapshot:
            return task, None, LEGACY_SNAPSHOT_MESSAGE
        try:
            installed_provider = self.providers.get_installed(task.provider_id)
            packaged_provider = self.providers.get_packaged(task.provider_id)
        except ProviderManifestError as exc:
            return task, None, f"Provider installation state could not be read: {exc}"
        if installed_provider is None:
            return task, None, (
                f"{task.provider_name} is not installed. Reinstall the provider before starting or retrying this task."
            )

        accounts = []
        for account_id in task.account_ids:
            account = self.state.accounts.get(account_id)
            if account is None:
                return task, None, "A provider account assigned to this task no longer exists."
            if account.status != "Verified":
                return task, None, f"Account '{account.name}' is not verified. Run a successful API Test before starting this task."
            accounts.append(account)

        execution = task.execution_snapshot
        injected_runner_available = task.provider_id in self.task_runners
        runtime_profile = None if injected_runner_available else self.provider_runtime.capability_profile(task.provider_id)
        additional_issues = ()
        if not injected_runner_available and execution is not None and execution.template is not None:
            additional_issues = self.provider_runtime.external_task_validation_issues(
                task.provider_id, execution.template.to_template(), list(execution.customers)
            )
        result = preflight_task(
            task=task,
            installed_manifest=installed_provider,
            packaged_manifest=packaged_provider,
            accounts=accounts,
            injected_runner_available=injected_runner_available,
            runtime_profile=runtime_profile,
            additional_issues=additional_issues,
        )
        if not result.passed:
            return task, None, result.message

        injected = self.task_runners.get(task.provider_id)
        if injected is not None:
            if retry_failed or resume_remaining:
                return task, None, EXTERNAL_CONTINUATION_UNAVAILABLE_MESSAGE
            return task, injected, ""
        try:
            runner = self.provider_runtime.make_task_runner(
                task,
                self.state,
                retry_failed=retry_failed,
                resume_remaining=resume_remaining,
            )
        except ProviderRuntimeError as exc:
            return task, None, str(exc)
        return task, runner, ""

    def start_task(self, task_id: str) -> None:
        task = self.state.tasks.get(task_id)
        if task is None:
            return
        action = TaskAction.RESUME_REMAINING if task.status == "Stopped" else TaskAction.START
        try:
            mode = self._require_task_action(task, action)
        except ValueError as exc:
            self._task_action_blocked(task, action.value, str(exc))
            return

        resume_remaining = mode is TaskExecutionMode.RESUME_REMAINING
        task, runner, error = self._runner_for_task(task_id, resume_remaining=resume_remaining)
        if task is None:
            return
        if runner is None:
            message = error or "No task runner is available for this provider."
            self.tasks_page.refresh_task(task_id)
            self.log(f"{task.name}: {action.value} blocked: {message}")
            title = "Provider Unavailable" if task.has_immutable_execution_snapshot else "Task Snapshot Unavailable"
            self._message(title, f"{message} No invoice was sent.", QMessageBox.Icon.Warning)
            self._refresh_dashboard()
            return
        self.worker_manager.start(task, runner)

    def pause_task(self, task_id: str) -> None:
        task = self.state.tasks.get(task_id)
        if task is None:
            return
        try:
            self._require_task_action(task, TaskAction.PAUSE)
            self._require_active_worker(task)
        except ValueError as exc:
            self._task_action_blocked(task, "Pause", str(exc))
            return
        self.worker_manager.pause(task_id)

    def resume_task(self, task_id: str) -> None:
        task = self.state.tasks.get(task_id)
        if task is None:
            return
        try:
            self._require_task_action(task, TaskAction.RESUME)
            self._require_active_worker(task)
        except ValueError as exc:
            self._task_action_blocked(task, "Resume", str(exc))
            return
        self.worker_manager.resume(task_id)

    def stop_task(self, task_id: str) -> None:
        task = self.state.tasks.get(task_id)
        if task is None:
            return
        try:
            self._require_task_action(task, TaskAction.STOP)
            self._require_active_worker(task)
        except ValueError as exc:
            self._task_action_blocked(task, "Stop", str(exc))
            return
        self.worker_manager.stop(task_id)

    def retry_task(self, task_id: str) -> None:
        task = self.state.tasks.get(task_id)
        if task is None:
            return
        try:
            self._require_task_action(task, TaskAction.RETRY_FAILED)
        except ValueError as exc:
            self._task_action_blocked(task, "Retry Failed", str(exc))
            return
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
        try:
            self._require_task_action(task, TaskAction.CLOSE)
        except ValueError as exc:
            self._task_action_blocked(task, "Close Task", str(exc))
            return
        if self.worker_manager.is_running(task_id):
            self._message("Task", "Stop the task before closing it.", QMessageBox.Icon.Warning)
            return
        if self.app_settings.confirm_close_task:
            answer = self._question("Close Task", f"Close {task.name} and release its selected accounts?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        try:
            self.state.close_task(task_id)
        except StateError as exc:
            self._message("Task", str(exc), QMessageBox.Icon.Warning)
            self.log(f"{task.name}: close blocked because operational state could not be saved: {exc}")
            return
        self.provider_runtime.clear_task(task_id)
        self.log(f"{task.name} closed; reserved accounts released.")
        self.tasks_page.refresh()
        self.accounts_page.refresh()
        self.reports_page.refresh()
        self._refresh_dashboard()

    def _task_persistence_failure(self, task_id: str, exc: StateError) -> None:
        # Mark the fault before requesting Stop. WorkerManager.stop() emits a
        # status signal synchronously when invoked from the GUI thread, which
        # can re-enter this handler if persistence is still unavailable.
        # Registering the fault first makes that re-entrant path idempotent.
        if task_id in self._persistence_faulted_tasks:
            return
        self._persistence_faulted_tasks.add(task_id)
        self.worker_manager.stop(task_id)
        task = self.state.tasks.get(task_id)
        name = task.name if task is not None else task_id
        self.log(f"{name}: operational state persistence failed; stop requested. {exc}")
        self._message(
            "Operational Storage",
            f"{name} was stopped because its operational state could not be saved. The prior valid database transaction was retained.\n\n{exc}",
            QMessageBox.Icon.Warning,
        )

    def _worker_status(self, task_id: str, status: str, message: str) -> None:
        if task_id in self.state.tasks:
            try:
                self.state.set_task_status(task_id, status, message)
            except StateError as exc:
                self._task_persistence_failure(task_id, exc)
                return
            self.tasks_page.refresh_task(task_id)
            self.reports_page.refresh()
            self._refresh_dashboard()

    def _worker_progress(self, task_id: str, processed: int, success: int, failed: int, message: str) -> None:
        if task_id in self.state.tasks:
            try:
                self.state.set_task_progress(task_id, processed=processed, success=success, failed=failed)
                self.state.set_task_status(task_id, self.state.tasks[task_id].status, message)
            except StateError as exc:
                self._task_persistence_failure(task_id, exc)
                return
            self.tasks_page.refresh_task(task_id)
            self.reports_page.refresh()
            self._refresh_dashboard()

    def _worker_finished(self, task_id: str, status: str) -> None:
        if task_id in self.state.tasks:
            task = self.state.tasks[task_id]
            try:
                summary = self.provider_runtime.delivery_summary(task)
            except ProviderRuntimeError as exc:
                summary = None
                self.log(f"{task.name}: durable delivery summary unavailable at worker finish: {exc}")
            try:
                effective_status = reconcile_worker_terminal_status(task.status, status)
                if effective_status == "Failed" and summary is not None and summary.continuation_safe:
                    if (
                        summary.success == task.total
                        and not summary.failed_recipients
                        and not summary.pending_recipients
                        and not summary.uncertain_recipients
                    ):
                        effective_status = "Completed"
                    elif summary.pending_recipients or summary.uncertain_recipients:
                        effective_status = "Stopped"
                if summary is not None and summary.continuation_safe:
                    self.state.set_task_progress(
                        task_id,
                        processed=summary.processed,
                        success=summary.success,
                        failed=summary.failed,
                    )
                if effective_status == "Failed":
                    if summary is not None and summary.continuation_safe and summary.failed:
                        message = f"{summary.failed} recipient(s) failed. Review Live Logs and use Retry Failed."
                    else:
                        message = (
                            "Worker failed. The exact retry recipient set is unavailable, so Retry Failed is disabled."
                        )
                elif effective_status == "Stopped":
                    safe_resume_available = bool(
                        summary is not None and summary.continuation_safe and summary.resume_remaining_available
                    )
                    if task.provider_id == "refrens" and summary is not None and summary.continuation_safe:
                        safe_resume_available = bool(summary.pending_recipients or summary.failed_recipients)
                    if summary is not None and summary.continuation_safe and safe_resume_available:
                        message = (
                            f"Stopped with {summary.failed} failed, {len(summary.pending_recipients)} pending and "
                            f"{len(summary.uncertain_recipients)} uncertain recipient(s). "
                            "Use Resume Remaining to continue only the safe durable unresolved set."
                        )
                    elif (
                        task.provider_id == "refrens"
                        and summary is not None
                        and summary.continuation_safe
                        and summary.uncertain_recipients
                    ):
                        message = (
                            f"Stopped with {len(summary.uncertain_recipients)} uncertain Refrens provider outcome(s). "
                            "Automatic Resume is disabled to prevent duplicate invoice/email delivery."
                        )
                    elif summary is not None and summary.continuation_safe:
                        message = "Stopped after all recipients were resolved; there are no recipients remaining to resume."
                    else:
                        message = (
                            "Worker stopped. The exact continuation recipient set is unavailable in this session; "
                            "Resume Remaining is disabled."
                        )
                else:
                    message = f"Worker finished with status: {effective_status}"
                self.state.set_task_status(task_id, effective_status, message)
            except StateError as exc:
                self._task_persistence_failure(task_id, exc)
                return
            self._persistence_faulted_tasks.discard(task_id)
            self.tasks_page.refresh_task(task_id)
            self.reports_page.refresh()
            self._refresh_dashboard()
            self.log(f"{task.name}: worker finished with {effective_status}.")

    # Reports / logs ---------------------------------------------------
    def _export_failure(self, label: str, exc: BaseException) -> None:
        self.log(f"{label} could not be saved: {exc}", severity="ERROR", category="EXPORT")
        self._message(
            "Export Failed",
            f"{label} could not be saved. No completed export was reported.\n\n{exc}",
            QMessageBox.Icon.Warning,
        )

    def export_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Task Report", self._save_dialog_path("invio_task_report.csv"), "CSV (*.csv)"
        )
        if not path:
            return
        rows: list[list[object]] = [[
            "Task", "Provider", "Invoice Template", "Accounts", "Customer List",
            "Total", "Success", "Failed", "Remaining", "Status",
        ]]
        rows.extend(
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
            for task in self.state.tasks.values()
        )
        try:
            atomic_write_csv(path, rows)
        except (PermissionError, OSError, UnicodeError, csv.Error) as exc:
            self._export_failure("Task report", exc)
            return
        except Exception as exc:
            self._export_failure("Task report", exc)
            return
        self._remember_dialog_path(path)
        self.log(f"Task report exported: {Path(path).name}", category="EXPORT")

    def export_recipient_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Recipient Report", self._save_dialog_path("invio_recipient_report.csv"), "CSV (*.csv)"
        )
        if not path:
            return
        try:
            records = self.domain_store.recipient_delivery_report()
            rows: list[list[object]] = [[
                "Task", "Recipient", "Provider", "Safe Status", "Attempts", "Account Reference",
                "Provider Invoice", "Last Stage", "Error Code", "Provider Send Acceptance", "Email Delivery",
            ]]
            rows.extend(
                [
                    f"{record.task_name} ({record.task_id})",
                    record.recipient_email,
                    record.provider_id,
                    record.safe_status,
                    record.attempts,
                    record.account_reference,
                    record.provider_invoice_reference,
                    record.last_stage,
                    record.error_code,
                    record.provider_send_acceptance,
                    record.email_delivery,
                ]
                for record in records
            )
            atomic_write_csv(path, rows)
        except (DomainStoreError, PermissionError, OSError, UnicodeError, csv.Error) as exc:
            self._export_failure("Recipient report", exc)
            return
        except Exception as exc:
            self._export_failure("Recipient report", exc)
            return
        self._remember_dialog_path(path)
        self.log(f"Recipient report exported: {Path(path).name}", category="EXPORT")

    def clear_delivery_history(self) -> None:
        answer = self._question(
            "Clear Delivery History",
            "Delete persisted delivery history only for Tasks that are already closed? "
            "Open Task recovery records will be preserved.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            task_count, run_count = self.domain_store.clear_closed_delivery_history()
        except DomainStoreError as exc:
            self.log(f"Delivery history could not be cleared: {exc}", severity="ERROR", category="STORAGE")
            self._message("Clear Delivery History", f"Delivery history could not be cleared.\n\n{exc}", QMessageBox.Icon.Warning)
            return
        self.reports_page.refresh()
        self.log(
            f"Cleared delivery history for {task_count} closed Task(s) across {run_count} run(s); open Task recovery data was preserved.",
            category="PRIVACY",
        )

    def clear_logs(self) -> None:
        if self.app_settings.confirm_clear_logs:
            answer = self._question(
                "Clear Live Logs",
                "Clear only the current in-memory Live Logs view? Persisted delivery history will be retained.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.logs_page.clear()
        self.log("Current Live Logs view cleared; persisted delivery history was retained.", category="PRIVACY")

    def export_logs(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", self._save_dialog_path("invio_logs.txt"), "Text (*.txt)"
        )
        if not path:
            return
        try:
            atomic_write_text(path, self.logs_page.viewer.toPlainText(), encoding="utf-8")
        except (PermissionError, OSError, UnicodeError) as exc:
            self._export_failure("Live Logs", exc)
            return
        except Exception as exc:
            self._export_failure("Live Logs", exc)
            return
        self._remember_dialog_path(path)
        self.log(f"Live Logs exported: {Path(path).name}", category="EXPORT")

    def _complete_pending_shutdown(self) -> None:
        if not self._shutdown_pending or self.worker_manager.has_active_workers():
            return
        self.log("All task worker threads stopped; completing application shutdown.")
        self.close()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.worker_manager.has_active_workers():
            if not self._shutdown_pending and self.app_settings.confirm_exit_active_tasks:
                answer = self._question("Exit Invio", "Active task worker threads are running. Stop them and exit?")
                if answer != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
            if not self._shutdown_pending:
                self._shutdown_pending = True
                self.log("Application shutdown requested; waiting for active task workers to stop safely.")
                self.worker_manager.stop_all()
            event.ignore()
            return

        self._shutdown_pending = False
        geometry = self.normalGeometry() if self.isMaximized() else self.geometry()
        self.settings_manager.record_window_state(
            WindowState(geometry.x(), geometry.y(), geometry.width(), geometry.height())
        )
        event.accept()
