from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..core.paths import asset_path
from .tokens import CONST


class _FramelessResizeFilter(QObject):
    """Delegate frameless edge drags back to the operating-system resize loop."""

    def __init__(self, window: QWidget, margin: int = 5):
        super().__init__(window)
        self.window = window
        self.margin = margin
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
            window.destroyed.connect(lambda: app.removeEventFilter(self))

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # type: ignore[override]
        if event.type() != QEvent.Type.MouseButtonPress:
            return False
        if not hasattr(event, "button") or event.button() != Qt.MouseButton.LeftButton:
            return False
        if self.window.isMaximized() or self.window.isFullScreen():
            return False
        if not isinstance(watched, QWidget) or watched.window() is not self.window:
            return False
        if isinstance(watched, QPushButton):
            return False
        if not hasattr(event, "globalPosition"):
            return False

        point = self.window.mapFromGlobal(event.globalPosition().toPoint())
        edges = self._edges_at(point)
        if not edges:
            return False
        handle = self.window.windowHandle()
        if handle is None:
            return False
        try:
            return bool(handle.startSystemResize(edges))
        except (AttributeError, RuntimeError):
            return False

    def _edges_at(self, point: QPoint):
        width = self.window.width()
        height = self.window.height()
        if width <= 0 or height <= 0:
            return Qt.Edges()

        edges = Qt.Edges()
        if point.x() <= self.margin:
            edges |= Qt.Edge.LeftEdge
        elif point.x() >= width - self.margin - 1:
            edges |= Qt.Edge.RightEdge
        if point.y() <= self.margin:
            edges |= Qt.Edge.TopEdge
        elif point.y() >= height - self.margin - 1:
            edges |= Qt.Edge.BottomEdge
        return edges


class _ModalOverlayController(QObject):
    """Dim the owning application surface while an app-owned modal is visible."""

    def __init__(self, dialog: QWidget):
        super().__init__(dialog)
        self.dialog = dialog
        self.parent_widget = dialog.parentWidget()
        self.overlay: QWidget | None = None
        if self.parent_widget is not None:
            self.overlay = QWidget(self.parent_widget)
            self.overlay.setObjectName("ModalOverlay")
            self.overlay.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.overlay.hide()
            self.parent_widget.installEventFilter(self)
            dialog.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # type: ignore[override]
        overlay = self.overlay
        if overlay is None:
            return False
        if watched is self.parent_widget and event.type() == QEvent.Type.Resize:
            overlay.setGeometry(self.parent_widget.rect())
        elif watched is self.dialog:
            if event.type() == QEvent.Type.Show:
                overlay.setGeometry(self.parent_widget.rect())
                overlay.show()
                overlay.raise_()
            elif event.type() in (QEvent.Type.Hide, QEvent.Type.Close):
                overlay.hide()
            elif event.type() == QEvent.Type.Destroy:
                overlay.hide()
                overlay.deleteLater()
        return False


class TitleBar(QFrame):
    """Shared frameless-window title-bar movement behavior."""

    def __init__(self, window: QWidget, *, object_name: str, height: int):
        super().__init__(window)
        self._window = window
        self._fallback_drag_offset: QPoint | None = None
        self.setObjectName(object_name)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self._window.windowHandle()
            if handle is not None:
                try:
                    if handle.startSystemMove():
                        event.accept()
                        return
                except (AttributeError, RuntimeError):
                    pass
            self._fallback_drag_offset = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._fallback_drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._fallback_drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._fallback_drag_offset = None
        super().mouseReleaseEvent(event)

    @staticmethod
    def _icon_label(window: QWidget, size: int = 16) -> QLabel:
        icon_label = QLabel()
        icon_label.setObjectName("TitleBarIcon")
        icon_label.setFixedSize(size, size)
        icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        icon = window.windowIcon()
        if icon.isNull():
            app = QApplication.instance()
            if app is not None:
                icon = app.windowIcon()
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(size, size))
        return icon_label

    @staticmethod
    def _control(icon_name: str, object_name: str, tooltip: str, *, width: int, height: int) -> QPushButton:
        control = QPushButton("")
        control.setObjectName(object_name)
        icon_path = asset_path("icons", "window", icon_name)
        if icon_path.is_file():
            control.setIcon(QIcon(str(icon_path)))
        control.setToolTip(tooltip)
        control.setCursor(Qt.CursorShape.PointingHandCursor)
        control.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        control.setFixedSize(width, height)
        return control


