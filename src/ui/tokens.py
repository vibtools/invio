from __future__ import annotations

from dataclasses import dataclass


COLORS = {
    "window_background": "#090D14",
    "page_background": "#090D14",
    "surface": "#111722",
    "elevated_surface": "#151C27",
    "nested_surface": "#1A212E",
    "border": "#1E2633",
    "border_subtle": "#18202C",
    "input_border": "#2D3748",
    "primary": "#2563EB",
    "primary_hover": "#3B82F6",
    "primary_pressed": "#1D4ED8",
    "focus": "#38BDF8",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#B91C1C",
    "danger_hover": "#991B1B",
    "primary_text": "#F8FAFC",
    "title_text": "#F1F5F9",
    "secondary_text": "#CBD5E1",
    "muted_text": "#94A3B8",
    "disabled_text": "#64748B",
    "button_border": "#283345",
    "input_background": "#161D2A",
    "table_header": "#111620",
    "nav_selected": "rgba(37,99,235,31)",
    "hover": "rgba(255,255,255,13)",
    "row_hover": "rgba(255,255,255,6)",
    "row_alternate": "rgba(255,255,255,2)",
    "data_divider": "#263244",
    "selection": "rgba(37,99,235,38)",
    # v1.42.0 scoped form/settings typography tokens.
    "text_title": "#E6EDF3",
    "text_body": "#C9D1D9",
    "text_muted": "#8B949E",
    "text_placeholder": "#48515E",
    "danger_text": "#FCA5A5",
}


@dataclass(frozen=True, slots=True)
class UiConstants:
    sidebar_width: int = 220
    sidebar_padding: int = 8
    nav_height: int = 28
    main_titlebar_height: int = 32
    dialog_titlebar_height: int = 30
    header_height: int = 44
    status_height: int = 24
    page_padding: int = 14
    space_tight: int = 4
    space_compact: int = 6
    space_standard: int = 8
    section_gap: int = 10
    content_gap: int = 12
    card_padding: int = 14
    card_gap: int = 7
    button_height: int = 28
    button_padding_x: int = 9
    input_height: int = 32
    table_header_height: int = 28
    table_row_height: int = 30
    data_grid_control_height: int = 28
    data_grid_gap: int = 6
    data_grid_padding: int = 8
    data_grid_search_width: int = 220
    data_grid_default_page_size: int = 10
    data_grid_accounts_max_height: int = 250
    common_radius: int = 8
    form_control_height: int = 32
    form_radius: int = 6
    dialog_padding: int = 12
    dialog_gap: int = 8
    min_window_width: int = 1120
    min_window_height: int = 720
    default_window_width: int = 1366
    default_window_height: int = 768
    compact_breakpoint: int = 1180
    medium_breakpoint: int = 1440


CONST = UiConstants()

NAV_ITEMS = (
    ("Dashboard", "dashboard"),
    ("Accounts", "accounts"),
    ("Invoice Templates", "invoice"),
    ("Customer Lists", "customers"),
    ("Tasks", "tasks"),
    ("Providers", "providers"),
    ("Reports", "reports"),
    ("Live Logs", "logs"),
    ("Settings", "settings"),
)


NAV_GROUPS = (
    ("MAIN", (
        ("Dashboard", "dashboard"),
        ("Accounts", "accounts"),
        ("Invoice Templates", "invoice"),
        ("Customer Lists", "customers"),
        ("Tasks", "tasks"),
    )),
    ("OPERATIONS", (
        ("Providers", "providers"),
        ("Reports", "reports"),
        ("Live Logs", "logs"),
    )),
    ("SETTINGS", (
        ("Settings", "settings"),
    )),
)
