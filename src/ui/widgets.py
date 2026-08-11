from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from math import ceil

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.paths import asset_path
from .tokens import CONST


def vbox(parent: QWidget | None = None, margins=(0, 0, 0, 0), spacing: int = 0) -> QVBoxLayout:
    layout = QVBoxLayout(parent)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def hbox(parent: QWidget | None = None, margins=(0, 0, 0, 0), spacing: int = 0) -> QHBoxLayout:
    layout = QHBoxLayout(parent)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def label(text: str, role: str = "Description", wrap: bool = True) -> QLabel:
    item = QLabel(text)
    item.setObjectName(role)
    item.setWordWrap(wrap)
    item.setMinimumWidth(0)
    item.setSizePolicy(QSizePolicy.Policy.Ignored if wrap else QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
    if not wrap:
        item.setToolTip(text)
    return item


def button(text: str, kind: str = "secondary") -> QPushButton:
    item = QPushButton(text)
    item.setCursor(Qt.CursorShape.PointingHandCursor)
    item.setAutoDefault(False)
    item.setDefault(False)
    if kind == "primary":
        item.setObjectName("PrimaryButton")
    elif kind == "danger":
        item.setObjectName("DangerButton")
    elif kind == "ghost":
        item.setObjectName("GhostButton")
    return item


def card(title: str | None = None, description: str | None = None, nested: bool = False) -> QFrame:
    frame = QFrame()
    frame.setObjectName("NestedCard" if nested else "Card")
    frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    layout = vbox(frame, (CONST.card_padding,) * 4, CONST.card_gap)
    if title:
        layout.addWidget(label(title, "CardTitle", False))
    # v1.44.0 UI scope: static card intro/subtitle descriptions are intentionally hidden.
    # Keep the argument for backward compatibility with frozen callers and helper API shape.
    _ = description
    return frame


def divider() -> QFrame:
    line = QFrame()
    line.setObjectName("Divider")
    return line


def status_badge(text: str, tone: str = "neutral") -> QLabel:
    item = label(text, "StatusBadge", False)
    mapping = {
        "success": "StatusBadgeSuccess",
        "warning": "StatusBadgeWarning",
        "danger": "StatusBadgeDanger",
        "neutral": "StatusBadge",
        "info": "StatusBadge",
    }
    item.setObjectName(mapping.get(tone, "StatusBadge"))
    item.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return item



def inline_status(text: str, tone: str = "neutral") -> QLabel:
    item = label(text, "InlineStatusNeutral", True)
    set_inline_status(item, text, tone)
    return item


def set_inline_status(item: QLabel, text: str, tone: str = "neutral") -> None:
    mapping = {
        "neutral": "InlineStatusNeutral",
        "info": "InlineStatusInfo",
        "success": "InlineStatusSuccess",
        "warning": "InlineStatusWarning",
        "danger": "InlineStatusDanger",
    }
    item.setText(str(text))
    item.setObjectName(mapping.get(tone, "InlineStatusNeutral"))
    item.style().unpolish(item)
    item.style().polish(item)

def token_chip(text: str) -> QLabel:
    item = label(text, "TokenChip", False)
    item.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return item


def metric_card(title_text: str, value: str, tone: str = "neutral") -> tuple[QFrame, QLabel]:
    frame = QFrame()
    frame.setObjectName("MetricCard")
    layout = vbox(frame, (10, 7, 10, 7), 2)
    layout.addWidget(label(title_text, "Caption", False))
    role = "MetricValueSuccess" if tone == "success" else "MetricValueDanger" if tone == "danger" else "MetricValue"
    value_label = label(value, role, False)
    layout.addWidget(value_label)
    return frame, value_label


def page_header(title_text: str, description: str, actions: Iterable[QWidget] | None = None) -> QFrame:
    header = QFrame()
    header.setObjectName("PageHeader")
    root = hbox(header, (0, 0, 0, 0), CONST.section_gap)
    title = label(title_text, "PageTitle", False)
    root.addWidget(title, 1, Qt.AlignmentFlag.AlignVCenter)
    # v1.44.0 clean-header rule: static page subtitles stay hidden.
    _ = description
    if actions:
        action_host = QWidget()
        action_host.setObjectName("PageHeaderActions")
        action_layout = hbox(action_host, (0, 0, 0, 0), CONST.space_compact)
        for action in actions:
            action_layout.addWidget(action)
        root.addWidget(action_host, 0, Qt.AlignmentFlag.AlignVCenter)
    return header


def form_group(label_text: str, field: QWidget, help_text: str = "") -> QWidget:
    host = QWidget()
    layout = vbox(host, (0, 0, 0, 0), 4)
    layout.addWidget(label(label_text, "FormLabel", False))
    layout.addWidget(field)
    if help_text:
        layout.addWidget(label(help_text, "Caption", True))
    return host


_DATA_STATUS_TONES = {
    "accepted": "success",
    "available": "success",
    "confirmed": "success",
    "delivered": "success",
    "completed": "success",
    "installed": "success",
    "protected storage": "success",
    "sent": "success",
    "succeeded": "success",
    "success": "success",
    "verified": "success",
    "error": "danger",
    "failed": "danger",
    "not installed": "danger",
    "http_400": "danger",
    "not verified": "warning",
    "api test required": "warning",
    "queued": "warning",
    "uncertain": "warning",
    "in use": "warning",
}


def data_status_tone(text: str) -> str:
    value = str(text).strip().casefold()
    if value in _DATA_STATUS_TONES:
        return _DATA_STATUS_TONES[value]
    if value.startswith("http_"):
        return "danger"
    if value.startswith("in use by "):
        return "warning"
    return "neutral"


def data_status_badge(text: str, tone: str | None = None) -> QLabel:
    item = label(str(text), "DataGridStatusNeutral", False)
    selected_tone = tone or data_status_tone(text)
    mapping = {
        "success": "DataGridStatusSuccess",
        "warning": "DataGridStatusWarning",
        "danger": "DataGridStatusDanger",
        "neutral": "DataGridStatusNeutral",
    }
    item.setObjectName(mapping.get(selected_tone, "DataGridStatusNeutral"))
    item.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    item.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return item


def data_badge_host(text: str, tone: str | None = None, *, align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft) -> QWidget:
    host = QWidget()
    host.setObjectName("DataGridBadgeHost")
    layout = hbox(host, (2, 2, 2, 2), 0)
    badge = data_status_badge(text, tone)
    if align & Qt.AlignmentFlag.AlignRight:
        layout.addStretch(1)
        layout.addWidget(badge)
    elif align & Qt.AlignmentFlag.AlignHCenter:
        layout.addStretch(1)
        layout.addWidget(badge)
        layout.addStretch(1)
    else:
        layout.addWidget(badge)
        layout.addStretch(1)
    return host


def data_table_item(
    text: object,
    *,
    right_align: bool = False,
    tooltip: str | None = None,
) -> QTableWidgetItem:
    value = str(text)
    item = QTableWidgetItem(value)
    item.setToolTip(value if tooltip is None else tooltip)
    if right_align:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    else:
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return item


class DataGridToolbar(QWidget):
    """Compact search/filter strip for presentation-only in-memory data grids."""

    def __init__(
        self,
        search_placeholder: str,
        *,
        on_changed: Callable[[], None],
        filters: Sequence[tuple[str, Sequence[tuple[str, object]]]] = (),
    ) -> None:
        super().__init__()
        self.setObjectName("DataGridToolbar")
        self._on_changed = on_changed
        layout = hbox(self, (0, 0, 0, 0), CONST.data_grid_gap)

        self.search = QLineEdit()
        self.search.setObjectName("DataGridSearchInput")
        self.search.setPlaceholderText(search_placeholder)
        self.search.setClearButtonEnabled(True)
        self.search.setMaximumWidth(CONST.data_grid_search_width)
        search_icon = asset_path("icons", "search.svg")
        if search_icon.is_file():
            self.search.addAction(QIcon(str(search_icon)), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(lambda _text: self._on_changed())
        layout.addWidget(self.search)

        layout.addStretch(1)
        self.filters: list[QComboBox] = []
        for placeholder, options in filters:
            combo = QComboBox()
            combo.setObjectName("DataGridFilter")
            combo.setAccessibleName(placeholder)
            for display, value in options:
                combo.addItem(display, value)
            combo.currentIndexChanged.connect(lambda _index: self._on_changed())
            self.filters.append(combo)
            layout.addWidget(combo)

    @property
    def query(self) -> str:
        return self.search.text().strip().casefold()

    def filter_value(self, index: int) -> object:
        return self.filters[index].currentData() if index < len(self.filters) else None

    def set_filter_options(self, index: int, options: Sequence[tuple[str, object]], *, preserve: object = None) -> None:
        if index >= len(self.filters):
            return
        combo = self.filters[index]
        current = combo.currentData() if preserve is None else preserve
        combo.blockSignals(True)
        combo.clear()
        for display, value in options:
            combo.addItem(display, value)
        match_index = combo.findData(current)
        combo.setCurrentIndex(match_index if match_index >= 0 else 0)
        combo.blockSignals(False)


class DataGridPager(QWidget):
    """Compact in-memory pagination footer. It never mutates application data."""

    def __init__(self, *, on_changed: Callable[[], None], page_sizes: Sequence[int] = (10, 25, 50)) -> None:
        super().__init__()
        self.setObjectName("DataGridFooter")
        self._on_changed = on_changed
        self.page = 1
        self.total = 0

        layout = hbox(self, (0, 0, 0, 0), CONST.data_grid_gap)
        self.summary = label("Showing 0–0 of 0", "DataGridMeta", False)
        layout.addWidget(self.summary)
        layout.addStretch(1)

        rows_label = label("Rows:", "DataGridMeta", False)
        layout.addWidget(rows_label)
        self.page_size_combo = QComboBox()
        self.page_size_combo.setObjectName("DataGridPageSize")
        for size in page_sizes:
            self.page_size_combo.addItem(str(size), int(size))
        default_index = self.page_size_combo.findData(CONST.data_grid_default_page_size)
        if default_index >= 0:
            self.page_size_combo.setCurrentIndex(default_index)
        self.page_size_combo.currentIndexChanged.connect(self._page_size_changed)
        layout.addWidget(self.page_size_combo)

        self.previous = QPushButton("<")
        self.previous.setObjectName("DataGridPageButton")
        self.previous.clicked.connect(lambda: self._move_page(-1))
        layout.addWidget(self.previous)

        self.page_buttons: list[QPushButton] = []
        for _index in range(3):
            page_button = QPushButton("")
            page_button.setObjectName("DataGridPageButton")
            page_button.clicked.connect(self._page_button_clicked)
            self.page_buttons.append(page_button)
            layout.addWidget(page_button)

        self.next = QPushButton(">")
        self.next.setObjectName("DataGridPageButton")
        self.next.clicked.connect(lambda: self._move_page(1))
        layout.addWidget(self.next)
        self.set_total(0)

    @property
    def page_size(self) -> int:
        return int(self.page_size_combo.currentData() or CONST.data_grid_default_page_size)

    @property
    def page_count(self) -> int:
        return max(1, ceil(self.total / self.page_size))

    def reset(self) -> None:
        self.page = 1

    def _page_size_changed(self, _index: int) -> None:
        self.page = 1
        self._on_changed()

    def _move_page(self, delta: int) -> None:
        target = max(1, min(self.page_count, self.page + delta))
        if target != self.page:
            self.page = target
            self._on_changed()

    def _page_button_clicked(self) -> None:
        sender = self.sender()
        if not isinstance(sender, QPushButton):
            return
        target = sender.property("pageNumber")
        if isinstance(target, int) and target != self.page:
            self.page = target
            self._on_changed()

    def set_total(self, total: int) -> tuple[int, int]:
        self.total = max(0, int(total))
        self.page = max(1, min(self.page, self.page_count))
        start = (self.page - 1) * self.page_size
        end = min(self.total, start + self.page_size)
        if self.total:
            self.summary.setText(f"Showing {start + 1}–{end} of {self.total}")
        else:
            self.summary.setText("Showing 0–0 of 0")
        self.previous.setEnabled(self.page > 1)
        self.next.setEnabled(self.page < self.page_count)
        self._refresh_page_buttons()
        return start, end

    def _refresh_page_buttons(self) -> None:
        count = self.page_count
        if count <= 3:
            pages = list(range(1, count + 1))
        elif self.page <= 2:
            pages = [1, 2, 3]
        elif self.page >= count - 1:
            pages = [count - 2, count - 1, count]
        else:
            pages = [self.page - 1, self.page, self.page + 1]
        for index, page_button in enumerate(self.page_buttons):
            if index < len(pages):
                page_number = pages[index]
                page_button.setText(str(page_number))
                page_button.setProperty("pageNumber", page_number)
                page_button.setProperty("currentPage", page_number == self.page)
                page_button.setVisible(True)
                page_button.style().unpolish(page_button)
                page_button.style().polish(page_button)
            else:
                page_button.setVisible(False)


def data_grid_empty_label(text: str) -> QLabel:
    item = label(text, "DataGridEmpty", False)
    item.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return item
