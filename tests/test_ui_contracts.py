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
        self.assertEqual(COLORS["text_title"], "#E6EDF3")
        self.assertEqual(COLORS["text_body"], "#C9D1D9")
        self.assertEqual(COLORS["text_muted"], "#8B949E")
        self.assertEqual(COLORS["text_placeholder"], "#48515E")
        self.assertEqual(CONST.sidebar_width, 220)
        self.assertEqual(CONST.header_height, 44)
        self.assertEqual(CONST.page_padding, 14)
        self.assertEqual(CONST.button_height, 28)
        self.assertEqual(CONST.input_height, 32)
        self.assertEqual(CONST.form_control_height, 32)
        self.assertEqual(CONST.form_radius, 6)
        self.assertEqual(CONST.dialog_padding, 12)
        self.assertEqual(CONST.dialog_gap, 8)
        self.assertEqual(CONST.table_header_height, 28)
        self.assertEqual(CONST.table_row_height, 30)
        self.assertEqual((CONST.min_window_width, CONST.min_window_height), (1120, 720))
        self.assertEqual((CONST.default_window_width, CONST.default_window_height), (1366, 768))

    def test_requested_page_inventory_is_exact(self):
        self.assertEqual(
            [name for name, _key in NAV_ITEMS],
            [
                "Dashboard",
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


    def test_dark_popup_list_and_table_surfaces_are_explicitly_styled(self):
        root = Path(__file__).resolve().parents[1]
        style_source = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        app_source = (root / "src" / "app.py").read_text(encoding="utf-8")
        self.assertIn("QListWidget {", style_source)
        self.assertIn("QMenu {", style_source)
        self.assertIn("QMenu::item:selected", style_source)
        self.assertIn("selection-color: {c['primary_text']}", style_source)
        self.assertIn("app.setStyleSheet(app_qss())", app_source)


    def test_v143_compact_data_grid_contract_is_scope_locked(self):
        root = Path(__file__).resolve().parents[1]
        widgets = (root / "src" / "ui" / "widgets.py").read_text(encoding="utf-8")
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        accounts = (root / "src" / "ui" / "pages" / "accounts_page.py").read_text(encoding="utf-8")
        customers = (root / "src" / "ui" / "pages" / "customer_lists_page.py").read_text(encoding="utf-8")
        templates = (root / "src" / "ui" / "pages" / "invoice_templates_page.py").read_text(encoding="utf-8")
        reports = (root / "src" / "ui" / "pages" / "reports_page.py").read_text(encoding="utf-8")
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")

        self.assertEqual(CONST.data_grid_control_height, 28)
        self.assertEqual(CONST.data_grid_gap, 6)
        self.assertEqual(CONST.data_grid_search_width, 220)
        self.assertEqual(CONST.data_grid_default_page_size, 10)
        self.assertEqual(CONST.data_grid_accounts_max_height, 250)
        self.assertIn("class DataGridToolbar(QWidget):", widgets)
        self.assertIn("class DataGridPager(QWidget):", widgets)
        self.assertIn('self.summary.setText(f"Showing {start + 1}–{end} of {self.total}")', widgets)
        self.assertIn('(10, 25, 50)', widgets)
        self.assertIn('asset_path("icons", "search.svg")', widgets)
        self.assertTrue((root / "assets" / "icons" / "search.svg").is_file())
        self.assertIn('"search.svg"', pyproject)
        self.assertIn('QLineEdit#DataGridSearchInput', styles)
        self.assertIn('QPushButton#DataGridPageButton', styles)
        self.assertIn('QLabel#DataGridStatusSuccess', styles)
        self.assertIn('background: #064E3B; color: #34D399;', styles)
        self.assertIn('background: #7F1D1D; color: #F87171;', styles)
        self.assertIn('background: #78350F; color: #FBBF24;', styles)
        self.assertIn("alternate-background-color: {c['row_alternate']}", styles)
        self.assertIn("letter-spacing: 0.2px", styles)

        self.assertIn('self.setProperty("dataPage", True)', accounts)
        self.assertIn('DataGridToolbar(', accounts)
        self.assertIn('DataGridPager(', accounts)
        self.assertIn('strftime("%b %d, %Y • %H:%M")', accounts)
        self.assertIn('setIconSize(QSize(16, 16))', accounts)
        self.assertIn('data_badge_host(provider_status)', accounts)

        self.assertIn('"Search lists..."', customers)
        self.assertIn('"Search customers..."', customers)
        self.assertIn('self.email_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)', customers)
        self.assertIn('"No matching records."', customers)

        self.assertIn('"Search templates..."', templates)
        self.assertIn('self.table.setColumnWidth(6, 80)', templates)
        self.assertIn('edit.setFixedWidth(32)', templates)
        self.assertIn('delete.setFixedWidth(44)', templates)

        self.assertIn('"Search tasks..."', reports)
        self.assertIn('"Search delivery history..."', reports)
        self.assertIn('setObjectName("RecipientReportTable")', reports)
        self.assertIn('data_badge_host(value)', reports)

        new_task = dialogs[dialogs.index("class NewTaskDialog") :]
        self.assertIn('self.accounts = QTableWidget(0, 4)', new_task)
        self.assertNotIn('QListWidget()', new_task)
        self.assertIn('["✓", "ACCOUNT NAME", "MODE", "STATUS"]', new_task)
        self.assertIn('self.accounts.setFixedHeight(CONST.data_grid_accounts_max_height)', new_task)
        self.assertIn('CONST.data_grid_accounts_max_height', new_task)
        self.assertIn('self.accounts_pager = DataGridPager', new_task)
        self.assertIn('self.accounts_toolbar = DataGridToolbar', new_task)

        invoice = dialogs[dialogs.index("class InvoiceTemplateDialog") : dialogs.index("class NewTaskDialog")]
        self.assertIn('self.items_toolbar = DataGridToolbar', invoice)
        self.assertIn('self.items_pager = DataGridPager', invoice)
        self.assertIn('self.items.setRowHidden(row, row not in visible_rows)', invoice)

    def test_v145_provider_cards_are_reparented_before_becoming_visible(self):
        root = Path(__file__).resolve().parents[1]
        page_source = (root / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        reflow = page_source.split("def _reflow_cards", 1)[1].split("def _apply_filter", 1)[0]
        self.assertIn("item.setVisible(False)", reflow)
        self.assertIn("self.grid.addWidget(item, row, column)", reflow)
        self.assertIn("item.setVisible(True)", reflow)
        self.assertLess(reflow.index("self.grid.addWidget(item, row, column)"), reflow.index("item.setVisible(True)"))
        self.assertNotIn("item.setVisible(item in visible_cards)", reflow)

    def test_application_icon_contract_uses_owner_asset_paths_and_windows_build_icon(self):
        root = Path(__file__).resolve().parents[1]
        app_source = (root / "src" / "app.py").read_text(encoding="utf-8")
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('("app.png", "app.ico")', app_source)
        self.assertIn('SetCurrentProcessExplicitAppUserModelID("VibTools.Invio")', app_source)
        self.assertIn("app.setWindowIcon(icon)", app_source)
        self.assertIn("windows-icon-from-ico: assets/icons/app.ico", workflow)
        self.assertIn('"app.png", "app.ico"', pyproject)

    def test_customer_default_settings_controls_and_import_wiring_are_present(self):
        root = Path(__file__).resolve().parents[1]
        settings_page = (root / "src" / "ui" / "pages" / "settings_page.py").read_text(encoding="utf-8")
        main_window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        customer_page = (root / "src" / "ui" / "pages" / "customer_lists_page.py").read_text(encoding="utf-8")
        self.assertIn("Default customer name", settings_page)
        self.assertIn("Default customer country", settings_page)
        self.assertIn("apply_customer_defaults", main_window)
        self.assertIn("default_name=self.app_settings.default_customer_name", main_window)
        self.assertIn("default_country=self.app_settings.default_customer_country", main_window)
        self.assertIn("email username", customer_page)
        self.assertIn("Settings default", customer_page)

    def test_provider_cards_use_official_plugin_visual_contract(self):
        root = Path(__file__).resolve().parents[1]
        page_source = (root / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        style_source = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('PROVIDER_CARD_HEIGHT = 194', page_source)
        self.assertIn('PROVIDER_CARD_MIN_WIDTH = 280', page_source)
        self.assertIn('PROVIDER_CARD_PADDING = 16', page_source)
        self.assertIn('PROVIDER_GRID_GAP = 16', page_source)
        self.assertIn('PROVIDER_LOGO_SIZE = 40', page_source)
        self.assertIn('PROVIDER_STATUS_HEIGHT = 18', page_source)
        self.assertIn('PROVIDER_MIN_COLUMNS = 2', page_source)
        self.assertIn('PROVIDER_MAX_COLUMNS = 4', page_source)
        self.assertIn('self.search_input = QLineEdit()', page_source)
        self.assertIn('self.search_input.setObjectName("ProviderSearchInput")', page_source)
        self.assertIn('self.search_input.textChanged.connect(self._apply_filter)', page_source)
        self.assertIn('item.setObjectName("PluginCard")', page_source)
        self.assertIn('item.setFixedHeight(PROVIDER_CARD_HEIGHT)', page_source)
        self.assertIn('item.setMinimumWidth(PROVIDER_CARD_MIN_WIDTH)', page_source)
        self.assertIn('"ProviderLogo"', page_source)
        self.assertIn('_PROVIDER_LOGO_FILES', page_source)
        self.assertIn('asset_path("icons", "providers", filename)', page_source)
        self.assertIn('status_badge("Verified" if installed else "Available"', page_source)
        self.assertIn('identity.addWidget(status, 0, Qt.AlignmentFlag.AlignLeft)', page_source)
        self.assertNotIn('brand.addWidget(status', page_source)
        self.assertIn('"ProviderVersionText"', page_source)
        self.assertIn('"PluginCardTitle"', page_source)
        self.assertIn('class _ElidedDescriptionLabel(QLabel):', page_source)
        self.assertNotIn('"ProviderLogoPlaceholder"', page_source)
        self.assertNotIn('"ProviderCapabilityChip"', page_source)
        self.assertNotIn('"ProviderMeta"', page_source)
        self.assertNotIn('f"Runtime:', page_source)
        self.assertIn('layout.addStretch(1)', page_source)
        self.assertIn('action.setObjectName("ProviderUninstallButton")', page_source)
        self.assertIn('footer.addWidget(version, 0, Qt.AlignmentFlag.AlignRight', page_source)
        self.assertIn('self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)', page_source)
        self.assertIn('divmod(index, columns)', page_source)
        self.assertIn('QFrame#PluginCard', style_source)
        self.assertIn("background: {c['nested_surface']};", style_source)
        self.assertIn('QLabel#ProviderLogo', style_source)
        self.assertIn('QLabel#ProviderVersionText', style_source)
        self.assertIn('QLineEdit#ProviderSearchInput', style_source)
        self.assertIn('QPushButton#ProviderUninstallButton', style_source)
        self.assertIn('QPushButton#ProviderLoadButton', style_source)
        self.assertIn('QFrame#PluginCard QLabel#StatusBadgeSuccess', style_source)
        self.assertIn('font-size: 9px;', style_source)
        self.assertNotIn('QLabel#ProviderLogoPlaceholder', style_source)
        self.assertNotIn('QLabel#ProviderCapabilityChip', style_source)
        self.assertIn('"providers/*.png"', pyproject)
        for name in ("stripe.png", "refrens.png", "agiled.png", "odoo.png"):
            self.assertTrue((root / "assets" / "icons" / "providers" / name).is_file())

    def test_current_runtime_surfaces_have_no_ui_only_release_markers(self):
        root = Path(__file__).resolve().parents[1]
        paths = list((root / "src").rglob("*.py")) + list((root / "providers" / "packages").rglob("*.json"))
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
        self.assertIn('button("Reset Settings")', source)
        self.assertIn('self.search_input.setPlaceholderText("Search settings... (Ctrl+F)")', source)
        self.assertIn('self.search_input.textChanged.connect(self._filter_settings_cards)', source)
        self.assertIn('QShortcut(QKeySequence.StandardKey.Find, self)', source)
        self.assertNotIn('button("Restore Defaults")', source)

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
        self.assertIn("os.replace(target, staged_manifest)", manager_source)
        self.assertIn("os.replace(staged_manifest, target)", manager_source)

    def test_application_owned_modals_use_compact_geometry(self):
        root = Path(__file__).resolve().parents[1]
        dialog_source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        window_source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(dialog_source.count("_apply_compact_dialog_geometry("), 5)
        self.assertIn("def compact_message_box(", dialog_source)
        self.assertIn("compact_message_box(self, title, text, icon=icon)", window_source)
        self.assertNotIn("QMessageBox.question(", window_source)

    def test_v1420_global_dialog_visual_contract_is_scoped_and_uniform(self):
        root = Path(__file__).resolve().parents[1]
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertIn("CONST.dialog_padding", dialogs)
        self.assertIn("CONST.dialog_gap", dialogs)
        self.assertIn("def _dialog_footer", dialogs)
        self.assertIn('button(primary_text, "primary")', dialogs)
        self.assertNotIn("QDialogButtonBox", dialogs)
        for removed in (
            "Create a named list first, then upload customer email addresses into that list.",
            "Only installed providers are available. Credentials are saved through protected credential storage",
            "Reusable invoice content only. Customer, billing, shipping and payment details remain outside templates.",
            "Select a provider, one or more available provider accounts, an invoice template and a customer list.",
        ):
            self.assertNotIn(removed, dialogs)
        self.assertIn("QDialog QLineEdit", styles)
        self.assertIn("QDialog QPushButton", styles)
        self.assertIn("placeholder-text-color: {c['text_placeholder']}", styles)
        self.assertIn("border-radius: {CONST.form_radius}px", styles)

    def test_add_account_dialog_uses_compact_two_column_provider_fields(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn("width_ratio=0.64", source)
        self.assertIn("QGridLayout(self.credentials_host)", source)
        self.assertIn("column_count = 2 if len(provider.credential_fields) > 2 else 1", source)
        self.assertIn("row, column = divmod(index, column_count)", source)

    def test_dashboard_uses_actual_invio_state_metrics(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "pages" / "dashboard_page.py").read_text(encoding="utf-8")
        for model in ("invoice_templates", "customer_lists", "account_reservations", "state.tasks"):
            self.assertIn(model, source)
        self.assertNotIn("License Summary", source)
        self.assertNotIn("Authorized", source)

    def test_invoice_template_dialog_has_global_template_fields_and_compact_items_table(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        for marker in (
            "SUPPORTED_INVOICE_CURRENCIES",
            'form_group("Invoice note (optional)"',
            'form_group("Customer note (optional)"',
            'form_group("Invoice type"',
            '["DESCRIPTION", "QUANTITY", "UNIT AMOUNT", "TAX %"]',
            'self.items.verticalHeader().setVisible(False)',
        ):
            self.assertIn(marker, source)
        self.assertIn('invoice_template_id', source)

    def test_settings_checked_checkbox_uses_visible_checkmark_asset(self):
        root = Path(__file__).resolve().parents[1]
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertTrue((root / "assets" / "icons" / "checkmark.svg").is_file())
        self.assertIn('QCheckBox::indicator:checked', styles)
        self.assertIn('image: url("{check_icon}")', styles)
        self.assertIn('QWidget#SettingsPage QCheckBox', styles)
        self.assertIn('QCheckBox {{ spacing: 8px; color:', styles)

    def test_settings_page_uses_scoped_compact_searchable_responsive_contract(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "pages" / "settings_page.py").read_text(encoding="utf-8")
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertIn("root.setContentsMargins(CONST.page_padding", source)
        self.assertIn("_SETTINGS_MIN_CARD_WIDTH = 360", source)
        self.assertIn("self.settings_grid.setHorizontalSpacing(_SETTINGS_GRID_GAP)", source)
        self.assertIn("self.search_input.textChanged.connect(self._filter_settings_cards)", source)
        self.assertIn("def _reflow_settings_grid", source)
        self.assertIn("self.settings_grid.addWidget(settings_card, row, 0, 1, 2)", source)
        self.assertIn("self.default_customer_country.setMaximumWidth(_SETTINGS_COUNTRY_FIELD_WIDTH)", source)
        self.assertIn("QWidget#SettingsPage QLabel#Caption", styles)
        self.assertIn("QWidget#SettingsPage QLabel#FormLabel", styles)
        self.assertIn("QWidget#SettingsPage QLineEdit", styles)
        self.assertIn("QWidget#SettingsPage QPushButton", styles)
        for removed in (
            "Choose what you see when Invio opens",
            "Keep confirmation prompts for actions",
            "Control how the Live Logs page displays",
            "Choose the starting folder used by provider loading",
            "Fill missing customer identity data during import",
        ):
            self.assertNotIn(removed, source)

    def test_live_logs_and_reports_use_compact_reference_aligned_surfaces(self):
        root = Path(__file__).resolve().parents[1]
        logs = (root / "src" / "ui" / "pages" / "logs_page.py").read_text(encoding="utf-8")
        reports = (root / "src" / "ui" / "pages" / "reports_page.py").read_text(encoding="utf-8")
        self.assertIn('button("Save Logs")', logs)
        self.assertIn('button("Clear Logs", "danger")', logs)
        self.assertIn('setObjectName("CompactControlBar")', logs)
        self.assertIn('setObjectName("LogViewer")', logs)
        self.assertIn('setObjectName("ReportTableSurface")', reports)
        self.assertIn('setObjectName("ReportTable")', reports)

    def test_task_dialog_requires_invoice_template_selection(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn('self.invoice_template', source)
        self.assertIn('"invoice_template_id": str(self.invoice_template.currentData())', source)

    def test_stylesheet_generation_is_runtime_safe(self):
        from src.ui.styles import app_qss

        qss = app_qss()
        self.assertIn("checkmark.svg", qss)
        self.assertIn("QWidget#SettingsPage", qss)
        self.assertIn("QPlainTextEdit#LogViewer", qss)

    def test_invoice_currency_catalog_is_uppercase_and_broad(self):
        from src.invoices.templates import SUPPORTED_INVOICE_CURRENCIES

        self.assertGreaterEqual(len(SUPPORTED_INVOICE_CURRENCIES), 135)
        self.assertEqual(len(SUPPORTED_INVOICE_CURRENCIES), len(set(SUPPORTED_INVOICE_CURRENCIES)))
        self.assertTrue(all(code == code.upper() for code in SUPPORTED_INVOICE_CURRENCIES))
        for required in ("USD", "EUR", "GBP", "BDT", "JPY", "INR"):
            self.assertIn(required, SUPPORTED_INVOICE_CURRENCIES)

    def test_scroll_backdrops_use_explicit_dark_surface(self):
        root = Path(__file__).resolve().parents[1]
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertIn("QScrollArea#MinimalScrollArea::viewport", styles)
        self.assertIn("QWidget#SettingsContent, QWidget#DialogContent", styles)
        self.assertIn("background: {c['page_background']}; border: none;", styles)

    def test_invoice_currency_uses_searchable_compact_completion(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn("self.currency.setEditable(True)", source)
        self.assertIn("QComboBox.InsertPolicy.NoInsert", source)
        self.assertIn("self.currency.setMaxVisibleItems(8)", source)
        self.assertIn("QCompleter(SUPPORTED_INVOICE_CURRENCIES, self.currency)", source)
        self.assertIn("Qt.MatchFlag.MatchContains", source)
        self.assertIn("currency_code not in SUPPORTED_INVOICE_CURRENCIES", source)
        self.assertIn("settings_grid.setColumnStretch(0, 2)", source)
        self.assertIn("settings_grid.setColumnStretch(1, 3)", source)

    def test_invoice_template_cards_do_not_absorb_scroll_viewport_height(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        invoice_source = source[source.index("class InvoiceTemplateDialog") : source.index("class NewTaskDialog")]
        self.assertNotIn(
            "setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)",
            invoice_source,
        )
        self.assertIn("upper_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)", source)
        self.assertIn("content_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)", source)
        self.assertIn("content_layout.addWidget(upper_host, 0, Qt.AlignmentFlag.AlignTop)", source)
        self.assertIn("upper.addWidget(settings_card, 0, 0, Qt.AlignmentFlag.AlignTop)", source)
        self.assertIn("upper.addWidget(content_card, 0, 1, Qt.AlignmentFlag.AlignTop)", source)
        self.assertIn("content_layout.addWidget(secondary_card, 0, Qt.AlignmentFlag.AlignTop)", source)
        self.assertIn("content_layout.addWidget(items_card, 0, Qt.AlignmentFlag.AlignTop)", source)
        self.assertIn("content_layout.addStretch(1)", source)
        self.assertIn("upper.setAlignment(Qt.AlignmentFlag.AlignTop)", source)
        self.assertIn("secondary_grid.setAlignment(Qt.AlignmentFlag.AlignTop)", source)

    def test_invoice_template_compact_groups_remove_verbose_help_without_changing_fields(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn("def _invoice_form_group", source)
        self.assertIn('_invoice_form_group("Currency", self.currency)', source)
        self.assertIn('_invoice_form_group("Days until due", self.days_due)', source)
        self.assertIn('_invoice_form_group("Invoice type", self.invoice_type)', source)
        for removed in (
            "Displayed in uppercase; provider API formatting is handled automatically.",
            "BOS is used only by providers that support it.",
            "Provider-supported headings and customer-facing notes",
            "Tax rate is used by providers with direct line-tax support",
        ):
            self.assertNotIn(removed, source)
        self.assertIn("self.memo.setFixedHeight(52)", source)
        self.assertIn("self.customer_note.setFixedHeight(52)", source)
        self.assertIn("self.footer.setFixedHeight(52)", source)
        self.assertIn("self.terms.setFixedHeight(52)", source)

    def test_p01_real_account_api_verification_is_threaded_and_task_gated(self):
        root = Path(__file__).resolve().parents[1]
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        runtime = (root / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        state = (root / "src" / "core" / "state" / "app_state.py").read_text(encoding="utf-8")
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertIn("class _AccountVerificationWorker(QObject)", dialogs)
        self.assertIn("thread = QThread(self)", dialogs)
        self.assertIn('thread.setObjectName(f"InvioAccountApiTest-{provider.id}")', dialogs)
        self.assertIn("self.runtime.test_account(", dialogs)
        self.assertIn("def _ui_validate_credentials(self)", dialogs)
        self.assertIn("self.provider_runtime.supports_api_test(provider.id)", dialogs)
        self.assertIn('"status": "Verified"', dialogs)
        self.assertIn('account.status != "Verified"', dialogs)
        self.assertIn("API Test is unavailable for this provider", dialogs)
        self.assertIn("def supports_api_test(self, provider_id: str)", runtime)
        self.assertIn('mode=self.mode', dialogs)
        self.assertIn('if account.status != "Verified"', state)
        self.assertIn('dialog = AddAccountDialog(providers, self, provider_runtime=self.provider_runtime, log_callback=self.log)', window)
        self.assertIn('if account.status != "Verified"', window)

    def test_p02_durable_storage_is_wired_without_changing_task_thread_boundary(self):
        root = Path(__file__).resolve().parents[1]
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        app = (root / "src" / "app.py").read_text(encoding="utf-8")
        state = (root / "src" / "core" / "state" / "app_state.py").read_text(encoding="utf-8")
        self.assertIn('DomainStore(self.settings_manager.path.with_name("domain.sqlite3"))', window)
        self.assertIn("loaded_domain = self.domain_store.load(self.credential_store)", window)
        self.assertIn("domain_store=self.domain_store", window)
        self.assertIn("credential_store=self.credential_store", window)
        self.assertIn("except (OSError, ValueError, StateError) as exc", window)
        self.assertIn("self.worker_manager.stop(task_id)", window)
        self.assertIn("except DomainStoreError as exc", app)
        self.assertIn("self._domain_store.create_task_with_reservations(task)", state)
        self.assertIn("self._domain_store.update_task(task)", state)


    def test_p02_persistence_failure_marks_fault_before_stop_request(self):
        root = Path(__file__).resolve().parents[1]
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        method = window.split("def _task_persistence_failure", 1)[1].split("def _worker_status", 1)[0]
        self.assertLess(
            method.index("self._persistence_faulted_tasks.add(task_id)"),
            method.index("self.worker_manager.stop(task_id)"),
        )

    def test_p03_account_lifecycle_ui_and_verification_health_are_wired(self):
        root = Path(__file__).resolve().parents[1]
        page = (root / "src" / "ui" / "pages" / "accounts_page.py").read_text(encoding="utf-8")
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertIn('button("Edit")', page)
        self.assertIn('button("Re-test")', page)
        self.assertIn('button("Delete")', page)
        self.assertIn('"LAST API TEST"', page)
        self.assertIn('"Protected storage"', page)
        self.assertIn('"Not Installed"', page)
        self.assertIn('class AccountRetestDialog(QDialog)', dialogs)
        self.assertIn('thread.setObjectName(f"InvioAccountApiRetest-{self.account.id}")', dialogs)
        self.assertIn('account: Account | None = None', dialogs)
        self.assertIn('self.provider_combo.setEnabled(not self._provider_locked)', dialogs)
        self.assertIn('"Save Changes" if account is not None else "Add Account"', dialogs)
        self.assertIn('def edit_account(self, account_id: str)', window)
        self.assertIn('def retest_account(self, account_id: str)', window)
        self.assertIn('def delete_account(self, account_id: str)', window)

    def test_p03_provider_uninstall_and_task_execution_are_consistent(self):
        root = Path(__file__).resolve().parents[1]
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        uninstall = window.split("def uninstall_provider", 1)[1].split("def load_provider", 1)[0]
        runner = window.split("def _runner_for_task", 1)[1].split("def start_task", 1)[0]
        self.assertIn('self.worker_manager.is_running(task.id)', uninstall)
        self.assertIn('Existing accounts, protected credentials, tasks and reservations will remain saved', uninstall)
        self.assertIn('self.providers.get_installed(task.provider_id)', runner)
        self.assertIn('Reinstall the provider before starting or retrying this task.', runner)

    def test_v1440_intro_and_subtitle_cleanup_is_scope_locked(self):
        root = Path(__file__).resolve().parents[1]
        widgets = (root / "src" / "ui" / "widgets.py").read_text(encoding="utf-8")
        tasks = (root / "src" / "ui" / "pages" / "tasks_page.py").read_text(encoding="utf-8")
        providers = (root / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        dashboard = (root / "src" / "ui" / "pages" / "dashboard_page.py").read_text(encoding="utf-8")
        self.assertNotIn('text_layout.addWidget(label(description, "Description", True))', widgets)
        self.assertNotIn('layout.addWidget(label(description, "Description", True))', widgets)
        self.assertEqual(widgets.count("_ = description"), 2)
        self.assertNotIn("Independent provider task with dedicated account reservation and worker-thread slot.", tasks)
        self.assertIn('self.setObjectName("PluginCardDescription")', providers)
        self.assertIn('self.next_step = label("", "Description")', dashboard)

    def test_worker_manager_declares_task_scoped_qthreads(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        self.assertIn("self._slots: dict[str, _WorkerSlot]", source)
        self.assertIn("thread = QThread(self)", source)
        self.assertIn('thread.setObjectName(f"InvioTaskThread-{task.id}")', source)
        self.assertNotIn("self.thread: QThread", source)


    def test_p04_customer_page_and_import_contract_are_customer_aware(self):
        page = (Path(__file__).resolve().parents[1] / "src" / "ui" / "pages" / "customer_lists_page.py").read_text(encoding="utf-8")
        main_window = (Path(__file__).resolve().parents[1] / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        importer = (Path(__file__).resolve().parents[1] / "src" / "customers" / "importers" / "email_importer.py").read_text(encoding="utf-8")
        model = (Path(__file__).resolve().parents[1] / "src" / "customers" / "models" / "customer_list.py").read_text(encoding="utf-8")
        self.assertIn('["#", "EMAIL", "NAME", "COUNTRY"]', page)
        self.assertIn('button("Upload Customers")', page)
        self.assertIn('import_customers(path)', main_window)
        self.assertIn('class CustomerRecord', model)
        self.assertIn('def import_emails', importer)
        self.assertIn('def import_customers', importer)
        self.assertNotIn('Only email addresses are stored', page)

    def test_p04_import_passes_source_rows_into_existing_list_merge(self):
        root = Path(__file__).resolve().parents[1]
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertIn(
            "self.state.add_customers(list_id, normalized_records, source_rows=imported.record_rows)",
            window,
        )

    def test_p04_verification_restores_out_of_scope_dashboard_label(self):
        root = Path(__file__).resolve().parents[1]
        dashboard = (root / "src" / "ui" / "pages" / "dashboard_page.py").read_text(encoding="utf-8")
        self.assertIn('("customers", "Customer Emails")', dashboard)
        self.assertNotIn('("customers", "Customers")', dashboard)
    def test_p06_provider_page_uses_actual_installed_manifest_for_declared_capabilities(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        self.assertIn("installed_by_id", source)
        self.assertIn("installed_by_id.get(provider.id, provider)", source)

    def test_p06_runtime_capability_display_fails_closed_on_manifest_mismatch(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        block = source[source.index("def _runtime_capabilities_for_provider"):source.index("def _provider_manifest_contract_error")]
        self.assertIn("manifest_runtime_contract_matches", block)
        self.assertIn("effective_capabilities(provider)", block)



class V1460TitleBarContractTests(unittest.TestCase):
    def test_v1460_main_window_uses_custom_frameless_title_bar(self):
        root = Path(__file__).resolve().parents[1]
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        chrome = (root / "src" / "ui" / "title_bars.py").read_text(encoding="utf-8")
        self.assertIn("enable_frameless_window(self)", window)
        self.assertIn('MainTitleBar(self, "Invio", "Home / Accounts")', window)
        self.assertIn('self.main_title_bar.set_context(f"Home / {name}")', window)
        self.assertIn("class MainTitleBar(TitleBar):", chrome)
        self.assertIn("FramelessWindowHint", chrome)
        self.assertIn("startSystemMove", chrome)
        self.assertIn("startSystemResize", chrome)
        self.assertIn("showMinimized", chrome)
        self.assertIn("showMaximized", chrome)

    def test_v1460_app_owned_dialogs_use_compact_custom_title_bar(self):
        root = Path(__file__).resolve().parents[1]
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        chrome = (root / "src" / "ui" / "title_bars.py").read_text(encoding="utf-8")
        app = (root / "src" / "app.py").read_text(encoding="utf-8")
        self.assertIn("class DialogTitleBar(TitleBar):", chrome)
        self.assertIn("build_dialog_shell", dialogs)
        self.assertGreaterEqual(dialogs.count("build_dialog_shell(self)"), 5)
        self.assertIn("install_dialog_chrome(box, preserve_client_height=False)", dialogs)
        self.assertNotIn("install_dialog_chrome(box, box.layout()", dialogs)
        self.assertIn('compact_message_box(None, "Invio Runtime Resources"', app)
        self.assertNotIn("QMessageBox.critical(", app)

    def test_v1460_title_bar_styles_are_scoped_to_custom_chrome(self):
        root = Path(__file__).resolve().parents[1]
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        tokens = (root / "src" / "ui" / "tokens.py").read_text(encoding="utf-8")
        self.assertIn("QFrame#MainTitleBar", styles)
        self.assertIn("QFrame#DialogTitleBar", styles)
        self.assertIn("QPushButton#MainTitleClose:hover", styles)
        self.assertIn("QPushButton#DialogTitleClose:hover", styles)
        self.assertIn("main_titlebar_height: int = 32", tokens)
        self.assertIn("dialog_titlebar_height: int = 30", tokens)



class V1470DesktopDesignSystemContractTests(unittest.TestCase):
    def test_v147_single_global_app_header_replaces_legacy_double_header(self):
        root = Path(__file__).resolve().parents[1]
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        chrome = (root / "src" / "ui" / "title_bars.py").read_text(encoding="utf-8")
        self.assertIn('MainTitleBar(self, "Invio", "Home / Accounts")', window)
        shell = window.split("def _build_shell", 1)[1].split("def _nav_icon", 1)[0]
        self.assertNotIn("_build_header()", shell)
        self.assertNotIn('setObjectName("WindowHeader")', window)
        self.assertIn('self.main_title_bar.set_context(f"Home / {name}")', window)
        self.assertIn('asset_path("icons", "window", icon_name)', chrome)
        self.assertIn('TitleBarContextDivider', chrome)

    def test_v147_sidebar_is_grouped_and_uses_packaged_svg_icon_family(self):
        root = Path(__file__).resolve().parents[1]
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        tokens = (root / "src" / "ui" / "tokens.py").read_text(encoding="utf-8")
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertIn("NAV_GROUPS", tokens)
        self.assertIn('("MAIN", (', tokens)
        self.assertIn('("OPERATIONS", (', tokens)
        self.assertIn('("SETTINGS", (', tokens)
        self.assertIn('asset_path("icons", "nav", f"{icon_key}.svg")', window)
        self.assertIn('label(group_name, "SidebarSectionLabel", False)', window)
        self.assertIn('setObjectName("SidebarFooter")', window)
        self.assertIn('QLabel#SidebarSectionLabel', styles)
        self.assertIn('QFrame#SidebarFooter', styles)
        for name in ("dashboard", "accounts", "invoice", "customers", "tasks", "providers", "reports", "logs", "settings"):
            self.assertTrue((root / "assets" / "icons" / "nav" / f"{name}.svg").is_file(), name)

    def test_v147_dialog_shell_overlay_footer_and_focus_contract(self):
        root = Path(__file__).resolve().parents[1]
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        chrome = (root / "src" / "ui" / "title_bars.py").read_text(encoding="utf-8")
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertIn("def build_dialog_shell", chrome)
        self.assertIn('body.setObjectName("DialogBody")', chrome)
        self.assertIn('setObjectName("ModalOverlay")', chrome)
        self.assertGreaterEqual(dialogs.count("build_dialog_shell(self)"), 5)
        self.assertIn('host.setObjectName("DialogActionFooter")', dialogs)
        self.assertIn('primary_button.setDefault(True)', dialogs)
        self.assertIn('QTimer.singleShot(0, self.name_edit.setFocus)', dialogs)
        self.assertIn('QWidget#ModalOverlay', styles)
        self.assertIn('QWidget#DialogActionFooter', styles)

    def test_v147_component_states_dropdown_icons_and_inline_feedback_are_centralized(self):
        root = Path(__file__).resolve().parents[1]
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        widgets = (root / "src" / "ui" / "widgets.py").read_text(encoding="utf-8")
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn('validationState="error"', styles)
        self.assertIn('validationState="success"', styles)
        self.assertIn('QComboBox::down-arrow', styles)
        self.assertIn('QSpinBox::up-arrow', styles)
        self.assertIn('QLabel#InlineStatusSuccess', styles)
        self.assertIn('def set_inline_status', widgets)
        self.assertIn('inline_status("API test has not been run.", "neutral")', dialogs)
        self.assertIn('set_inline_status(self.validation_label, safe, "success")', dialogs)
        for name in ("chevron-down.svg", "chevron-up.svg"):
            self.assertTrue((root / "assets" / "icons" / name).is_file(), name)

    def test_v147_accounts_empty_state_is_not_rendered_as_a_fake_tree_record(self):
        root = Path(__file__).resolve().parents[1]
        accounts = (root / "src" / "ui" / "pages" / "accounts_page.py").read_text(encoding="utf-8")
        self.assertIn('data_grid_empty_label("No accounts found.")', accounts)
        self.assertNotIn('QTreeWidgetItem(["No matching records."', accounts)



if __name__ == "__main__":
    unittest.main()


class P05UiContractTests(unittest.TestCase):
    def test_p05_legacy_tasks_are_blocked_in_ui_and_backend_gate(self):
        root = Path(__file__).resolve().parents[1]
        task_page = (root / "src" / "ui" / "pages" / "tasks_page.py").read_text(encoding="utf-8")
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertIn("snapshot_ready = task.has_immutable_execution_snapshot", task_page)
        self.assertIn("self.start_btn.setEnabled(snapshot_ready", task_page)
        self.assertIn("self.retry_btn.setEnabled(snapshot_ready", task_page)
        self.assertIn("LEGACY_SNAPSHOT_MESSAGE", task_page)
        runner = window.split("def _runner_for_task", 1)[1].split("def start_task", 1)[0]
        self.assertIn("if not task.has_immutable_execution_snapshot", runner)
        self.assertIn("LEGACY_SNAPSHOT_MESSAGE", runner)
        start = window.split("def start_task", 1)[1].split("def pause_task", 1)[0]
        self.assertIn("if task.has_immutable_execution_snapshot", start)
        self.assertIn("Task Snapshot Unavailable", start)

    def test_p05_runtime_reads_durable_snapshot_not_live_customer_or_template_content(self):
        root = Path(__file__).resolve().parents[1]
        runtime = (root / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        snapshot_method = runtime.split("def _snapshot", 1)[1].split("def _run_stripe_batch", 1)[0]
        self.assertIn("execution = task.execution_snapshot", snapshot_method)
        self.assertIn("execution.template.to_template()", snapshot_method)
        self.assertIn("execution.customers", snapshot_method)
        self.assertNotIn("state.customer_lists.get", snapshot_method)
        self.assertNotIn("state.invoice_templates.get", snapshot_method)

    def test_p05_does_not_change_worker_manager_thread_architecture(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        self.assertIn("thread = QThread(self)", source)
        self.assertIn('thread.setObjectName(f"InvioTaskThread-{task.id}")', source)


class P06UiContractTests(unittest.TestCase):
    def test_p06_new_task_runs_preflight_before_state_task_creation(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        new_task = source.split("def new_task", 1)[1].split("def _runner_for_task", 1)[0]
        self.assertIn("preflight_candidate(", new_task)
        self.assertIn("if not result.passed:", new_task)
        self.assertLess(new_task.index("preflight_candidate("), new_task.index("self.state.create_task(**payload)"))

    def test_p06_start_and_retry_share_preflight_gate_before_runner_creation(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runner = source.split("def _runner_for_task", 1)[1].split("def start_task", 1)[0]
        self.assertIn("preflight_task(", runner)
        self.assertIn("if not result.passed:", runner)
        self.assertLess(runner.index("preflight_task("), runner.index("self.provider_runtime.make_task_runner"))
        self.assertIn("retry_failed=retry_failed", runner)

    def test_p06_provider_page_separates_declared_and_runtime_capabilities(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        self.assertIn("runtime_capabilities", source)
        self.assertIn("runtime_adapter_status", source)
        self.assertNotIn("Declared capabilities:", source)
        self.assertNotIn("Runtime capabilities:", source)

    def test_p06_refrens_endpoint_is_validated_before_auth_payload(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "core" / "provider_runtime" / "runtime.py").read_text(encoding="utf-8")
        auth = source.split("def _refrens_auth", 1)[1].split("def _refrens_request", 1)[0]
        self.assertLess(auth.index("canonical_refrens_base_url"), auth.index('payload = {"strategy": "app-secret"'))


class P07UiContractTests(unittest.TestCase):
    def test_p07_tasks_page_exposes_deterministic_state_actions_without_new_page(self):
        root = Path(__file__).resolve().parents[1]
        page = (root / "src" / "ui" / "pages" / "tasks_page.py").read_text(encoding="utf-8")
        self.assertIn("self.start_btn.setText(policy.start_label)", page)
        self.assertIn("self.start_btn.setEnabled(snapshot_ready and policy.start_enabled)", page)
        self.assertIn("self.retry_btn.setEnabled(snapshot_ready and policy.retry_enabled)", page)
        self.assertIn("self.close_btn.setEnabled(policy.close_enabled)", page)
        self.assertNotIn('task.status in {"Ready", "Stopped", "Failed", "Completed"}', page)

    def test_v10014801_task_close_confirmation_forces_widget_message_box_before_custom_chrome(self):
        root = Path(__file__).resolve().parents[1]
        dialog_source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        window_source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")

        compact = dialog_source.split("def compact_message_box", 1)[1].split("def _invoice_wrapped_label", 1)[0]
        self.assertIn("force_widget_dialog: bool = False", compact)
        self.assertIn("QMessageBox.Option.DontUseNativeDialog", compact)
        self.assertLess(
            compact.index("box.setOption(QMessageBox.Option.DontUseNativeDialog, True)"),
            compact.index("box.setWindowTitle(title)"),
        )

        close = window_source.split("def close_task", 1)[1].split("def _task_persistence_failure", 1)[0]
        self.assertIn('"Close Task"', close)
        self.assertIn("force_widget_dialog=True", close)
        self.assertIn("self.state.close_task(task_id)", close)
        self.assertLess(close.index("force_widget_dialog=True"), close.index("self.state.close_task(task_id)"))

    def test_p07_start_routes_stopped_task_to_resume_remaining_and_never_rewrites_blocked_status(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        start = source.split("def start_task", 1)[1].split("def pause_task", 1)[0]
        self.assertIn('TaskAction.RESUME_REMAINING if task.status == "Stopped" else TaskAction.START', start)
        self.assertIn("resume_remaining=resume_remaining", start)
        self.assertNotIn('self.state.set_task_status(task_id, "Ready"', start)

    def test_p07_runner_gate_blocks_duplicate_worker_before_runtime_state_mutation(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runner = source.split("def _runner_for_task", 1)[1].split("def start_task", 1)[0]
        self.assertIn("self.worker_manager.is_running(task_id)", runner)
        self.assertLess(runner.index("self.worker_manager.is_running(task_id)"), runner.index("preflight_task("))

    def test_p07_retry_and_resume_fail_closed_for_injected_runner(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        runner = source.split("def _runner_for_task", 1)[1].split("def start_task", 1)[0]
        self.assertIn("if retry_failed or resume_remaining:", runner)
        self.assertIn("EXTERNAL_CONTINUATION_UNAVAILABLE_MESSAGE", runner)
        self.assertIn("retry_failed=retry_failed", runner)
        self.assertIn("resume_remaining=resume_remaining", runner)

    def test_p07_app_state_uses_central_transition_validator(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "core" / "state" / "app_state.py").read_text(encoding="utf-8")
        status = source.split("def set_task_status", 1)[1].split("def set_task_progress", 1)[0]
        self.assertIn("validate_status_transition(task.status, status)", status)
        close = source.split("def close_task", 1)[1].split("def set_task_status", 1)[0]
        self.assertIn("require_task_action(task, TaskAction.CLOSE)", close)

    def test_p07_worker_finish_reconciles_runtime_recipient_sets_before_terminal_status(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        block = source.split("def _worker_finished", 1)[1].split("# Reports / logs", 1)[0]
        self.assertIn("summary = self.provider_runtime.delivery_summary(task)", block)
        self.assertIn("if summary is not None and summary.continuation_safe", block)
        self.assertLess(block.index("self.state.set_task_progress"), block.index("self.state.set_task_status"))


    def test_p07_correction_disables_stale_worker_controls_and_reconciles_late_completed_signal(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        policy = source.split("def _task_action_policy", 1)[1].split("def _require_task_action", 1)[0]
        self.assertIn("active_worker_available=self.worker_manager.is_running(task.id)", policy)
        for method, next_method in (("pause_task", "resume_task"), ("resume_task", "stop_task"), ("stop_task", "retry_task")):
            block = source.split(f"def {method}", 1)[1].split(f"def {next_method}", 1)[0]
            self.assertIn("self._require_active_worker(task)", block)
        finished = source.split("def _worker_finished", 1)[1].split("# Reports / logs", 1)[0]
        self.assertIn("reconcile_worker_terminal_status(task.status, status)", finished)
        self.assertIn("there are no recipients remaining to resume", finished)

    def test_p07_correction_distinguishes_safe_empty_continuation_from_lost_identity_state(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        block = source.split("def _task_continuation_message", 1)[1].split("def _task_action_policy", 1)[0]
        self.assertIn("NO_REMAINING_RECIPIENTS_MESSAGE", block)
        self.assertIn("NO_FAILED_RECIPIENTS_MESSAGE", block)
        self.assertIn("summary.continuation_safe", block)

    def test_p07_worker_manager_thread_architecture_remains_unchanged(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        self.assertIn("thread = QThread(self)", source)
        self.assertIn('thread.setObjectName(f"InvioTaskThread-{task.id}")', source)
        self.assertNotIn("ThreadPoolExecutor", source)


class V1480DialogChromePolishContractTests(unittest.TestCase):
    def test_v148_title_bars_keep_compact_right_margin_after_close_controls(self):
        root = Path(__file__).resolve().parents[1]
        chrome = (root / "src" / "ui" / "title_bars.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(
            chrome.count("layout.setContentsMargins(10, 0, CONST.space_compact, 0)"), 2
        )

    def test_v148_dialog_surface_has_subtle_border_shadow_and_transparent_outer_chrome(self):
        root = Path(__file__).resolve().parents[1]
        chrome = (root / "src" / "ui" / "title_bars.py").read_text(encoding="utf-8")
        styles = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertIn("QGraphicsDropShadowEffect", chrome)
        self.assertIn("shadow.setBlurRadius(12.0)", chrome)
        self.assertIn("shadow.setOffset(0.0, 2.0)", chrome)
        self.assertIn("QColor(0, 0, 0, 96)", chrome)
        self.assertIn('surface.setObjectName("DialogSurface")', chrome)
        self.assertIn("WA_TranslucentBackground", chrome)
        self.assertIn("QFrame#DialogSurface", styles)
        self.assertIn("border: 1px solid #2D3748", styles)

    def test_v148_form_dialog_title_is_rendered_once_by_custom_title_bar(self):
        root = Path(__file__).resolve().parents[1]
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        for window_title in (
            'self.setWindowTitle("New Customer List")',
            'self.setWindowTitle("Re-test Account")',
            'self.setWindowTitle("Invoice Template")',
            'self.setWindowTitle("New Task")',
        ):
            self.assertIn(window_title, dialogs)
        self.assertIn('self.setWindowTitle("Edit Account" if account is not None else "Add Account")', dialogs)
        for duplicate in (
            'label("Create Customer List", "PageTitle", False)',
            'label("Edit Provider Account" if account is not None else "Add Provider Account", "PageTitle", False)',
            'label("Re-test Provider Account", "PageTitle", False)',
            'label("Invoice Template", "PageTitle", False)',
            'label("Create Task", "PageTitle", False)',
        ):
            self.assertNotIn(duplicate, dialogs)



class V1484NewTaskCompactModalContractTests(unittest.TestCase):
    def test_v1484_new_task_modal_uses_only_the_approved_compact_rows(self):
        root = Path(__file__).resolve().parents[1]
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        new_task = dialogs[dialogs.index("class NewTaskDialog") :]

        self.assertIn(
            "self, parent, width_ratio=0.62, preferred_height=430, min_width=760, max_width=920, min_height=400",
            new_task,
        )
        self.assertIn('toolbar_row.setObjectName("NewTaskToolbarRow")', new_task)
        self.assertIn('toolbar_layout.addWidget(self.provider_combo)', new_task)
        self.assertIn('toolbar_layout.addWidget(self.accounts_toolbar, 1)', new_task)
        self.assertIn('account_toolbar_layout.addWidget(account_filter)', new_task)
        self.assertIn('account_toolbar_layout.addWidget(self.accounts_toolbar.search)', new_task)
        self.assertNotIn('root.addWidget(form_group("Provider", self.provider_combo))', new_task)
        self.assertNotIn('root.addWidget(label("Accounts", "FormLabel", False))', new_task)

        self.assertIn('self.accounts.setHorizontalHeaderLabels(["✓", "ACCOUNT NAME", "MODE", "STATUS"])', new_task)
        self.assertIn('self.accounts.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)', new_task)
        self.assertIn('self.accounts.setFixedHeight(CONST.data_grid_accounts_max_height)', new_task)
        self.assertIn('self.accounts_pager = DataGridPager(on_changed=self._refresh_accounts)', new_task)
        self.assertIn('root.addWidget(self.accounts_pager)', new_task)

        self.assertIn('bottom_row.setObjectName("NewTaskBottomRow")', new_task)
        self.assertIn('bottom_layout.addWidget(self.invoice_template, 1)', new_task)
        self.assertIn('bottom_layout.addWidget(self.customer_list, 1)', new_task)
        self.assertIn('cancel_button.clicked.connect(self.reject)', new_task)
        self.assertIn('create_button.clicked.connect(self._validate_and_accept)', new_task)
        self.assertIn('create_button.setDefault(True)', new_task)
        self.assertNotIn('root.addWidget(_dialog_footer("Create Task"', new_task)

    def test_v1484_new_task_business_validation_and_payload_contract_remain_intact(self):
        root = Path(__file__).resolve().parents[1]
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        new_task = dialogs[dialogs.index("class NewTaskDialog") :]
        validation = new_task.split("def _validate_and_accept", 1)[1].split("def payload", 1)[0]
        payload = new_task.split("def payload", 1)[1]

        for message in (
            "Install and select a provider.",
            "Select at least one available account.",
            "Create and select an invoice template.",
            "Create and select a customer list.",
        ):
            self.assertIn(message, validation)
        self.assertIn("self.accept()", validation)
        for key in (
            '"provider_id": provider.id',
            '"provider_name": provider.name',
            '"account_ids": self.selected_account_ids()',
            '"invoice_template_id": str(self.invoice_template.currentData())',
            '"customer_list_id": str(self.customer_list.currentData())',
        ):
            self.assertIn(key, payload)

    def test_v1484_runtime_interaction_suite_covers_new_task_modal_workflow(self):
        root = Path(__file__).resolve().parents[1]
        runtime_test = (root / "tests" / "test_ui_runtime_interactions.py").read_text(encoding="utf-8")
        self.assertIn("class NewTaskDialogRuntimeInteractionTests", runtime_test)
        for token in (
            "dialog.show()",
            "dialog.reject()",
            "dialog.provider_combo.setCurrentIndex",
            "dialog.accounts_toolbar.search.setText",
            "dialog.accounts_toolbar.filters[0].setCurrentIndex",
            "dialog.accounts.item(0, 0).setCheckState",
            "dialog.accounts.verticalScrollBar().maximum()",
            "dialog.invoice_template.setCurrentIndex",
            "dialog.customer_list.setCurrentIndex",
            'self._button(dialog, "Cancel").click()',
            'self._button(dialog, "Create Task").click()',
            "dialog.payload()",
        ):
            self.assertIn(token, runtime_test)



class V14802PopupLifecycleContractTests(unittest.TestCase):
    def test_v14802_message_box_chrome_reacquires_live_layout_after_window_mutation(self):
        root = Path(__file__).resolve().parents[1]
        dialogs = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        chrome = (root / "src" / "ui" / "title_bars.py").read_text(encoding="utf-8")

        compact = dialogs.split("def compact_message_box", 1)[1].split("def _invoice_wrapped_label", 1)[0]
        self.assertIn("box.setOption(QMessageBox.Option.DontUseNativeDialog, True)", compact)
        self.assertNotIn("install_dialog_chrome(box, box.layout()", compact)
        self.assertIn("install_dialog_chrome(box, preserve_client_height=False)", compact)

        install = chrome.split("def install_dialog_chrome", 1)[1]
        self.assertIn("layout = dialog.layout()", install)
        self.assertIn('raise RuntimeError("Custom dialog chrome requires a live dialog layout.")', install)
        self.assertLess(install.index("enable_frameless_window(dialog)"), install.index("layout = dialog.layout()"))
        self.assertLess(install.index("layout = dialog.layout()"), install.index("margins = layout.contentsMargins()"))

    def test_v14802_real_runtime_test_module_exercises_modal_exec_and_button_clicks(self):
        root = Path(__file__).resolve().parents[1]
        runtime_test = (root / "tests" / "test_ui_runtime_interactions.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")', runtime_test)
        self.assertIn("QApplication.activeModalWidget()", runtime_test)
        self.assertIn("target.click()", runtime_test)
        self.assertIn("compact_message_box(", runtime_test)
        self.assertIn("QMessageBox.Icon.Information", runtime_test)
        self.assertIn("QMessageBox.Icon.Warning", runtime_test)
        self.assertIn("QMessageBox.Icon.Critical", runtime_test)
        self.assertIn("QMessageBox.Icon.Question", runtime_test)
        self.assertIn("Question One", runtime_test)
        self.assertIn("Question Two", runtime_test)
