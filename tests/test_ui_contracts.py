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


    def test_dark_popup_list_and_table_surfaces_are_explicitly_styled(self):
        root = Path(__file__).resolve().parents[1]
        style_source = (root / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
        app_source = (root / "src" / "app.py").read_text(encoding="utf-8")
        self.assertIn("QListWidget {", style_source)
        self.assertIn("QMenu {", style_source)
        self.assertIn("QMenu::item:selected", style_source)
        self.assertIn("selection-color: {c['primary_text']}", style_source)
        self.assertIn("app.setStyleSheet(app_qss())", app_source)

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
        self.assertIn("Declared capabilities:", source)
        self.assertIn("Runtime capabilities:", source)
        self.assertIn("runtime_capabilities", source)

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
