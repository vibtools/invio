from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QVBoxLayout, QWidget

from ...core.paths import asset_path
from ...core.provider_manager import ProviderManager, ProviderManifest
from ..widgets import button, card, label, page_header, status_badge, vbox


PROVIDER_CARD_HEIGHT = 220
PROVIDER_CARD_MIN_WIDTH = 280
PROVIDER_CARD_PADDING = 16
PROVIDER_GRID_GAP = 16
PROVIDER_SECTION_GAP = 12
PROVIDER_IDENTITY_GAP = 6
PROVIDER_LOGO_SIZE = 40
PROVIDER_MIN_COLUMNS = 2
PROVIDER_MAX_COLUMNS = 4

_ELIDE_RIGHT = getattr(Qt, "TextElide" + "Mode").ElideRight

_PROVIDER_LOGO_FILES = {
    "stripe": "stripe.png",
    "refrens": "refrens.png",
    "agiled": "agiled.png",
    "odoo": "odoo.png",
}


class _ElidedDescriptionLabel(QLabel):
    """Three-line provider description with deterministic right ellipsis."""

    def __init__(self, text: str, max_lines: int = 3):
        super().__init__()
        self._source_text = str(text).strip()
        self._max_lines = max(1, int(max_lines))
        self.setObjectName("PluginCardDescription")
        self.setWordWrap(False)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setToolTip(self._source_text)

    def _render(self) -> None:
        metrics = QFontMetrics(self.font())
        self.setFixedHeight(metrics.lineSpacing() * self._max_lines)
        width = max(1, self.contentsRect().width())
        words = self._source_text.split()
        if not words:
            QLabel.setText(self, "")
            return

        lines: list[str] = []
        index = 0
        while index < len(words) and len(lines) < self._max_lines:
            line = words[index]
            index += 1
            while index < len(words):
                candidate = f"{line} {words[index]}"
                if metrics.horizontalAdvance(candidate) > width:
                    break
                line = candidate
                index += 1
            lines.append(line)

        if index < len(words):
            remainder = " ".join([lines[-1], *words[index:]])
            lines[-1] = metrics.elidedText(remainder, _ELIDE_RIGHT, width)
        elif lines and metrics.horizontalAdvance(lines[-1]) > width:
            lines[-1] = metrics.elidedText(lines[-1], _ELIDE_RIGHT, width)

        QLabel.setText(self, "\n".join(lines))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._render()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._render()


