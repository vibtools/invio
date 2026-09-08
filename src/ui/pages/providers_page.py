from __future__ import annotations

import base64
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.paths import asset_path
from ...core.provider_manager import ProviderManager, ProviderManifest, RemoteProviderInfo
from ..tokens import CONST
from ..widgets import button, card, label, page_header, section_toolbar, status_badge, vbox


PROVIDER_CARD_HEIGHT = 188
PROVIDER_CARD_MIN_WIDTH = 280
PROVIDER_CARD_PADDING = 14
PROVIDER_GRID_GAP = 12
PROVIDER_SECTION_GAP = 10
PROVIDER_IDENTITY_GAP = 4
PROVIDER_STATUS_HEIGHT = 18
PROVIDER_LOGO_SIZE = 40
PROVIDER_MIN_COLUMNS = 2
PROVIDER_MAX_COLUMNS = 3

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
        on_install_remote: Callable[[RemoteProviderInfo], None] | None = None,
        on_refresh_remote: Callable[[], None] | None = None,
        on_open_license: Callable[[ProviderManifest], None] | None = None,
        is_licensed: Callable[[str], bool] | None = None,
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
        self.on_install_remote = on_install_remote
        self.on_refresh_remote = on_refresh_remote
        self.on_open_license = on_open_license
        self.is_licensed = is_licensed
        self._cards: list[QWidget] = []
        self._current_columns = 0
        self._remote_items: list[RemoteProviderInfo] = []
        self._remote_loading = False
        self._remote_error: str | None = None
        self._remote_busy_ids: set[int] = set()
        self._remote_cards: list[QWidget] = []
        self._remote_current_columns = 0
        self.setObjectName("PageContent")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(CONST.space_compact)

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
        self.search_input.setMinimumWidth(180)
        self.search_input.setMaximumWidth(CONST.data_grid_search_width)
        self.search_input.textChanged.connect(self._apply_filter)

        # Both the local grid and the Online Provider Catalog can grow past one
        # screen (multiple rows, or several online providers) - the page header
        # and search/refresh toolbars stay put while this scroll area carries
        # everything below them, matching the SettingsPage scroll pattern.
        scroll = QScrollArea()
        scroll.setObjectName("MinimalScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("ProvidersScrollContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(CONST.space_compact)

        content_layout.addWidget(section_toolbar("Provider Catalog", (self.search_input,)))

        self.host = QWidget()
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(PROVIDER_GRID_GAP)
        self.grid.setVerticalSpacing(PROVIDER_GRID_GAP)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.addWidget(self.host, 0)

        self.online_refresh_button = button("Refresh", "ghost")
        self.online_refresh_button.clicked.connect(self._handle_refresh_remote_clicked)
        content_layout.addWidget(
            section_toolbar("Online Provider Catalog (invio.vib.tools)", (self.online_refresh_button,))
        )

        self.online_status_label = label("", "Caption", True)
        self.online_status_label.setVisible(False)
        content_layout.addWidget(self.online_status_label)

        self.online_host = QWidget()
        self.online_grid = QGridLayout(self.online_host)
        self.online_grid.setContentsMargins(0, 0, 0, 0)
        self.online_grid.setHorizontalSpacing(PROVIDER_GRID_GAP)
        self.online_grid.setVerticalSpacing(PROVIDER_GRID_GAP)
        self.online_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.addWidget(self.online_host, 0)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self.refresh()
        self._reflow_remote_cards(force=True)

    @staticmethod
    def _provider_search_text(provider: ProviderManifest, installed: bool) -> str:
        status = "verified" if installed else "available"
        return " ".join((provider.id, provider.name, provider.description, status)).casefold()

    def _provider_logo(self, provider: ProviderManifest) -> QLabel:
        logo = QLabel()
        logo.setObjectName("ProviderLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(PROVIDER_LOGO_SIZE, PROVIDER_LOGO_SIZE)
        logo.setToolTip(provider.name)

        candidates: list[Path] = []
        logo_resolver = getattr(self.manager, "provider_logo_path", None)
        if callable(logo_resolver):
            plugin_logo = logo_resolver(provider.id)
            if plugin_logo is not None:
                candidates.append(Path(plugin_logo))
        filename = _PROVIDER_LOGO_FILES.get(provider.id.strip().lower())
        if filename:
            candidates.append(asset_path("icons", "providers", filename))
        candidates.append(asset_path("icons", "providers", "fallback.png"))

        for path in candidates:
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                continue
            scaled = pixmap.scaled(
                PROVIDER_LOGO_SIZE,
                PROVIDER_LOGO_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo.setPixmap(scaled)
            break
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

        header.addWidget(self._provider_logo(provider), 0, Qt.AlignmentFlag.AlignTop)

        licensed = installed and callable(self.is_licensed) and self.is_licensed(provider.id)

        identity_host = QWidget()
        identity = vbox(identity_host, (0, 1, 0, 0), PROVIDER_IDENTITY_GAP)
        identity.addWidget(label(provider.name, "PluginCardTitle", False))
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 0, 0, 0)
        badge_row.setSpacing(4)
        status = status_badge("Verified" if installed else "Available")
        status.setFixedHeight(PROVIDER_STATUS_HEIGHT)
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_row.addWidget(status, 0, Qt.AlignmentFlag.AlignLeft)
        if licensed:
            licensed_badge = status_badge("Licensed", "success")
            licensed_badge.setFixedHeight(PROVIDER_STATUS_HEIGHT)
            licensed_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge_row.addWidget(licensed_badge, 0, Qt.AlignmentFlag.AlignLeft)
        badge_row.addStretch(1)
        identity.addLayout(badge_row)
        identity.addStretch(1)
        header.addWidget(identity_host, 1, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        description = _ElidedDescriptionLabel(provider.description, max_lines=3)
        layout.addWidget(description)

        layout.addStretch(1)
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(6)
        if installed:
            uninstall_action = button("Uninstall", "danger")
            uninstall_action.setObjectName("ProviderUninstallButton")
            uninstall_action.clicked.connect(lambda _checked=False, pid=provider.id: self.on_uninstall(pid))
            footer.addWidget(uninstall_action)
            if self.on_open_license is not None:
                license_action = button("Re-license" if licensed else "License", "ghost" if licensed else "primary")
                license_action.setObjectName("ProviderLicenseButton")
                license_action.clicked.connect(lambda _checked=False, p=provider: self.on_open_license(p))
                footer.addWidget(license_action)
        else:
            action = button("Install", "primary")
            action.clicked.connect(lambda _checked=False, pid=provider.id: self.on_install(pid))
            footer.addWidget(action)
        footer.addStretch(1)
        version = label(f"v{provider.version}", "ProviderVersionText", False)
        version.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        footer.addWidget(version, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(footer)
        return item

    @staticmethod
    def _remote_logo_pixmap(info: RemoteProviderInfo) -> QPixmap | None:
        """Decode the registry-supplied logo (a data: URL) for the Online Provider Catalog card."""
        data_url = info.logo_data_url
        if not data_url or "," not in data_url:
            return None
        try:
            raw = base64.b64decode(data_url.split(",", 1)[1], validate=False)
        except (ValueError, TypeError):
            return None
        pixmap = QPixmap()
        if not pixmap.loadFromData(raw) or pixmap.isNull():
            return None
        return pixmap

    def _remote_provider_card(self, info: RemoteProviderInfo, *, installed: bool, busy: bool) -> QFrame:
        item = QFrame()
        item.setObjectName("PluginCard")
        item.setMinimumWidth(PROVIDER_CARD_MIN_WIDTH)
        item.setFixedHeight(PROVIDER_CARD_HEIGHT)
        item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = vbox(item, (PROVIDER_CARD_PADDING,) * 4, PROVIDER_SECTION_GAP)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)

        logo = QLabel()
        logo.setObjectName("ProviderLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(PROVIDER_LOGO_SIZE, PROVIDER_LOGO_SIZE)
        logo.setToolTip(info.name)
        pixmap = self._remote_logo_pixmap(info) or QPixmap(str(asset_path("icons", "providers", "fallback.png")))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    PROVIDER_LOGO_SIZE,
                    PROVIDER_LOGO_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        header.addWidget(logo, 0, Qt.AlignmentFlag.AlignTop)

        identity_host = QWidget()
        identity = vbox(identity_host, (0, 1, 0, 0), PROVIDER_IDENTITY_GAP)
        identity.addWidget(label(info.name, "PluginCardTitle", False))
        status = status_badge("Installed" if installed else "Online")
        status.setFixedHeight(PROVIDER_STATUS_HEIGHT)
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        identity.addWidget(status, 0, Qt.AlignmentFlag.AlignLeft)
        identity.addStretch(1)
        header.addWidget(identity_host, 1, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        description = _ElidedDescriptionLabel(info.description or f"{info.name} provider package.", max_lines=3)
        layout.addWidget(description)

        layout.addStretch(1)
        action_text = "Installing..." if busy else ("Update" if installed else "Install")
        action = button(action_text, "primary")
        action.setEnabled(not busy)
        action.clicked.connect(lambda _checked=False, remote=info: self._handle_install_remote_clicked(remote))

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(6)
        footer.addWidget(action)
        footer.addStretch(1)
        version = label(f"v{info.version}", "ProviderVersionText", False)
        version.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        footer.addWidget(version, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(footer)
        return item

    def _handle_install_remote_clicked(self, info: RemoteProviderInfo) -> None:
        if info.remote_id in self._remote_busy_ids or self.on_install_remote is None:
            return
        self.on_install_remote(info)

    def _handle_refresh_remote_clicked(self) -> None:
        if self.on_refresh_remote is not None:
            self.on_refresh_remote()

    def set_remote_catalog(
        self,
        items: list[RemoteProviderInfo] | None = None,
        *,
        loading: bool = False,
        error: str | None = None,
        busy_ids: set[int] | None = None,
    ) -> None:
        """Update the Online Provider Catalog section. Called by MainWindow after a background fetch/install."""
        if items is not None:
            self._remote_items = list(items)
        self._remote_loading = loading
        self._remote_error = error
        if busy_ids is not None:
            self._remote_busy_ids = set(busy_ids)
        if loading:
            self.online_status_label.setText("Loading online provider catalog...")
            self.online_status_label.setVisible(True)
        elif error:
            self.online_status_label.setText(error)
            self.online_status_label.setVisible(True)
        elif not self._remote_items:
            self.online_status_label.setText("No providers are published online yet.")
            self.online_status_label.setVisible(True)
        else:
            self.online_status_label.setVisible(False)
        self._rebuild_remote_cards()

    def _rebuild_remote_cards(self) -> None:
        while self.online_grid.count():
            item = self.online_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._remote_cards.clear()
        installed_ids = self.manager.installed_ids()
        for info in self._remote_items:
            installed = info.slug.strip().casefold() in installed_ids
            busy = info.remote_id in self._remote_busy_ids
            self._remote_cards.append(self._remote_provider_card(info, installed=installed, busy=busy))
        self._reflow_remote_cards(force=True)

    def _column_count_for(self, host: QWidget) -> int:
        available_width = host.contentsRect().width()
        if available_width <= 0:
            available_width = max(0, self.width() - 28)
        fitting = (available_width + PROVIDER_GRID_GAP) // (PROVIDER_CARD_MIN_WIDTH + PROVIDER_GRID_GAP)
        return max(PROVIDER_MIN_COLUMNS, min(PROVIDER_MAX_COLUMNS, int(fitting)))

    def _reflow_remote_cards(self, *, force: bool = False) -> None:
        columns = self._column_count_for(self.online_host)
        if not force and columns == self._remote_current_columns:
            return
        self._remote_current_columns = columns
        while self.online_grid.count():
            self.online_grid.takeAt(0)
        for item in self._remote_cards:
            item.setVisible(False)
        for column in range(PROVIDER_MAX_COLUMNS):
            self.online_grid.setColumnMinimumWidth(column, PROVIDER_CARD_MIN_WIDTH if column < columns else 0)
            self.online_grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, item in enumerate(self._remote_cards):
            row, column = divmod(index, columns)
            self.online_grid.addWidget(item, row, column)
            item.setVisible(True)
        self.online_host.setFixedHeight(self._grid_content_height(len(self._remote_cards), columns))

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

    @staticmethod
    def _grid_content_height(item_count: int, columns: int) -> int:
        """Exact pixel height needed for a fixed-height provider-card grid.

        A plain QWidget hosting a QGridLayout does not reliably report an
        up-to-date sizeHint to its parent QVBoxLayout once a stretch factor of
        0 is used (see the Providers page layout). Without an explicit fixed
        height, a second row of cards can render past the widget's allocated
        space and overlap the section drawn immediately below it.
        """
        if item_count <= 0 or columns <= 0:
            return 0
        rows = -(-item_count // columns)  # ceil division
        return rows * PROVIDER_CARD_HEIGHT + max(0, rows - 1) * PROVIDER_GRID_GAP

    def _reflow_cards(self, *, force: bool = False) -> None:
        columns = self._column_count()
        visible_cards = self._filtered_cards()
        if not force and columns == self._current_columns:
            return
        self._current_columns = columns
        while self.grid.count():
            self.grid.takeAt(0)
        # Provider cards can be newly constructed and parentless at this point.
        # Never show them until QGridLayout has re-parented them into self.host;
        # otherwise Windows briefly exposes the card as a top-level "Invio" window.
        for item in self._cards:
            item.setVisible(False)
        for column in range(PROVIDER_MAX_COLUMNS):
            self.grid.setColumnMinimumWidth(column, PROVIDER_CARD_MIN_WIDTH if column < columns else 0)
            self.grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, item in enumerate(visible_cards):
            row, column = divmod(index, columns)
            self.grid.addWidget(item, row, column)
            item.setVisible(True)
        self.host.setFixedHeight(self._grid_content_height(len(visible_cards), columns))

    def _apply_filter(self, _text: str) -> None:
        self._reflow_cards(force=True)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if hasattr(self, "grid"):
            self._reflow_cards()
        if hasattr(self, "online_grid"):
            self._reflow_remote_cards()

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
            self.host.setFixedHeight(PROVIDER_CARD_HEIGHT)
        else:
            self._cards.extend(self._provider_card(provider, provider.id in installed_ids) for provider in providers)
            self._reflow_cards(force=True)
        if hasattr(self, "online_grid"):
            self._rebuild_remote_cards()
