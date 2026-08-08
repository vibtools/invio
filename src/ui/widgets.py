from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

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
    if description:
        layout.addWidget(label(description, "Description", True))
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
    root = hbox(header, (0, 0, 0, 0), 10)
    text_host = QWidget()
    text_layout = vbox(text_host, (0, 0, 0, 0), 3)
    text_layout.addWidget(label(title_text, "PageTitle", False))
    text_layout.addWidget(label(description, "Description", True))
    root.addWidget(text_host, 1)
    if actions:
        action_host = QWidget()
        action_layout = hbox(action_host, (0, 2, 0, 0), 5)
        for action in actions:
            action_layout.addWidget(action)
        root.addWidget(action_host, 0, Qt.AlignmentFlag.AlignTop)
    return header


def form_group(label_text: str, field: QWidget, help_text: str = "") -> QWidget:
    host = QWidget()
    layout = vbox(host, (0, 0, 0, 0), 4)
    layout.addWidget(label(label_text, "FormLabel", False))
    layout.addWidget(field)
    if help_text:
        layout.addWidget(label(help_text, "Caption", True))
    return host