class MainTitleBar(TitleBar):
    """Single compact Invio application header and frameless window chrome."""

    def __init__(self, window: QWidget, title: str, context: str):
        super().__init__(window, object_name="MainTitleBar", height=CONST.main_titlebar_height)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, CONST.space_compact, 0)
        layout.setSpacing(CONST.space_compact)
        layout.addWidget(self._icon_label(window, 16))

        title_label = QLabel(title)
        title_label.setObjectName("MainTitleText")
        title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(title_label)

        context_divider = QFrame()
        context_divider.setObjectName("TitleBarContextDivider")
        context_divider.setFixedSize(1, 14)
        layout.addWidget(context_divider)

        self.context_label = QLabel(context)
        self.context_label.setObjectName("MainTitleContext")
        self.context_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.context_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.context_label, 1)

        brand = QLabel("Vib Tools")
        brand.setObjectName("MainTitleBrand")
        brand.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(brand)

        self.minimize_button = self._control(
            "minimize.svg", "MainTitleMinimize", "Minimize", width=36, height=CONST.main_titlebar_height
        )
        self.maximize_button = self._control(
            "maximize.svg", "MainTitleMaximize", "Maximize", width=36, height=CONST.main_titlebar_height
        )
        self.close_button = self._control(
            "close.svg", "MainTitleClose", "Close", width=40, height=CONST.main_titlebar_height
        )
        self.minimize_button.clicked.connect(window.showMinimized)
        self.maximize_button.clicked.connect(self._toggle_maximized)
        self.close_button.clicked.connect(window.close)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)
        window.installEventFilter(self)

    def set_context(self, text: str) -> None:
        self.context_label.setText(text)

    def _toggle_maximized(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()
        self._sync_maximize_state()

    def _sync_maximize_state(self) -> None:
        maximized = self._window.isMaximized()
        icon_name = "restore.svg" if maximized else "maximize.svg"
        icon_path = asset_path("icons", "window", icon_name)
        if icon_path.is_file():
            self.maximize_button.setIcon(QIcon(str(icon_path)))
        self.maximize_button.setToolTip("Restore" if maximized else "Maximize")

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # type: ignore[override]
        if watched is self._window and event.type() == QEvent.Type.WindowStateChange:
            self._sync_maximize_state()
        return False

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximized()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class DialogTitleBar(TitleBar):
    """Compact dialog chrome: app icon, dialog title, close only."""

    def __init__(self, dialog: QWidget):
        super().__init__(dialog, object_name="DialogTitleBar", height=CONST.dialog_titlebar_height)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, CONST.space_compact, 0)
        layout.setSpacing(CONST.space_compact)
        layout.addWidget(self._icon_label(dialog, 15))

        self.title_label = QLabel(dialog.windowTitle())
        self.title_label.setObjectName("DialogTitleText")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.title_label, 1)

        close_button = self._control(
            "close.svg", "DialogTitleClose", "Close", width=34, height=CONST.dialog_titlebar_height
        )
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        dialog.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # type: ignore[override]
        if watched is self._window and event.type() == QEvent.Type.WindowTitleChange:
            self.title_label.setText(self._window.windowTitle())
        return False


def enable_frameless_window(window: QWidget) -> _FramelessResizeFilter:
    """Remove native chrome while preserving operating-system move/resize loops."""
    window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    controller = _FramelessResizeFilter(window)
    window.setProperty("customChrome", True)
    return controller


def _dialog_shadow(surface: QWidget) -> QGraphicsDropShadowEffect:
    """Apply a restrained separation shadow to an app-owned dialog surface."""
    shadow = QGraphicsDropShadowEffect(surface)
    shadow.setBlurRadius(12.0)
    shadow.setOffset(0.0, 2.0)
    shadow.setColor(QColor(0, 0, 0, 96))
    surface.setGraphicsEffect(shadow)
    return shadow


