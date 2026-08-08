from __future__ import annotations

import unittest
from pathlib import Path

from src.ui.tokens import COLORS, CONST, NAV_ITEMS


class UiContractTests(unittest.TestCase):
    def test_step40j_core_tokens_are_frozen(self):
        self.assertEqual(COLORS["window_background"], "#090D14")
        self.assertEqual(COLORS["surface"], "#111722")
        self.assertEqual(COLORS["nested_surface"], "#1A212E")
        self.assertEqual(COLORS["border"], "#1E2633")
        self.assertEqual(COLORS["primary"], "#2563EB")
        self.assertEqual(COLORS["focus"], "#38BDF8")
        self.assertEqual(COLORS["primary_text"], "#F8FAFC")
        self.assertEqual(COLORS["secondary_text"], "#CBD5E1")
        self.assertEqual(CONST.sidebar_width, 220)
        self.assertEqual(CONST.header_height, 44)
        self.assertEqual(CONST.page_padding, 14)
        self.assertEqual(CONST.button_height, 28)
        self.assertEqual(CONST.input_height, 32)
        self.assertEqual(CONST.table_header_height, 30)
        self.assertEqual(CONST.table_row_height, 32)
        self.assertEqual((CONST.min_window_width, CONST.min_window_height), (1120, 720))
        self.assertEqual((CONST.default_window_width, CONST.default_window_height), (1366, 768))

    def test_requested_page_inventory_is_exact(self):
        self.assertEqual(
            [name for name, _key in NAV_ITEMS],
            [
                "Accounts",
                "Invoice Templates",
                "Customer Lists",
                "Tasks",
                "Providers",
                "Reports",
                "Live Logs",
                "Settings",
            ],
        )


    def test_sidebar_uses_official_dark_scroll_surface_contract(self):
        root = Path(__file__).resolve().parents[1]
        window_source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        style_source = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertIn('nav_host.setObjectName("SidebarNavHost")', window_source)
        self.assertIn('scroll.setObjectName("MinimalScrollArea")', window_source)
        self.assertIn('QWidget#Sidebar QScrollArea#MinimalScrollArea::viewport', style_source)
        self.assertIn('QWidget#Sidebar QWidget#SidebarNavHost', style_source)
        self.assertIn("background: {c['window_background']};", style_source)

    def test_provider_cards_use_official_plugin_visual_contract(self):
        root = Path(__file__).resolve().parents[1]
        page_source = (root / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        style_source = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertIn('item.setObjectName("PluginCard")', page_source)
        self.assertIn('"PluginCategoryChip"', page_source)
        self.assertIn('"PluginCardTitle"', page_source)
        self.assertIn('"PluginCardDescription"', page_source)
        self.assertIn('self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)', page_source)
        self.assertIn('QFrame#PluginCard', style_source)
        self.assertIn('QLabel#PluginCategoryChip', style_source)
        self.assertIn('background: #1E293B;', style_source)

    def test_current_runtime_surfaces_have_no_ui_only_release_markers(self):
        root = Path(__file__).resolve().parents[1]
        paths = list((root / "src").rglob("*.py")) + list((root / "providers").rglob("*.json"))
        corpus = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
        for marker in (
            "ui milestone",
            "ui-first",
            "backend milestone",
            "backend pending",
            "frontend-only",
            "demo-stage",
            "demo",
            "fake",
            "-ui\"",
        ):
            self.assertNotIn(marker, corpus)

    def test_settings_page_exposes_only_approved_basic_controls(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "pages" / "settings_page.py").read_text(encoding="utf-8")
        for control in (
            "start_page",
            "remember_window",
            "confirm_exit_active_tasks",
            "confirm_close_task",
            "confirm_delete_template",
            "confirm_delete_customer_list",
            "confirm_clear_logs",
            "show_log_timestamps",
            "auto_scroll_logs",
            "max_log_entries",
            "default_file_folder",
            "remember_last_folder",
        ):
            self.assertIn(f"self.{control}", source)
        self.assertIn('button("Save Changes", "primary")', source)
        self.assertIn('button("Restore Defaults")', source)

    def test_settings_are_wired_to_existing_runtime_actions(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        for hook in (
            "confirm_exit_active_tasks",
            "confirm_close_task",
            "confirm_delete_template",
            "confirm_delete_customer_list",
            "confirm_clear_logs",
            "show_log_timestamps",
            "auto_scroll_logs",
            "max_log_entries",
            "dialog_directory",
            "record_window_state",
        ):
            self.assertIn(hook, source)


    def test_provider_cards_expose_real_uninstall_action(self):
        root = Path(__file__).resolve().parents[1]
        page_source = (root / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        window_source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        manager_source = (root / "src" / "core" / "provider_manager" / "manager.py").read_text(encoding="utf-8")
        self.assertIn('button("Uninstall", "danger")', page_source)
        self.assertIn("self.on_uninstall(pid)", page_source)
        self.assertIn("def uninstall_provider(self, provider_id: str)", window_source)
        self.assertIn("removed = self.providers.uninstall(provider_id)", window_source)
        self.assertIn("def uninstall(self, provider_id: str)", manager_source)
        self.assertIn("target.unlink()", manager_source)

    def test_application_owned_modals_use_compact_geometry(self):
        root = Path(__file__).resolve().parents[1]
        dialog_source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        window_source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(dialog_source.count("_apply_compact_dialog_geometry("), 5)
        self.assertIn("def compact_message_box(", dialog_source)
        self.assertIn("compact_message_box(self, title, text, icon=icon)", window_source)
        self.assertNotIn("QMessageBox.question(", window_source)

    def test_add_account_dialog_uses_compact_two_column_provider_fields(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn("width_ratio=0.64", source)
        self.assertIn("QGridLayout(self.credentials_host)", source)
        self.assertIn("column_count = 2 if len(provider.credential_fields) > 2 else 1", source)
        self.assertIn("row, column = divmod(index, column_count)", source)

    def test_worker_manager_declares_task_scoped_qthreads(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        self.assertIn("self._slots: dict[str, _WorkerSlot]", source)
        self.assertIn("thread = QThread(self)", source)
        self.assertIn('thread.setObjectName(f"InvioTaskThread-{task.id}")', source)
        self.assertNotIn("self.thread: QThread", source)


if __name__ == "__main__":
    unittest.main()
