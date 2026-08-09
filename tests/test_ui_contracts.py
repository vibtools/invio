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
            '["Description", "Quantity", "Unit amount", "Tax %"]',
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

    def test_invoice_template_wrapped_notes_have_height_for_width_and_separate_rows(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ui" / "dialogs.py").read_text(encoding="utf-8")
        self.assertIn("def _invoice_wrapped_label", source)
        self.assertIn("QSizePolicy.Policy.Minimum", source)
        self.assertIn("policy.setHeightForWidth(True)", source)
        self.assertIn("def _invoice_form_group", source)
        self.assertIn('_invoice_form_group("Currency", self.currency)', source)
        self.assertIn('_invoice_form_group("Days until due", self.days_due)', source)
        self.assertIn('"Displayed in uppercase; provider API formatting is handled automatically."', source)
        self.assertIn('_invoice_form_group("Invoice type", self.invoice_type)', source)
        self.assertIn('"BOS is used only by providers that support it."', source)
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
        self.assertIn("def supports_api_test(provider_id: str)", runtime)
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
        self.assertIn('"Last API Test"', page)
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
        self.assertIn('["#", "Email", "Name", "Country"]', page)
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
            "self.state.add_customers(list_id, imported.records, source_rows=imported.record_rows)",
            window,
        )

    def test_p04_verification_restores_out_of_scope_dashboard_label(self):
        root = Path(__file__).resolve().parents[1]
        dashboard = (root / "src" / "ui" / "pages" / "dashboard_page.py").read_text(encoding="utf-8")
        self.assertIn('("customers", "Customer Emails")', dashboard)
        self.assertNotIn('("customers", "Customers")', dashboard)

if __name__ == "__main__":
    unittest.main()