def build_dialog_shell(dialog: QWidget) -> QVBoxLayout:
    """Create the standard Vib dialog structure: shadowed surface, title bar and padded body."""
    resize_filter = enable_frameless_window(dialog)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    outer = QVBoxLayout(dialog)
    outer.setContentsMargins(
        CONST.space_compact, CONST.space_compact, CONST.space_compact, CONST.space_compact
    )
    outer.setSpacing(0)

    surface = QFrame(dialog)
    surface.setObjectName("DialogSurface")
    surface_layout = QVBoxLayout(surface)
    surface_layout.setContentsMargins(0, 0, 0, 0)
    surface_layout.setSpacing(0)
    shadow = _dialog_shadow(surface)

    title_bar = DialogTitleBar(dialog)
    surface_layout.addWidget(title_bar)

    body = QWidget(surface)
    body.setObjectName("DialogBody")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(
        CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding, CONST.dialog_padding
    )
    body_layout.setSpacing(CONST.dialog_gap)
    surface_layout.addWidget(body, 1)
    outer.addWidget(surface, 1)

    dialog._invio_dialog_surface = surface  # type: ignore[attr-defined]
    dialog._invio_dialog_shadow = shadow  # type: ignore[attr-defined]
    dialog._invio_title_bar = title_bar  # type: ignore[attr-defined]
    dialog._invio_resize_filter = resize_filter  # type: ignore[attr-defined]
    dialog._invio_modal_overlay = _ModalOverlayController(dialog)  # type: ignore[attr-defined]
    return body_layout


def install_dialog_chrome(dialog: QWidget, *, preserve_client_height: bool = True) -> DialogTitleBar:
    """Overlay custom chrome on a complex Qt-owned dialog layout.

    Window-flag changes can cause Qt-owned dialogs such as ``QMessageBox`` to
    rebuild their internal layout.  Never accept a caller-captured layout
    wrapper here: apply the window mutations first, then reacquire the live
    layout from the dialog before reading or changing its margins.
    """
    resize_filter = enable_frameless_window(dialog)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    layout = dialog.layout()
    if layout is None:
        raise RuntimeError("Custom dialog chrome requires a live dialog layout.")
    shadow_margin = CONST.space_compact
    margins = layout.contentsMargins()
    layout.setContentsMargins(
        margins.left() + shadow_margin,
        margins.top() + CONST.dialog_titlebar_height + shadow_margin,
        margins.right() + shadow_margin,
        margins.bottom() + shadow_margin,
    )
    if preserve_client_height and dialog.height() > 0:
        dialog.resize(
            dialog.width() + (shadow_margin * 2),
            dialog.height() + CONST.dialog_titlebar_height + (shadow_margin * 2),
        )

    surface = QFrame(dialog)
    surface.setObjectName("DialogSurface")
    shadow = _dialog_shadow(surface)
    title_bar = DialogTitleBar(dialog)

    class _OverlayGeometry(QObject):
        def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # type: ignore[override]
            if watched is dialog and event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
                width = max(0, dialog.width() - (shadow_margin * 2))
                height = max(0, dialog.height() - (shadow_margin * 2))
                surface.setGeometry(shadow_margin, shadow_margin, width, height)
                surface.lower()
                title_bar.setGeometry(
                    shadow_margin, shadow_margin, width, CONST.dialog_titlebar_height
                )
                title_bar.raise_()
            return False

    geometry_controller = _OverlayGeometry(dialog)
    dialog.installEventFilter(geometry_controller)
    width = max(0, dialog.width() - (shadow_margin * 2))
    height = max(0, dialog.height() - (shadow_margin * 2))
    surface.setGeometry(shadow_margin, shadow_margin, width, height)
    surface.show()
    surface.lower()
    title_bar.setGeometry(shadow_margin, shadow_margin, width, CONST.dialog_titlebar_height)
    title_bar.show()
    title_bar.raise_()
    dialog._invio_dialog_surface = surface  # type: ignore[attr-defined]
    dialog._invio_dialog_shadow = shadow  # type: ignore[attr-defined]
    dialog._invio_title_bar = title_bar  # type: ignore[attr-defined]
    dialog._invio_resize_filter = resize_filter  # type: ignore[attr-defined]
    dialog._invio_title_geometry = geometry_controller  # type: ignore[attr-defined]
    dialog._invio_modal_overlay = _ModalOverlayController(dialog)  # type: ignore[attr-defined]
    return title_bar
