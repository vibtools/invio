from __future__ import annotations

from dataclasses import dataclass


COLORS = {
    "window_background": "#090D14",
    "page_background": "#090D14",
    "surface": "#111722",
    "nested_surface": "#1A212E",
    "border": "#1E2633",
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
    "row_hover": "rgba(255,255,255,8)",
    "selection": "rgba(37,99,235,38)",
}


@dataclass(frozen=True, slots=True)
class UiConstants:
    sidebar_width: int = 220
    sidebar_padding: int = 8
    nav_height: int = 28
    header_height: int = 44
    status_height: int = 24
    page_padding: int = 14
    section_gap: int = 10
    content_gap: int = 12
    card_padding: int = 14
    card_gap: int = 7
    button_height: int = 28
    button_padding_x: int = 9
    input_height: int = 32
    table_header_height: int = 30
    table_row_height: int = 32
    common_radius: int = 8
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
