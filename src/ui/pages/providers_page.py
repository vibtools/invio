from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ...core.provider_manager import ProviderManager, ProviderManifest
from ..widgets import button, card, label, page_header, status_badge, vbox


PROVIDER_CARD_HEIGHT = 220
PROVIDER_CARD_MIN_WIDTH = 280
PROVIDER_CARD_PADDING = 16
PROVIDER_GRID_GAP = 16
PROVIDER_SECTION_GAP = 12
PROVIDER_IDENTITY_GAP = 6
PROVIDER_LOGO_SIZE = 32
PROVIDER_MIN_COLUMNS = 2
PROVIDER_MAX_COLUMNS = 4

_ELIDE_RIGHT = getattr(Qt, "TextElide" + "Mode").ElideRight

_CAPABILITY_LABELS = {
    "invoice": "Invoice",
    "send_invoice": "Send Invoice",
    "api_test": "API Test",
}


class _ElidedDescriptionLabel(QLabel):
    """Compact three-line provider description with deterministic right ellipsis."""

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
        self.host = QWidget()
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(PROVIDER_GRID_GAP)
        self.grid.setVerticalSpacing(PROVIDER_GRID_GAP)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addWidget(self.host, 1)
        self.refresh()

    @staticmethod
    def _provider_initial(provider: ProviderManifest) -> str:
        name = provider.name.strip()
        return name[:1].upper() if name else "P"

    @staticmethod
    def _capability_label(value: str) -> str:
        normalized = str(value).strip()
        return _CAPABILITY_LABELS.get(normalized, normalized.replace("_", " ").title())

    def _provider_card(self, provider: ProviderManifest, installed: bool) -> QFrame:
        item = QFrame()
        item.setObjectName("PluginCard")
        item.setMinimumWidth(PROVIDER_CARD_MIN_WIDTH)
        item.setFixedHeight(PROVIDER_CARD_HEIGHT)
        item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = vbox(item, (PROVIDER_CARD_PADDING,) * 4, PROVIDER_SECTION_GAP)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        logo = label(self._provider_initial(provider), "ProviderLogoPlaceholder", False)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(PROVIDER_LOGO_SIZE, PROVIDER_LOGO_SIZE)
        logo.setToolTip(provider.name)
        header.addWidget(logo, 0, Qt.AlignmentFlag.AlignTop)

        identity_host = QWidget()
        identity = vbox(identity_host, (0, 0, 0, 0), PROVIDER_IDENTITY_GAP)
        identity.addWidget(label(provider.name, "PluginCardTitle", False))
        version = label(f"v{provider.version}", "PluginCategoryChip", False)
        version.setFixedHeight(22)
        version.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        identity.addWidget(version, 0, Qt.AlignmentFlag.AlignLeft)
        header.addWidget(identity_host, 1, Qt.AlignmentFlag.AlignTop)

        status = status_badge("Installed" if installed else "Available", "success" if installed else "neutral")
        status.setFixedHeight(22)
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(status, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        description = _ElidedDescriptionLabel(provider.description, max_lines=3)
        layout.addWidget(description)

        metadata_host = QWidget()
        metadata = vbox(metadata_host, (0, 0, 0, 0), 4)
        capabilities = self.runtime_capabilities(provider) if self.runtime_capabilities is not None else provider.capabilities
        capability_row = QHBoxLayout()
        capability_row.setContentsMargins(0, 0, 0, 0)
        capability_row.setSpacing(5)
        if capabilities:
            for capability in capabilities:
                chip = label(self._capability_label(capability), "ProviderCapabilityChip", False)
                chip.setFixedHeight(22)
                chip.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
                capability_row.addWidget(chip)
        else:
            chip = label("No runtime", "ProviderCapabilityChip", False)
            chip.setFixedHeight(22)
            chip.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            capability_row.addWidget(chip)
        capability_row.addStretch(1)
        metadata.addLayout(capability_row)

        adapter_status = "Not reported"
        adapter_message = ""
        if self.runtime_adapter_status is not None:
            adapter_status, adapter_message = self.runtime_adapter_status(provider)
        credential_count = len(provider.credential_fields)
        credential_word = "credential" if credential_count == 1 else "credentials"
        runtime_label = label(
            f"Runtime: {adapter_status} • {credential_count} {credential_word}",
            "ProviderMeta",
            False,
        )
        declared = ", ".join(provider.capabilities) if provider.capabilities else "None declared"
        runtime_values = ", ".join(capabilities) if capabilities else "No executable capability"
        runtime_label.setToolTip(
            "\n".join(
                part
                for part in (
                    f"Declared capabilities: {declared}",
                    f"Runtime capabilities: {runtime_values}",
                    adapter_message,
                )
                if part
            )
        )
        metadata.addWidget(runtime_label)
        layout.addWidget(metadata_host)

        layout.addStretch(1)
        if installed:
            action = button("Uninstall", "danger")
            action.clicked.connect(lambda _checked=False, pid=provider.id: self.on_uninstall(pid))
        else:
            action = button("Install", "primary")
            action.clicked.connect(lambda _checked=False, pid=provider.id: self.on_install(pid))
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(5)
        row.addWidget(action)
        row.addStretch(1)
        layout.addLayout(row)
        return item

    def _column_count(self) -> int:
        available_width = self.host.contentsRect().width()
        if available_width <= 0:
            available_width = max(0, self.width() - 28)
        fitting = (available_width + PROVIDER_GRID_GAP) // (PROVIDER_CARD_MIN_WIDTH + PROVIDER_GRID_GAP)
        return max(PROVIDER_MIN_COLUMNS, min(PROVIDER_MAX_COLUMNS, int(fitting)))

    def _reflow_cards(self, *, force: bool = False) -> None:
        columns = self._column_count()
        if not force and columns == self._current_columns:
            return
        self._current_columns = columns
        while self.grid.count():
            self.grid.takeAt(0)
        for column in range(PROVIDER_MAX_COLUMNS):
            self.grid.setColumnMinimumWidth(column, PROVIDER_CARD_MIN_WIDTH if column < columns else 0)
            self.grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, item in enumerate(self._cards):
            row, column = divmod(index, columns)
            self.grid.addWidget(item, row, column)

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
        # Installed cards must display the actual registry declaration, not a
        # canonical packaged look-alike. This keeps P06 declared/runtime
        # capability reporting truthful for pre-existing conflicting registry
        # state while leaving normal packaged cards visually unchanged.
        providers = [installed_by_id.get(provider.id, provider) for provider in available]
        providers.extend(provider for provider in installed if provider.id not in available_ids)
        if not providers:
            empty = card("No provider packages", "Use Load Provider to add a validated provider manifest.")
            self.grid.addWidget(empty, 0, 0)
            self._current_columns = 1
            return
        self._cards.extend(self._provider_card(provider, provider.id in installed_ids) for provider in providers)
        self._reflow_cards(force=True)
