from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
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
from ..tokens import CONST
from ..widgets import button, card, form_group, label

SaveSettingsHandler = Callable[[AppSettings], tuple[bool, str]]

_SETTINGS_MIN_CARD_WIDTH = 360
_SETTINGS_GRID_GAP = 12
_SETTINGS_COUNTRY_FIELD_WIDTH = 120


class SettingsPage(QWidget):
    """User-facing controls for Invio's persistent application preferences."""

    def __init__(self, settings: AppSettings, on_save: SaveSettingsHandler):
        super().__init__()
        self._on_save = on_save
        self.setObjectName("SettingsPage")
        self._settings_cards: list[tuple[QWidget, str]] = []
        self._settings_matches: dict[QWidget, bool] = {}
        self._settings_columns = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(CONST.page_padding, CONST.page_padding, CONST.page_padding, CONST.page_padding)
        root.setSpacing(CONST.section_gap)

        # Header --------------------------------------------------------
        header = QWidget()
        header.setObjectName("SettingsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        header_layout.addWidget(label("Settings", "PageTitle", False))

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SettingsSearchInput")
        self.search_input.setPlaceholderText("Search settings... (Ctrl+F)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_settings_cards)
        header_layout.addWidget(self.search_input, 1)

        restore = button("Reset Settings")
        restore.setObjectName("SettingsResetButton")
        save = button("Save Changes", "primary")
        restore.clicked.connect(self._restore_defaults)
        save.clicked.connect(self._save)
        header_layout.addWidget(restore)
        header_layout.addWidget(save)
        root.addWidget(header)

        find_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        find_shortcut.activated.connect(self._focus_search)
        self._find_shortcut = find_shortcut

        scroll = QScrollArea()
        scroll.setObjectName("MinimalScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("SettingsContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(CONST.section_gap)

        self.settings_grid = QGridLayout()
        self.settings_grid.setHorizontalSpacing(_SETTINGS_GRID_GAP)
        self.settings_grid.setVerticalSpacing(_SETTINGS_GRID_GAP)
        self.settings_grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        # General -------------------------------------------------------
        general = card("Startup & Window")
        self.start_page = QComboBox()
        self.start_page.addItem("Last page used", START_PAGE_LAST)
        for page_name in START_PAGES:
            self.start_page.addItem(page_name, page_name)
        general.layout().addWidget(form_group("Open Invio on", self.start_page))

        self.remember_window = QCheckBox("Remember window size and position")
        general.layout().addWidget(self.remember_window)
        self._register_settings_card(
            general,
            "startup window open invio last page dashboard accounts invoice templates customer lists tasks providers reports live logs settings remember window size position",
        )

        # Safety --------------------------------------------------------
        safety = card("Confirmations")
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
        self._register_settings_card(
            safety,
            "confirmations ask before exiting tasks running closing task deleting invoice template customer list clearing live logs",
        )

        # Logs ----------------------------------------------------------
        logs = card("Live Logs")
        self.show_log_timestamps = QCheckBox("Show time on each log entry")
        self.auto_scroll_logs = QCheckBox("Automatically follow the newest log entry")
        logs.layout().addWidget(self.show_log_timestamps)
        logs.layout().addWidget(self.auto_scroll_logs)

        self.max_log_entries = QSpinBox()
        self.max_log_entries.setRange(0, 100000)
        self.max_log_entries.setSpecialValueText("Unlimited")
        self.max_log_entries.setSuffix(" lines")
        logs.layout().addWidget(form_group("Maximum log lines", self.max_log_entries))
        self._register_settings_card(
            logs,
            "live logs time timestamp automatically follow newest log entry maximum log lines unlimited retention",
        )

        # Files ---------------------------------------------------------
        files = card("File Locations")
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
        files.layout().addWidget(form_group("Default file folder", folder_row))
        self.remember_last_folder = QCheckBox("Remember the last folder I used")
        files.layout().addWidget(self.remember_last_folder)
        self._register_settings_card(
            files,
            "file locations default file folder system folder browse remember last folder provider loading customer imports report exports log exports",
        )

        # Customer defaults --------------------------------------------
        customer_defaults = card("Customer Defaults")
        self.default_customer_name = QLineEdit()
        self.default_customer_name.setPlaceholderText("Use email username")
        self.default_customer_country = QLineEdit()
        self.default_customer_country.setMaxLength(2)
        self.default_customer_country.setMaximumWidth(_SETTINGS_COUNTRY_FIELD_WIDTH)
        self.default_customer_country.setPlaceholderText("US")

        defaults_grid = QGridLayout()
        defaults_grid.setContentsMargins(0, 0, 0, 0)
        defaults_grid.setHorizontalSpacing(8)
        defaults_grid.setVerticalSpacing(8)
        defaults_grid.addWidget(form_group("Default customer name", self.default_customer_name), 0, 0)
        defaults_grid.addWidget(form_group("Default customer country", self.default_customer_country), 0, 1)
        defaults_grid.setColumnStretch(0, 1)
        defaults_grid.setColumnStretch(1, 0)
        customer_defaults.layout().addLayout(defaults_grid)
        self._register_settings_card(
            customer_defaults,
            "customer defaults default customer name country email username two letter country code us import missing identity",
        )
        self._customer_defaults_card = customer_defaults

        for settings_card, _keywords in self._settings_cards:
            settings_card.setProperty("settingsCard", True)
            settings_card.layout().setContentsMargins(
                CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding
            )
            settings_card.layout().setSpacing(CONST.dialog_gap)

        content_layout.addLayout(self.settings_grid)

        self.feedback = label("Changes are applied after you select Save Changes.", "Caption")
        content_layout.addWidget(self.feedback)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        self._settings_scroll = scroll

        self.load_settings(settings)
        self._reflow_settings_grid(force=True)

    def _register_settings_card(self, settings_card: QWidget, keywords: str) -> None:
        searchable = f"{keywords} {settings_card.windowTitle()}".casefold()
        self._settings_cards.append((settings_card, searchable))
        self._settings_matches[settings_card] = True

    def _focus_search(self) -> None:
        self.search_input.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search_input.selectAll()

    def _filter_settings_cards(self, text: str) -> None:
        query = " ".join(str(text).casefold().split())
        terms = tuple(query.split())
        for settings_card, searchable in self._settings_cards:
            matches = not terms or all(term in searchable for term in terms)
            self._settings_matches[settings_card] = matches
            settings_card.setVisible(matches)
        self._reflow_settings_grid(force=True)

    def _column_count(self) -> int:
        available = max(0, self.width() - (CONST.page_padding * 2))
        return 2 if available >= (_SETTINGS_MIN_CARD_WIDTH * 2 + _SETTINGS_GRID_GAP) else 1

    def _reflow_settings_grid(self, *, force: bool = False) -> None:
        columns = self._column_count()
        if not force and columns == self._settings_columns:
            return
        self._settings_columns = columns

        while self.settings_grid.count():
            self.settings_grid.takeAt(0)

        row = 0
        column = 0
        for settings_card, _keywords in self._settings_cards:
            if not self._settings_matches.get(settings_card, True):
                continue
            if settings_card is self._customer_defaults_card and columns == 2:
                if column:
                    row += 1
                    column = 0
                self.settings_grid.addWidget(settings_card, row, 0, 1, 2)
                row += 1
                continue
            self.settings_grid.addWidget(settings_card, row, column)
            column += 1
            if column >= columns:
                row += 1
                column = 0

        for index in range(2):
            self.settings_grid.setColumnStretch(index, 1 if index < columns else 0)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self._reflow_settings_grid()
        super().resizeEvent(event)

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
