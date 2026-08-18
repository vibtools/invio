from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...core.settings import (
    MAX_AUTOMATIC_ATTEMPTS_LIMIT,
    NETWORK_TIMEOUT_MAX_SECONDS,
    NETWORK_TIMEOUT_MIN_SECONDS,
    RECIPIENT_DELAY_MAX_SECONDS,
    START_PAGE_LAST,
    START_PAGES,
    AppSettings,
    SettingsManager,
)
from ..tokens import CONST
from ..widgets import button, card, form_group, label, page_header, section_toolbar

SaveSettingsHandler = Callable[[AppSettings], tuple[bool, str]]

_SETTINGS_MIN_CARD_WIDTH = 360
_SETTINGS_GRID_GAP = 12
_SETTINGS_COUNTRY_FIELD_WIDTH = 120


class SettingsPage(QWidget):
    """User-facing controls for Invio's persistent application preferences."""

    def __init__(
        self,
        settings: AppSettings,
        on_save: SaveSettingsHandler,
        provider_rate_limits: dict[str, tuple[str, float | None]] | None = None,
    ):
        super().__init__()
        self._on_save = on_save
        self.setObjectName("SettingsPage")
        self._settings_cards: list[tuple[QWidget, str]] = []
        self._settings_matches: dict[QWidget, bool] = {}
        self._settings_columns = 0
        self._provider_rate_limits = dict(provider_rate_limits or {})
        self._provider_rate_controls: dict[str, tuple[QComboBox, QDoubleSpinBox, float | None]] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(CONST.page_padding, CONST.page_padding, CONST.page_padding, CONST.page_padding)
        root.setSpacing(CONST.space_compact)

        # Frozen compact page header + section toolbar.
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SettingsSearchInput")
        self.search_input.setPlaceholderText("Search settings... (Ctrl+F)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(180)
        self.search_input.setMaximumWidth(CONST.data_grid_search_width)
        self.search_input.textChanged.connect(self._filter_settings_cards)

        restore = button("Reset Settings")
        restore.setObjectName("SettingsResetButton")
        save = button("Save Changes", "primary")
        restore.clicked.connect(self._restore_defaults)
        save.clicked.connect(self._save)
        root.addWidget(page_header("Settings", "Persistent application preferences.", [restore, save]))
        root.addWidget(section_toolbar("Preferences", (self.search_input,)))

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

        # Sending & retry ----------------------------------------------
        sending = card("Sending & Retry")
        self.network_timeout_seconds = QDoubleSpinBox()
        self.network_timeout_seconds.setRange(NETWORK_TIMEOUT_MIN_SECONDS, NETWORK_TIMEOUT_MAX_SECONDS)
        self.network_timeout_seconds.setDecimals(0)
        self.network_timeout_seconds.setSingleStep(5.0)
        self.network_timeout_seconds.setSuffix(" sec")
        sending.layout().addWidget(form_group("Task network timeout", self.network_timeout_seconds))

        self.max_automatic_attempts = QSpinBox()
        self.max_automatic_attempts.setRange(1, MAX_AUTOMATIC_ATTEMPTS_LIMIT)
        self.max_automatic_attempts.setSuffix(" attempts")
        sending.layout().addWidget(form_group("Maximum automatic attempts", self.max_automatic_attempts))

        self.additional_recipient_delay_seconds = QDoubleSpinBox()
        self.additional_recipient_delay_seconds.setRange(0.0, RECIPIENT_DELAY_MAX_SECONDS)
        self.additional_recipient_delay_seconds.setDecimals(1)
        self.additional_recipient_delay_seconds.setSingleStep(0.5)
        self.additional_recipient_delay_seconds.setSuffix(" sec")
        sending.layout().addWidget(form_group("Additional recipient delay", self.additional_recipient_delay_seconds))
        self._register_settings_card(
            sending,
            "sending retry task network timeout automatic attempts additional recipient delay bounded retry after",
        )

        # Provider rate limits -----------------------------------------
        self.provider_rates_card = card("Provider Rate Limits")
        self.provider_rates_container = QWidget()
        self.provider_rates_layout = QVBoxLayout(self.provider_rates_container)
        self.provider_rates_layout.setContentsMargins(0, 0, 0, 0)
        self.provider_rates_layout.setSpacing(8)
        self.provider_rates_card.layout().addWidget(self.provider_rates_container)
        self._register_settings_card(
            self.provider_rates_card,
            "provider rate limits requests per second account ceiling stripe refrens odoo custom lower rate",
        )
        self._rebuild_provider_rate_rows(settings)

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

    def set_provider_rate_limits(
        self,
        provider_rate_limits: dict[str, tuple[str, float | None]],
        settings: AppSettings | None = None,
    ) -> None:
        self._provider_rate_limits = dict(provider_rate_limits)
        self._rebuild_provider_rate_rows(settings or self._collect_settings())

    def _rebuild_provider_rate_rows(self, settings: AppSettings) -> None:
        while self.provider_rates_layout.count():
            item = self.provider_rates_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._provider_rate_controls.clear()

        if not self._provider_rate_limits:
            self.provider_rates_layout.addWidget(label("No installed Task provider declares a rate policy.", "Caption"))
            return

        for provider_id, (provider_name, ceiling) in sorted(
            self._provider_rate_limits.items(), key=lambda item: item[1][0].casefold()
        ):
            row = QWidget()
            grid = QGridLayout(row)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(8)
            grid.setVerticalSpacing(4)
            grid.addWidget(label(provider_name, "Body"), 0, 0)

            if ceiling is None:
                grid.addWidget(label("Approved ceiling: Not declared", "Caption"), 0, 1)
                mode = QComboBox()
                mode.addItem("Custom rate unavailable", "unavailable")
                mode.setEnabled(False)
                rate = QDoubleSpinBox()
                rate.setRange(0.001, 1000000.0)
                rate.setDecimals(3)
                rate.setEnabled(False)
                grid.addWidget(mode, 1, 0)
                grid.addWidget(rate, 1, 1)
                self._provider_rate_controls[provider_id] = (mode, rate, None)
            else:
                grid.addWidget(label(f"Approved ceiling: {ceiling:g} req/s/account", "Caption"), 0, 1)
                mode = QComboBox()
                mode.addItem("Provider default", "default")
                mode.addItem("Custom lower rate", "custom")
                rate = QDoubleSpinBox()
                rate.setRange(0.001, float(ceiling))
                rate.setDecimals(3)
                rate.setSingleStep(min(1.0, max(0.001, float(ceiling) / 10.0)))
                rate.setSuffix(" req/s/account")
                custom_value = settings.provider_rate_overrides.get(provider_id)
                if custom_value is not None:
                    mode.setCurrentIndex(mode.findData("custom"))
                    rate.setValue(min(float(ceiling), float(custom_value)))
                else:
                    rate.setValue(float(ceiling))
                rate.setEnabled(mode.currentData() == "custom")
                mode.currentIndexChanged.connect(
                    lambda _index, combo=mode, control=rate: control.setEnabled(combo.currentData() == "custom")
                )
                grid.addWidget(mode, 1, 0)
                grid.addWidget(rate, 1, 1)
                self._provider_rate_controls[provider_id] = (mode, rate, float(ceiling))
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)
            self.provider_rates_layout.addWidget(row)

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
        self.network_timeout_seconds.setValue(settings.network_timeout_seconds)
        self.max_automatic_attempts.setValue(settings.max_automatic_attempts)
        self.additional_recipient_delay_seconds.setValue(settings.additional_recipient_delay_seconds)
        self._rebuild_provider_rate_rows(settings)

    def _collect_settings(self) -> AppSettings:
        provider_rate_overrides: dict[str, float] = {}
        for provider_id, (mode, rate, ceiling) in self._provider_rate_controls.items():
            if ceiling is not None and mode.currentData() == "custom":
                provider_rate_overrides[provider_id] = float(rate.value())
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
            network_timeout_seconds=self.network_timeout_seconds.value(),
            max_automatic_attempts=self.max_automatic_attempts.value(),
            additional_recipient_delay_seconds=self.additional_recipient_delay_seconds.value(),
            provider_rate_overrides=provider_rate_overrides,
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