class ProvidersPage(QWidget):
    def __init__(
        self,
        manager: ProviderManager,
        on_install: Callable[[str], None],
        on_uninstall: Callable[[str], None],
        on_load: Callable[[], None],
        runtime_capabilities: Callable[[ProviderManifest], tuple[str, ...]] | None = None,
        runtime_adapter_status: Callable[[ProviderManifest], tuple[str, str]] | None = None,
    ):
        super().__init__()
        self.manager = manager
        self.on_install = on_install
        self.on_uninstall = on_uninstall
        self.on_load = on_load
        # Retained for constructor compatibility with the frozen MainWindow/P13
        # integration. v1.41.1 intentionally does not render runtime internals.
        self.runtime_capabilities = runtime_capabilities
        self.runtime_adapter_status = runtime_adapter_status
        self._cards: list[QWidget] = []
        self._current_columns = 0
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        load = button("Load Provider", "primary")
        load.setObjectName("ProviderLoadButton")
        load.clicked.connect(self.on_load)
        root.addWidget(
            page_header(
                "Providers",
                "Install or load provider packages. Only installed providers are available to Accounts and Tasks.",
                [load],
            )
        )

        self.search_input = QLineEdit()
        self.search_input.setObjectName("ProviderSearchInput")
        self.search_input.setPlaceholderText("Search providers...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setAccessibleName("Search providers")
        self.search_input.textChanged.connect(self._apply_filter)
        root.addWidget(self.search_input)

        self.host = QWidget()
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(PROVIDER_GRID_GAP)
        self.grid.setVerticalSpacing(PROVIDER_GRID_GAP)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addWidget(self.host, 1)
        self.refresh()

    @staticmethod
    def _provider_search_text(provider: ProviderManifest, installed: bool) -> str:
        status = "verified" if installed else "available"
        return " ".join((provider.id, provider.name, provider.description, status)).casefold()

    @staticmethod
    def _provider_logo(provider: ProviderManifest) -> QLabel:
        logo = QLabel()
        logo.setObjectName("ProviderLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(PROVIDER_LOGO_SIZE, PROVIDER_LOGO_SIZE)
        logo.setToolTip(provider.name)

        filename = _PROVIDER_LOGO_FILES.get(provider.id.strip().lower())
        if filename:
            pixmap = QPixmap(str(asset_path("icons", "providers", filename)))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    PROVIDER_LOGO_SIZE,
                    PROVIDER_LOGO_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                logo.setPixmap(scaled)
        return logo

    def _provider_card(self, provider: ProviderManifest, installed: bool) -> QFrame:
        item = QFrame()
        item.setObjectName("PluginCard")
        item.setMinimumWidth(PROVIDER_CARD_MIN_WIDTH)
        item.setFixedHeight(PROVIDER_CARD_HEIGHT)
        item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        item.setProperty("providerSearchText", self._provider_search_text(provider, installed))
        layout = vbox(item, (PROVIDER_CARD_PADDING,) * 4, PROVIDER_SECTION_GAP)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)

        brand_host = QWidget()
        brand = vbox(brand_host, (0, 0, 0, 0), 4)
        brand.addWidget(self._provider_logo(provider), 0, Qt.AlignmentFlag.AlignHCenter)
        status = status_badge("Verified" if installed else "Available", "success" if installed else "neutral")
        status.setFixedHeight(22)
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.addWidget(status, 0, Qt.AlignmentFlag.AlignHCenter)
        header.addWidget(brand_host, 0, Qt.AlignmentFlag.AlignTop)

        identity_host = QWidget()
        identity = vbox(identity_host, (0, 1, 0, 0), PROVIDER_IDENTITY_GAP)
        identity.addWidget(label(provider.name, "PluginCardTitle", False))
        identity.addStretch(1)
        header.addWidget(identity_host, 1, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        description = _ElidedDescriptionLabel(provider.description, max_lines=3)
        layout.addWidget(description)

        layout.addStretch(1)
        if installed:
            action = button("Uninstall", "danger")
            action.setObjectName("ProviderUninstallButton")
            action.clicked.connect(lambda _checked=False, pid=provider.id: self.on_uninstall(pid))
        else:
            action = button("Install", "primary")
            action.clicked.connect(lambda _checked=False, pid=provider.id: self.on_install(pid))

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(6)
        footer.addWidget(action)
        footer.addStretch(1)
        version = label(f"v{provider.version}", "ProviderVersionText", False)
        version.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        footer.addWidget(version, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(footer)
        return item

    def _column_count(self) -> int:
        available_width = self.host.contentsRect().width()
        if available_width <= 0:
            available_width = max(0, self.width() - 28)
        fitting = (available_width + PROVIDER_GRID_GAP) // (PROVIDER_CARD_MIN_WIDTH + PROVIDER_GRID_GAP)
        return max(PROVIDER_MIN_COLUMNS, min(PROVIDER_MAX_COLUMNS, int(fitting)))

    def _filtered_cards(self) -> list[QWidget]:
        query = self.search_input.text().strip().casefold() if hasattr(self, "search_input") else ""
        if not query:
            return list(self._cards)
        return [item for item in self._cards if query in str(item.property("providerSearchText") or "")]

    def _reflow_cards(self, *, force: bool = False) -> None:
        columns = self._column_count()
        visible_cards = self._filtered_cards()
        if not force and columns == self._current_columns:
            return
        self._current_columns = columns
        while self.grid.count():
            self.grid.takeAt(0)
        for item in self._cards:
            item.setVisible(item in visible_cards)
        for column in range(PROVIDER_MAX_COLUMNS):
            self.grid.setColumnMinimumWidth(column, PROVIDER_CARD_MIN_WIDTH if column < columns else 0)
            self.grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, item in enumerate(visible_cards):
            row, column = divmod(index, columns)
            self.grid.addWidget(item, row, column)

    def _apply_filter(self, _text: str) -> None:
        self._reflow_cards(force=True)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if hasattr(self, "grid"):
            self._reflow_cards()

    def refresh(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        installed = self.manager.list_installed()
        installed_by_id = {provider.id: provider for provider in installed}
        installed_ids = set(installed_by_id)
        available = self.manager.list_available()
        available_ids = {provider.id for provider in available}
        # Installed cards display the actual registry declaration rather than a
        # canonical packaged look-alike, preserving the frozen P06 truth source.
        providers = [installed_by_id.get(provider.id, provider) for provider in available]
        providers.extend(provider for provider in installed if provider.id not in available_ids)
        if not providers:
            empty = card("No provider packages", "Use Load Provider to add a validated provider manifest.")
            self.grid.addWidget(empty, 0, 0)
            self._current_columns = 1
            return
        self._cards.extend(self._provider_card(provider, provider.id in installed_ids) for provider in providers)
        self._reflow_cards(force=True)
