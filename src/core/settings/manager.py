from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

SETTINGS_SCHEMA_VERSION = 1
START_PAGE_LAST = "__last_page__"
START_PAGES = (
    "Accounts",
    "Invoice Templates",
    "Customer Lists",
    "Tasks",
    "Providers",
    "Reports",
    "Live Logs",
    "Settings",
)


class SettingsError(RuntimeError):
    """Raised when user-facing application settings cannot be validated or saved."""


@dataclass(slots=True)
class AppSettings:
    """User-configurable Invio behavior.

    Defaults intentionally preserve the behavior of the frozen v1.0.0.1
    baseline until the user changes a setting.
    """

    start_page: str = "Accounts"
    remember_window: bool = False

    confirm_exit_active_tasks: bool = True
    confirm_close_task: bool = True
    confirm_delete_template: bool = True
    confirm_delete_customer_list: bool = True
    confirm_clear_logs: bool = False

    show_log_timestamps: bool = True
    auto_scroll_logs: bool = True
    max_log_entries: int = 0

    default_file_folder: str = ""
    remember_last_folder: bool = False


@dataclass(slots=True)
class WindowState:
    x: int
    y: int
    width: int
    height: int


@dataclass(slots=True)
class _RuntimeState:
    last_page: str = "Accounts"
    last_folder: str = ""
    window: WindowState | None = None


def default_settings_path() -> Path:
    """Return the per-user settings path without introducing a new dependency."""

    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return base / "Vib Tools" / "Invio" / "settings.json"


