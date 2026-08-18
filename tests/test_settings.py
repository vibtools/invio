from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.core.settings import (
    START_PAGE_LAST,
    AppSettings,
    SettingsError,
    SettingsManager,
    WindowState,
)


class SettingsManagerTests(unittest.TestCase):
    def test_defaults_preserve_v1001_baseline_behavior(self):
        settings = SettingsManager.defaults()
        self.assertEqual(settings.start_page, "Accounts")
        self.assertFalse(settings.remember_window)
        self.assertTrue(settings.confirm_exit_active_tasks)
        self.assertTrue(settings.confirm_close_task)
        self.assertTrue(settings.confirm_delete_template)
        self.assertTrue(settings.confirm_delete_customer_list)
        self.assertFalse(settings.confirm_clear_logs)
        self.assertTrue(settings.show_log_timestamps)
        self.assertTrue(settings.auto_scroll_logs)
        self.assertEqual(settings.max_log_entries, 0)
        self.assertEqual(settings.default_file_folder, "")
        self.assertFalse(settings.remember_last_folder)
        self.assertEqual(settings.default_customer_name, "")
        self.assertEqual(settings.default_customer_country, "")

    def test_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "settings.json"
            manager = SettingsManager(path)
            saved = manager.update(
                AppSettings(
                    start_page="Tasks",
                    remember_window=True,
                    confirm_exit_active_tasks=False,
                    confirm_close_task=False,
                    confirm_delete_template=False,
                    confirm_delete_customer_list=False,
                    confirm_clear_logs=True,
                    show_log_timestamps=False,
                    auto_scroll_logs=False,
                    max_log_entries=2500,
                    default_file_folder=str(root),
                    remember_last_folder=True,
                    default_customer_name="Billing Customer",
                    default_customer_country="bd",
                )
            )
            reloaded = SettingsManager(path).settings
            self.assertEqual(reloaded, saved)
            self.assertEqual(reloaded.default_file_folder, str(root.resolve()))
            self.assertEqual(reloaded.default_customer_name, "Billing Customer")
            self.assertEqual(reloaded.default_customer_country, "BD")

    def test_last_page_is_used_only_when_selected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            manager = SettingsManager(path)
            manager.update(AppSettings(start_page=START_PAGE_LAST))
            manager.record_last_page("Providers")
            self.assertEqual(SettingsManager(path).startup_page(), "Providers")

            manager.update(AppSettings(start_page="Accounts"))
            manager.record_last_page("Tasks")
            self.assertEqual(SettingsManager(path).startup_page(), "Accounts")

    def test_last_folder_and_window_state_follow_opt_in_settings(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "settings.json"
            manager = SettingsManager(path)
            manager.record_last_folder(root)
            manager.record_window_state(WindowState(10, 20, 1200, 800))
            self.assertEqual(manager.dialog_directory(), "")
            self.assertIsNone(manager.window_state())

            manager.update(AppSettings(remember_last_folder=True, remember_window=True))
            manager.record_last_folder(root)
            manager.record_window_state(WindowState(10, 20, 1200, 800))
            reloaded = SettingsManager(path)
            self.assertEqual(reloaded.dialog_directory(), str(root.resolve()))
            self.assertEqual(reloaded.window_state(), WindowState(10, 20, 1200, 800))

    def test_invalid_file_falls_back_without_crashing(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            path.write_text("{broken", encoding="utf-8")
            manager = SettingsManager(path)
            self.assertEqual(manager.settings, AppSettings())
            self.assertTrue(manager.load_warning)

    def test_invalid_default_folder_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            manager = SettingsManager(Path(td) / "settings.json")
            with self.assertRaises(SettingsError):
                manager.update(AppSettings(default_file_folder=str(Path(td) / "missing")))


    def test_invalid_default_customer_country_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            manager = SettingsManager(Path(td) / "settings.json")
            with self.assertRaisesRegex(SettingsError, "two-letter country code"):
                manager.update(AppSettings(default_customer_country="United States"))

    def test_persisted_payload_contains_preferences_not_credentials(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            manager = SettingsManager(path)
            manager.update(AppSettings())
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(raw), {"schema_version", "settings", "runtime"})
            corpus = json.dumps(raw).lower()
            self.assertNotIn("secret_key", corpus)
            self.assertNotIn("app_secret", corpus)
            self.assertNotIn("credentials", corpus)


class Phase3SendingSettingsTests(unittest.TestCase):
    def test_phase3_defaults_preserve_existing_runtime_behavior(self):
        settings = SettingsManager.defaults()
        self.assertEqual(settings.network_timeout_seconds, 30.0)
        self.assertEqual(settings.max_automatic_attempts, 3)
        self.assertEqual(settings.additional_recipient_delay_seconds, 0.0)
        self.assertEqual(settings.provider_rate_overrides, {})

    def test_phase3_sending_controls_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "settings.json"
            manager = SettingsManager(path)
            saved = manager.update(AppSettings(
                network_timeout_seconds=45,
                max_automatic_attempts=2,
                additional_recipient_delay_seconds=1.5,
                provider_rate_overrides={"stripe": 10.0, "refrens": 0.5},
            ))
            loaded = SettingsManager(path).settings
            self.assertEqual(loaded, saved)
            self.assertEqual(loaded.provider_rate_overrides, {"stripe": 10.0, "refrens": 0.5})

    def test_phase3_sending_control_bounds_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            manager = SettingsManager(Path(td) / "settings.json")
            invalid = (
                AppSettings(network_timeout_seconds=9),
                AppSettings(network_timeout_seconds=121),
                AppSettings(max_automatic_attempts=0),
                AppSettings(max_automatic_attempts=4),
                AppSettings(additional_recipient_delay_seconds=-0.1),
                AppSettings(additional_recipient_delay_seconds=60.1),
                AppSettings(provider_rate_overrides={"stripe": 0}),
            )
            for candidate in invalid:
                with self.subTest(candidate=candidate):
                    with self.assertRaises(SettingsError):
                        manager.update(candidate)


if __name__ == "__main__":
    unittest.main()
