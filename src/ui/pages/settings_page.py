from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...core.settings import START_PAGE_LAST, START_PAGES, AppSettings, SettingsManager
from ..widgets import button, card, form_group, label, page_header

SaveSettingsHandler = Callable[[AppSettings], tuple[bool, str]]


class SettingsPage(QWidget):
    """User-facing controls for Invio's persistent application preferences."""

    def __init__(self, settings: AppSettings, on_save: SaveSettingsHandler):
        super().__init__()
        self._on_save = on_save
        self.setObjectName("SettingsPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(8)

        restore = button("Restore Defaults")
        save = button("Save Changes", "primary")
        restore.clicked.connect(self._restore_defaults)
        save.clicked.connect(self._save)
        root.addWidget(
            page_header(
                "Settings",
                "Control how Invio starts, asks for confirmation, handles logs, and opens files. Settings are saved locally on this computer.",
                [restore, save],
            )
        )

        scroll = QScrollArea()
        scroll.setObjectName("MinimalScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("SettingsContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        # General -------------------------------------------------------
        general = card(
            "Startup & Window",
            "Choose what you see when Invio opens and whether the last window size and position are remembered.",
        )
        self.start_page = QComboBox()
        self.start_page.addItem("Last page used", START_PAGE_LAST)
        for page_name in START_PAGES:
            self.start_page.addItem(page_name, page_name)
        general.layout().addWidget(form_group("Open Invio on", self.start_page))

        self.remember_window = QCheckBox("Remember window size and position")
        general.layout().addWidget(self.remember_window)
        general.layout().addWidget(
            label(
                "When this is off, Invio opens with the standard application window size.",
                "Caption",
            )
        )
        grid.addWidget(general, 0, 0)

        # Safety --------------------------------------------------------
        safety = card(
            "Confirmations",
            "Keep confirmation prompts for actions that may stop work or remove information. Turn off only the prompts you do not need.",
        )
        self.confirm_exit_active_tasks = QCheckBox("Ask before exiting while tasks are running")
        self.confirm_close_task = QCheckBox("Ask before closing a task")
        self.confirm_delete_template = QCheckBox("Ask before deleting an invoice template")
        self.confirm_delete_customer_list = QCheckBox("Ask before deleting a customer list")
        self.confirm_clear_logs = QCheckBox("Ask before clearing Live Logs")
        for control in (
            self.confirm_exit_active_tasks,
            self.confirm_close_task,
            self.confirm_delete_template,
            self.confirm_delete_customer_list,
            self.confirm_clear_logs,
        ):
            safety.layout().addWidget(control)
        grid.addWidget(safety, 0, 1)

        # Logs ----------------------------------------------------------
        logs = card(
            "Live Logs",
            "Control how the Live Logs page displays and retains application messages. Secret-like Stripe keys continue to be masked regardless of these settings.",
        )
        self.show_log_timestamps = QCheckBox("Show time on each log entry")
        self.auto_scroll_logs = QCheckBox("Automatically follow the newest log entry")
        logs.layout().addWidget(self.show_log_timestamps)
        logs.layout().addWidget(self.auto_scroll_logs)

        self.max_log_entries = QSpinBox()
        self.max_log_entries.setRange(0, 100000)
        self.max_log_entries.setSpecialValueText("Unlimited")
        self.max_log_entries.setSuffix(" lines")
        logs.layout().addWidget(
            form_group(
                "Maximum log lines",
                self.max_log_entries,
                "Use Unlimited to keep all log lines for the current application session.",
            )
        )
        grid.addWidget(logs, 1, 0)

        # Files ---------------------------------------------------------
        files = card(
            "File Locations",
            "Choose the starting folder used by provider loading, customer imports, report exports, and log exports.",
        )
        self.default_file_folder = QLineEdit()
        self.default_file_folder.setPlaceholderText("Use the system default folder")
        browse = button("Browse")
        browse.clicked.connect(self._browse_folder)
        folder_row = QWidget()
        folder_layout = QHBoxLayout(folder_row)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(6)
        folder_layout.addWidget(self.default_file_folder, 1)
        folder_layout.addWidget(browse)
        files.layout().addWidget(
            form_group(
                "Default file folder",
                folder_row,
                "Leave blank to let the operating system choose the starting folder.",
            )
        )
        self.remember_last_folder = QCheckBox("Remember the last folder I used")
        files.layout().addWidget(self.remember_last_folder)
        files.layout().addWidget(
            label(
                "Only application preferences and folder paths are stored here. Account credentials are not written to the settings file.",
                "Caption",
            )
        )
        grid.addWidget(files, 1, 1)

        # Customer defaults ----------------------------------------------
        customer_defaults = card(
            "Customer Defaults",
            "Fill missing customer identity data during import so email-only lists are immediately usable by providers that require name and country.",
        )
        self.default_customer_name = QLineEdit()
        self.default_customer_name.setPlaceholderText("Use email username")
        customer_defaults.layout().addWidget(
            form_group(
                "Default customer name",
                self.default_customer_name,
                "If set, this value is used when an imported customer has no name. If blank, Invio uses the email username.",
            )
        )
        self.default_customer_country = QLineEdit()
        self.default_customer_country.setMaxLength(2)
        self.default_customer_country.setPlaceholderText("US")
        customer_defaults.layout().addWidget(
            form_group(
                "Default customer country",
                self.default_customer_country,
                "Use a two-letter country code. If blank, Invio uses US for imported customers that have no country.",
            )
        )
        grid.addWidget(customer_defaults, 2, 0, 1, 2)

        for settings_card in (general, safety, logs, files, customer_defaults):
            settings_card.setProperty("settingsCard", True)
            settings_card.layout().setContentsMargins(12, 11, 12, 11)
            settings_card.layout().setSpacing(5)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        content_layout.addLayout(grid)

        self.feedback = label("Changes are applied after you select Save Changes.", "Caption")
        content_layout.addWidget(self.feedback)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self.load_settings(settings)

    def load_settings(self, settings: AppSettings) -> None:
        index = self.start_page.findData(settings.start_page)
        self.start_page.setCurrentIndex(index if index >= 0 else self.start_page.findData("Accounts"))
        self.remember_window.setChecked(settings.remember_window)

        self.confirm_exit_active_tasks.setChecked(settings.confirm_exit_active_tasks)
        self.confirm_close_task.setChecked(settings.confirm_close_task)
        self.confirm_delete_template.setChecked(settings.confirm_delete_template)
        self.confirm_delete_customer_list.setChecked(settings.confirm_delete_customer_list)
        self.confirm_clear_logs.setChecked(settings.confirm_clear_logs)

        self.show_log_timestamps.setChecked(settings.show_log_timestamps)
        self.auto_scroll_logs.setChecked(settings.auto_scroll_logs)
        self.max_log_entries.setValue(settings.max_log_entries)

        self.default_file_folder.setText(settings.default_file_folder)
        self.remember_last_folder.setChecked(settings.remember_last_folder)
        self.default_customer_name.setText(settings.default_customer_name)
        self.default_customer_country.setText(settings.default_customer_country)

    def _collect_settings(self) -> AppSettings:
        return AppSettings(
            start_page=str(self.start_page.currentData()),
            remember_window=self.remember_window.isChecked(),
            confirm_exit_active_tasks=self.confirm_exit_active_tasks.isChecked(),
            confirm_close_task=self.confirm_close_task.isChecked(),
            confirm_delete_template=self.confirm_delete_template.isChecked(),
            confirm_delete_customer_list=self.confirm_delete_customer_list.isChecked(),
            confirm_clear_logs=self.confirm_clear_logs.isChecked(),
            show_log_timestamps=self.show_log_timestamps.isChecked(),
            auto_scroll_logs=self.auto_scroll_logs.isChecked(),
            max_log_entries=self.max_log_entries.value(),
            default_file_folder=self.default_file_folder.text().strip(),
            remember_last_folder=self.remember_last_folder.isChecked(),
            default_customer_name=self.default_customer_name.text().strip(),
            default_customer_country=self.default_customer_country.text().strip(),
        )

    def _save(self) -> None:
        ok, message = self._on_save(self._collect_settings())
        self.feedback.setText(message)
        if ok:
            self.feedback.setObjectName("Caption")
            self.style().unpolish(self.feedback)
            self.style().polish(self.feedback)

    def _restore_defaults(self) -> None:
        self.load_settings(SettingsManager.defaults())
        self.feedback.setText("Default values loaded. Select Save Changes to apply them.")

    def _browse_folder(self) -> None:
        current = self.default_file_folder.text().strip()
        initial = current if current and Path(current).is_dir() else str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Select Default File Folder", initial)
        if selected:
            self.default_file_folder.setText(selected)