class SettingsManager:
    """Load, validate, and atomically persist non-sensitive Invio settings."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else default_settings_path()
        self._settings = AppSettings()
        self._runtime = _RuntimeState()
        self.load_warning = ""
        self._load()

    @staticmethod
    def defaults() -> AppSettings:
        return AppSettings()

    @property
    def settings(self) -> AppSettings:
        return replace(self._settings)

    def update(self, settings: AppSettings) -> AppSettings:
        normalized = self._validate_user_settings(settings, strict=True)
        previous_settings = replace(self._settings)
        previous_runtime = _RuntimeState(
            last_page=self._runtime.last_page,
            last_folder=self._runtime.last_folder,
            window=replace(self._runtime.window) if self._runtime.window is not None else None,
        )
        self._settings = normalized
        if not normalized.remember_window:
            self._runtime.window = None
        if not normalized.remember_last_folder:
            self._runtime.last_folder = ""
        try:
            self._save()
        except SettingsError:
            self._settings = previous_settings
            self._runtime = previous_runtime
            raise
        return self.settings

    def startup_page(self) -> str:
        if self._settings.start_page == START_PAGE_LAST:
            if self._runtime.last_page in START_PAGES:
                return self._runtime.last_page
            return "Accounts"
        return self._settings.start_page if self._settings.start_page in START_PAGES else "Accounts"

    def record_last_page(self, page_name: str) -> None:
        if self._settings.start_page != START_PAGE_LAST or page_name not in START_PAGES:
            return
        if self._runtime.last_page == page_name:
            return
        self._runtime.last_page = page_name
        self._save_runtime_best_effort()

    def dialog_directory(self) -> str:
        candidates: list[str] = []
        if self._settings.remember_last_folder:
            candidates.append(self._runtime.last_folder)
        candidates.append(self._settings.default_file_folder)
        for candidate in candidates:
            if candidate:
                path = Path(candidate).expanduser()
                if path.is_dir():
                    return str(path)
        return ""

    def record_last_folder(self, selected_path: str | Path) -> None:
        if not self._settings.remember_last_folder:
            return
        path = Path(selected_path).expanduser()
        folder = path if path.is_dir() else path.parent
        if not folder.is_dir():
            return
        normalized = str(folder.resolve())
        if normalized == self._runtime.last_folder:
            return
        self._runtime.last_folder = normalized
        self._save_runtime_best_effort()

    def window_state(self) -> WindowState | None:
        if not self._settings.remember_window or self._runtime.window is None:
            return None
        return replace(self._runtime.window)

    def record_window_state(self, state: WindowState) -> None:
        if not self._settings.remember_window:
            return
        if state.width <= 0 or state.height <= 0:
            return
        self._runtime.window = replace(state)
        self._save_runtime_best_effort()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Settings root must be an object.")
            settings_raw = raw.get("settings", {})
            runtime_raw = raw.get("runtime", {})
            if not isinstance(settings_raw, dict) or not isinstance(runtime_raw, dict):
                raise ValueError("Settings sections must be objects.")
            self._settings = self._settings_from_mapping(settings_raw)
            self._runtime = self._runtime_from_mapping(runtime_raw)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self._settings = AppSettings()
            self._runtime = _RuntimeState()
            self.load_warning = f"Application settings could not be loaded; defaults are being used. ({exc})"

    def _settings_from_mapping(self, raw: dict[str, Any]) -> AppSettings:
        defaults = AppSettings()
        values: dict[str, Any] = {}
        for key in asdict(defaults):
            if key in raw:
                values[key] = raw[key]
        candidate = replace(defaults, **values)
        return self._validate_user_settings(candidate, strict=False)

    def _runtime_from_mapping(self, raw: dict[str, Any]) -> _RuntimeState:
        last_page = raw.get("last_page", "Accounts")
        if last_page not in START_PAGES:
            last_page = "Accounts"

        last_folder = raw.get("last_folder", "")
        if not isinstance(last_folder, str):
            last_folder = ""

        window_state: WindowState | None = None
        window = raw.get("window")
        if isinstance(window, dict):
            try:
                candidate = WindowState(
                    x=int(window["x"]),
                    y=int(window["y"]),
                    width=int(window["width"]),
                    height=int(window["height"]),
                )
                if candidate.width > 0 and candidate.height > 0:
                    window_state = candidate
            except (KeyError, TypeError, ValueError):
                window_state = None
        return _RuntimeState(last_page=last_page, last_folder=last_folder, window=window_state)

    def _validate_user_settings(self, settings: AppSettings, *, strict: bool) -> AppSettings:
        defaults = AppSettings()

        start_page = settings.start_page
        if start_page not in (*START_PAGES, START_PAGE_LAST):
            if strict:
                raise SettingsError("Choose a valid start page.")
            start_page = defaults.start_page

        boolean_fields = (
            "remember_window",
            "confirm_exit_active_tasks",
            "confirm_close_task",
            "confirm_delete_template",
            "confirm_delete_customer_list",
            "confirm_clear_logs",
            "show_log_timestamps",
            "auto_scroll_logs",
            "remember_last_folder",
        )
        normalized_bools: dict[str, bool] = {}
        for field_name in boolean_fields:
            value = getattr(settings, field_name)
            if type(value) is not bool:
                if strict:
                    raise SettingsError(f"Invalid value for {field_name.replace('_', ' ')}.")
                value = getattr(defaults, field_name)
            normalized_bools[field_name] = value

        try:
            max_log_entries = int(settings.max_log_entries)
        except (TypeError, ValueError) as exc:
            if strict:
                raise SettingsError("Maximum log lines must be a whole number.") from exc
            max_log_entries = defaults.max_log_entries
        if max_log_entries < 0 or max_log_entries > 100000:
            if strict:
                raise SettingsError("Maximum log lines must be between 0 and 100,000. Use 0 for unlimited.")
            max_log_entries = defaults.max_log_entries

        folder_value = settings.default_file_folder
        if not isinstance(folder_value, str):
            if strict:
                raise SettingsError("Default file folder must be a folder path.")
            folder_value = ""
        folder_value = folder_value.strip()
        if folder_value:
            folder = Path(folder_value).expanduser()
            if strict and not folder.is_dir():
                raise SettingsError("The default file folder does not exist. Choose an existing folder or leave it blank.")
            if folder.is_dir():
                folder_value = str(folder.resolve())
            elif not strict:
                folder_value = ""

        return AppSettings(
            start_page=start_page,
            max_log_entries=max_log_entries,
            default_file_folder=folder_value,
            **normalized_bools,
        )

    def _payload(self) -> dict[str, Any]:
        window = asdict(self._runtime.window) if self._runtime.window is not None else None
        return {
            "schema_version": SETTINGS_SCHEMA_VERSION,
            "settings": asdict(self._settings),
            "runtime": {
                "last_page": self._runtime.last_page,
                "last_folder": self._runtime.last_folder,
                "window": window,
            },
        }

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_name(f"{self.path.name}.tmp")
            text = json.dumps(self._payload(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            with temp.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, self.path)
        except OSError as exc:
            raise SettingsError(f"Settings could not be saved to {self.path}: {exc}") from exc

    def _save_runtime_best_effort(self) -> None:
        try:
            self._save()
        except SettingsError:
            # Runtime convenience state must never interrupt normal app work.
            return
