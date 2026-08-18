from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from src.core.provider_manager import ProviderManager, ProviderManifestError
from src.core.provider_runtime import (
    ADAPTER_STATUS_EXECUTABLE,
    ADAPTER_STATUS_INCOMPATIBLE,
    ADAPTER_STATUS_MANIFEST_ONLY,
    ADAPTER_STATUS_MISSING,
    EXTERNAL_ADAPTER_INTERFACE_VERSION,
    ExternalAdapterError,
    ExternalAdapterRegistry,
    ProviderRuntime,
    ProviderRuntimeError,
    preflight_candidate,
)
from src.core.state import AppState
from src.core.storage import CredentialStore, DomainStore
from src.customers.models import CustomerRecord
from src.tasks.delivery_ledger import DELIVERY_OPERATION_SUCCEEDED, DELIVERY_OPERATION_UNCERTAIN

ROOT = Path(__file__).resolve().parents[1]


class _Keyring:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def set_password(self, service_name: str, username: str, password: str) -> None:
        self.values[(service_name, username)] = password

    def get_password(self, service_name: str, username: str) -> str | None:
        return self.values.get((service_name, username))

    def delete_password(self, service_name: str, username: str) -> None:
        self.values.pop((service_name, username), None)


class _Context:
    def __init__(self, task) -> None:
        self.task = task
        self.pause_gate = threading.Event()
        self.pause_gate.set()
        self.stop_flag = threading.Event()
        self.logs: list[str] = []
        self.progress_events: list[tuple[int, int, int, str]] = []

    def log(self, message: str) -> None:
        self.logs.append(message)

    def progress(self, processed: int, success: int, failed: int, message: str) -> None:
        self.progress_events.append((processed, success, failed, message))


class P13ExternalAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "providers" / "packages").mkdir(parents=True)
        (self.root / "providers" / "registry").mkdir(parents=True)
        self.store = DomainStore(self.root / "domain.sqlite3")
        self.credentials = CredentialStore(_Keyring())

    def _manifest_payload(self, *, runtime: bool = True, interface_version: int = 1) -> dict:
        payload = {
            "id": "external_demo",
            "name": "External Demo",
            "version": "2.0.0",
            "description": "P13 test provider",
            "credential_fields": [
                {"key": "token", "label": "Token", "kind": "password", "required": True}
            ],
            "account_modes": ["Default"],
            "capabilities": ["invoice", "send_invoice", "api_test"],
        }
        if runtime:
            payload["runtime_adapter"] = {
                "interface_version": interface_version,
                "adapter_version": "1.2.3",
                "entrypoint": "create_adapter",
            }
        return payload

    def _adapter_source(self, *, provider_id: str = "external_demo", adapter_version: str = "1.2.3", mutate_sys_path: bool = False, capabilities: str = 'frozenset({"invoice", "send_invoice", "api_test"})') -> str:
        sys_path_line = 'import sys; sys.path.append("P13_FORBIDDEN_PATH")' if mutate_sys_path else ''
        return f'''from src.core.provider_runtime import (\n    ExternalRecipientResult, NON_IDEMPOTENT_MUTATION, SAFE_READ,\n    ProviderCapabilityProfile, ProviderRuntimeError\n)\n{sys_path_line}\n\nclass Adapter:\n    interface_version = 1\n    provider_id = {provider_id!r}\n    adapter_version = {adapter_version!r}\n    scheduling_policy = None\n    profile = ProviderCapabilityProfile(\n        provider_id={provider_id!r},\n        executable_capabilities={capabilities},\n        task_execution_enabled=True,\n        task_unavailable_message="",\n        invoice_types=frozenset({{"INVOICE"}}),\n        currencies=None,\n        supports_automatic_tax=False,\n        supports_line_tax=False,\n        supports_customer_reuse=False,\n        supports_memo=True,\n        supports_footer=True,\n        supports_customer_note=True,\n        supports_terms=True,\n        required_customer_fields=("email",),\n    )\n\n    def test_account(self, context):\n        context.request(\n            stage="health", operation_kind=SAFE_READ, method="GET",\n            url="https://external.invalid/health", headers={{"Authorization": "Bearer " + context.credentials["token"]}},\n        )\n        return "External API connection verified."\n\n    def validate_task(self, context):\n        return ()\n\n    def execute_recipient(self, context):\n        result = context.request(\n            stage="invoice_send", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST",\n            url="https://external.invalid/invoices",\n            json_data={{"email": context.customer.email}}, provider_reference_key="id",\n        )\n        return ExternalRecipientResult(provider_invoice_id=result["id"], final_stage="external_mutation:invoice_send")\n\ndef create_adapter():\n    return Adapter()\n'''

    def _bundle(self, *, runtime: bool = True, adapter_source: str | None = None, interface_version: int = 1) -> Path:
        bundle = self.root / "bundle"
        bundle.mkdir(exist_ok=True)
        manifest = bundle / "provider.json"
        manifest.write_text(json.dumps(self._manifest_payload(runtime=runtime, interface_version=interface_version)), encoding="utf-8")
        if runtime:
            (bundle / "adapter.py").write_text(adapter_source or self._adapter_source(), encoding="utf-8")
        return manifest

    def _install_executable(self) -> tuple[ProviderManager, ProviderRuntime]:
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(project_root=self.root, domain_store=self.store, transport=lambda *args: self._transport(*args))
        manifest = self._bundle()
        manager.load_external(
            manifest,
            allow_executable=True,
            adapter_validator=runtime.validate_external_adapter,
        )
        runtime.reload_external_adapters()
        return manager, runtime

    @staticmethod
    def _transport(method, url, headers, body, timeout):
        del headers, body, timeout
        if method == "GET" and url.endswith("/health"):
            return {"ok": True}
        if method == "POST" and url.endswith("/invoices"):
            return {"id": "ext_inv_1"}
        raise AssertionError((method, url))

    def _state_task(self, emails: tuple[str, ...] = ("a@example.com",)):
        state = AppState(
            domain_store=self.store,
            credential_store=self.credentials,
            loaded=self.store.load(self.credentials),
        )
        account = state.add_account(
            "external_demo", "External Demo", "External A", "Default", {"token": "P13_SECRET"},
            status="Verified", last_verification_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        customers = state.create_customer_list("External Customers")
        state.add_customers(customers.id, [CustomerRecord(email) for email in emails])
        template = state.save_invoice_template(
            template_id=None, name="External Template", currency="USD", days_until_due=7,
            memo="", footer="", automatic_tax=False, reuse_customer=False,
            items=[("Service", "1", "10", "0")],
        )
        task = state.create_task(
            "external_demo", "External Demo", [account.id], customers.id, template.id,
        )
        return state, task, account, template, customers

    def test_interface_version_is_explicit(self):
        self.assertEqual(EXTERNAL_ADAPTER_INTERFACE_VERSION, 1)

    def test_manifest_only_provider_remains_installed_but_non_executable(self):
        manager = ProviderManager(self.root)
        provider = manager.load_external(self._bundle(runtime=False))
        self.assertIsNone(provider.runtime_adapter)
        runtime = ProviderRuntime(project_root=self.root)
        self.assertEqual(runtime.external_adapter_status(provider.id)[0], ADAPTER_STATUS_MANIFEST_ONLY)
        self.assertEqual(runtime.runtime_capabilities(provider.id), ())
        self.assertFalse(runtime.supports_api_test(provider.id))
        with self.assertRaises(ProviderRuntimeError):
            runtime.test_account(provider.id, {"token": "secret"}, mode="Default")

    def test_executable_bundle_requires_explicit_trust_and_installs_adapter_atomically(self):
        manager = ProviderManager(self.root)
        manifest = self._bundle()
        with self.assertRaisesRegex(ProviderManifestError, "trusted-code approval"):
            manager.load_external(manifest)
        runtime = ProviderRuntime(project_root=self.root)
        provider = manager.load_external(
            manifest, allow_executable=True, adapter_validator=runtime.validate_external_adapter
        )
        self.assertIsNotNone(provider.runtime_adapter)
        self.assertTrue(manager.external_adapter_path(provider.id).is_file())
        runtime.reload_external_adapters()
        self.assertEqual(runtime.external_adapter_status(provider.id)[0], ADAPTER_STATUS_EXECUTABLE)
        self.assertEqual(runtime.runtime_capabilities(provider.id), ("invoice", "send_invoice", "api_test"))

    def test_missing_and_incompatible_installed_adapters_fail_closed_without_startup_exception(self):
        manager = ProviderManager(self.root)
        manifest_path = self.root / "providers" / "registry" / "external_demo.json"
        manifest_path.write_text(json.dumps(self._manifest_payload()), encoding="utf-8")
        runtime = ProviderRuntime(project_root=self.root)
        self.assertEqual(runtime.external_adapter_status("external_demo")[0], ADAPTER_STATUS_MISSING)
        manager.external_adapter_path("external_demo").write_text("raise RuntimeError('broken adapter')\n", encoding="utf-8")
        runtime.reload_external_adapters()
        status, message = runtime.external_adapter_status("external_demo")
        self.assertEqual(status, ADAPTER_STATUS_INCOMPATIBLE)
        self.assertIn("import failed", message)
        self.assertFalse(runtime.supports_api_test("external_demo"))

    def test_version_provider_and_capability_mismatch_fail_closed(self):
        manager = ProviderManager(self.root)
        manifest = manager.inspect_manifest(self._bundle())
        with self.assertRaisesRegex(ExternalAdapterError, "provider_id"):
            ExternalAdapterRegistry.validate_adapter(
                manifest, self._bundle(adapter_source=self._adapter_source(provider_id="wrong_provider")).with_name("adapter.py")
            )
        with self.assertRaisesRegex(ExternalAdapterError, "version"):
            ExternalAdapterRegistry.validate_adapter(
                manifest, self._bundle(adapter_source=self._adapter_source(adapter_version="9.9.9")).with_name("adapter.py")
            )
        with self.assertRaisesRegex(ExternalAdapterError, "capabilities"):
            ExternalAdapterRegistry.validate_adapter(
                manifest,
                self._bundle(adapter_source=self._adapter_source(capabilities='frozenset({"api_test"})')).with_name("adapter.py"),
            )

    def test_wrong_interface_and_sys_path_mutation_are_rejected_and_restored(self):
        manager = ProviderManager(self.root)
        manifest = manager.inspect_manifest(self._bundle(interface_version=2))
        with self.assertRaisesRegex(ExternalAdapterError, "interface version"):
            ExternalAdapterRegistry.validate_adapter(manifest, self.root / "bundle" / "adapter.py")
        manifest = manager.inspect_manifest(self._bundle(adapter_source=self._adapter_source(mutate_sys_path=True)))
        before = list(sys.path)
        with self.assertRaisesRegex(ExternalAdapterError, "modified sys.path"):
            ExternalAdapterRegistry.validate_adapter(manifest, self.root / "bundle" / "adapter.py")
        self.assertEqual(sys.path, before)
        self.assertNotIn("P13_FORBIDDEN_PATH", sys.path)

    def test_packaged_provider_id_collision_is_rejected(self):
        stripe_package = self.root / "providers" / "packages" / "stripe"
        stripe_package.mkdir(parents=True)
        source = ROOT / "providers" / "packages" / "stripe" / "provider.json"
        stripe_package.joinpath("provider.json").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        payload = self._manifest_payload()
        payload["id"] = "stripe"
        payload["name"] = "Fake Stripe"
        manifest = self.root / "bundle" / "provider.json"
        manifest.parent.mkdir(exist_ok=True)
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        (manifest.parent / "adapter.py").write_text(self._adapter_source(provider_id="stripe"), encoding="utf-8")
        with self.assertRaisesRegex(ProviderManifestError, "reserved"):
            ProviderManager(self.root).load_external(manifest, allow_executable=True, adapter_validator=lambda *_: None)

    def test_external_api_test_uses_validated_runtime_and_safe_read_retry(self):
        manager, runtime = self._install_executable()
        self.assertEqual(manager.get_installed("external_demo").id, "external_demo")
        calls = {"count": 0}
        def transport(method, url, headers, body, timeout):
            del headers, body, timeout
            calls["count"] += 1
            if calls["count"] < 3:
                raise ProviderRuntimeError("temporary", category="network", retryable=True)
            return {"ok": True}
        runtime._transport = transport
        with patch("src.core.provider_runtime.runtime.time.sleep", return_value=None):
            message = runtime.test_account("external_demo", {"token": "secret"}, mode="Default")
        self.assertEqual(message, "External API connection verified.")
        self.assertEqual(calls["count"], 3)

    def test_external_profile_participates_in_p06_preflight(self):
        manager, runtime = self._install_executable()
        state, _task, account, template, customers = self._state_task()
        installed = manager.get_installed("external_demo")
        result = preflight_candidate(
            provider_id="external_demo",
            installed_manifest=installed,
            packaged_manifest=None,
            accounts=[account],
            template=template,
            customers=customers.customers,
            runtime_profile=runtime.capability_profile("external_demo"),
            additional_issues=runtime.external_task_validation_issues(
                "external_demo", template, customers.customers
            ),
        )
        self.assertTrue(result.passed, result.message)
        del state

    def test_external_task_uses_p10_write_ahead_and_persists_provider_reference(self):
        _manager, runtime = self._install_executable()
        state, task, _account, _template, _customers = self._state_task()
        context = _Context(task)
        runtime.make_task_runner(task, state)(context)
        with closing(sqlite3.connect(self.store.path)) as connection:
            operations = connection.execute(
                "SELECT stage, status, provider_reference FROM task_delivery_operations ORDER BY rowid"
            ).fetchall()
            recipient = connection.execute(
                "SELECT provider_invoice_id, final_result FROM task_delivery_recipients ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(operations, [("external_mutation:invoice_send", DELIVERY_OPERATION_SUCCEEDED, "ext_inv_1")])
        self.assertEqual(recipient, ("ext_inv_1", "Succeeded"))
        self.assertEqual(context.progress_events[-1][:3], (1, 1, 0))

    def test_idempotent_external_mutation_retries_only_with_stable_provider_key(self):
        source = '''from src.core.provider_runtime import (
    ExternalRecipientResult, IDEMPOTENT_MUTATION, SAFE_READ, ProviderCapabilityProfile
)
class Adapter:
    interface_version = 1
    provider_id = "external_demo"
    adapter_version = "1.2.3"
    scheduling_policy = None
    profile = ProviderCapabilityProfile(
        provider_id="external_demo",
        executable_capabilities=frozenset({"invoice", "send_invoice", "api_test"}),
        task_execution_enabled=True, task_unavailable_message="",
        invoice_types=frozenset({"INVOICE"}), currencies=None,
        supports_automatic_tax=False, supports_line_tax=False, supports_customer_reuse=False,
        supports_memo=True, supports_footer=True, supports_customer_note=True, supports_terms=True,
        required_customer_fields=("email",),
    )
    def test_account(self, context):
        context.request(stage="health", operation_kind=SAFE_READ, method="GET", url="https://external.invalid/health")
        return "ok"
    def validate_task(self, context): return ()
    def execute_recipient(self, context):
        key = "ext:" + context.task_id + ":" + context.customer.email
        result = context.request(
            stage="invoice_send", operation_kind=IDEMPOTENT_MUTATION, method="POST",
            url="https://external.invalid/invoices", json_data={"email": context.customer.email},
            idempotency_key=key, provider_reference_key="id",
        )
        return ExternalRecipientResult(provider_invoice_id=result["id"], final_stage="external_mutation:invoice_send")
def create_adapter(): return Adapter()
'''
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(project_root=self.root, domain_store=self.store, retry_jitter_source=lambda: 0.0)
        manager.load_external(
            self._bundle(adapter_source=source), allow_executable=True,
            adapter_validator=runtime.validate_external_adapter,
        )
        runtime.reload_external_adapters()
        state, task, _account, _template, _customers = self._state_task()
        calls = {"count": 0}
        def transport(method, url, headers, body, timeout):
            del headers, body, timeout
            if method == "POST":
                calls["count"] += 1
                if calls["count"] == 1:
                    raise ProviderRuntimeError("temporary", category="network", retryable=True)
                return {"id": "ext_inv_retry"}
            return {"ok": True}
        runtime._transport = transport
        with patch("src.core.provider_runtime.runtime._cooperative_retry_wait", return_value=True):
            runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(calls["count"], 2)
        with closing(sqlite3.connect(self.store.path)) as connection:
            rows = connection.execute(
                "SELECT attempt_number, stage, status, idempotency_key FROM task_delivery_operations ORDER BY rowid"
            ).fetchall()
        self.assertEqual([row[0] for row in rows], [1, 2])
        self.assertEqual({row[1] for row in rows}, {"external_mutation:invoice_send"})
        self.assertEqual([row[2] for row in rows], ["Failed", "Succeeded"])
        self.assertEqual(len({row[3] for row in rows}), 1)
        self.assertTrue(rows[0][3].startswith("ext:"))

    def test_ambiguous_non_idempotent_external_mutation_is_uncertain_and_not_replayed(self):
        _manager, runtime = self._install_executable()
        state, task, _account, _template, _customers = self._state_task()
        calls = {"count": 0}
        def transport(method, url, headers, body, timeout):
            del method, url, headers, body, timeout
            calls["count"] += 1
            raise ProviderRuntimeError("connection lost", category="network", retryable=True)
        runtime._transport = transport
        with self.assertRaisesRegex(ProviderRuntimeError, "uncertain provider outcomes"):
            runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(calls["count"], 1)
        with closing(sqlite3.connect(self.store.path)) as connection:
            operation = connection.execute(
                "SELECT stage, status FROM task_delivery_operations ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
            recipient = connection.execute(
                "SELECT final_result FROM task_delivery_recipients ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(operation, ("external_mutation:invoice_send", DELIVERY_OPERATION_UNCERTAIN))
        self.assertEqual(recipient, ("Uncertain",))
        summary = runtime.delivery_summary(task)
        self.assertEqual(summary.uncertain_recipients, ("a@example.com",))
        task.status = "Stopped"
        with self.assertRaisesRegex(ProviderRuntimeError, "only uncertain provider outcomes"):
            runtime.make_task_runner(task, state, resume_remaining=True)

    def test_external_fatal_batch_signal_halts_before_next_recipient_and_preserves_pending(self):
        original = '''    def execute_recipient(self, context):
        result = context.request(
            stage="invoice_send", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST",
            url="https://external.invalid/invoices",
            json_data={"email": context.customer.email}, provider_reference_key="id",
        )
        return ExternalRecipientResult(provider_invoice_id=result["id"], final_stage="external_mutation:invoice_send")'''
        replacement = '''    def execute_recipient(self, context):
        context.request(
            stage="invoice_send", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST",
            url="https://external.invalid/invoices",
            json_data={"email": context.customer.email}, provider_reference_key="id",
        )
        raise ProviderRuntimeError(
            "provider daily quota reached", category="provider-quota", retryable=False,
            halt_batch=True, halt_code="daily-limit",
            user_message="Provider daily limit reached. No new recipients will be started.",
        )'''
        source = self._adapter_source().replace(original, replacement)
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(
            project_root=self.root, domain_store=self.store,
            transport=lambda *args: self._transport(*args),
        )
        manager.load_external(
            self._bundle(adapter_source=source), allow_executable=True,
            adapter_validator=runtime.validate_external_adapter,
        )
        runtime.reload_external_adapters()
        state, task, _account, _template, _customers = self._state_task(
            ("a@example.com", "b@example.com", "c@example.com")
        )
        context = _Context(task)
        with self.assertRaisesRegex(ProviderRuntimeError, "daily quota reached") as captured:
            runtime.make_task_runner(task, state)(context)
        self.assertTrue(captured.exception.halt_batch)
        self.assertEqual(captured.exception.halt_code, "daily-limit")
        summary = runtime.delivery_summary(task)
        self.assertEqual(summary.uncertain_recipients, ("a@example.com",))
        self.assertEqual(summary.pending_recipients, ("b@example.com", "c@example.com"))
        self.assertEqual(summary.success, 0)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(summary.processed, 0)
        self.assertTrue(context.progress_events)
        self.assertTrue(context.progress_events[-1][3].startswith("Stopped: Provider daily limit reached."))
        self.assertIn("1 uncertain recipient(s); 2 pending", context.progress_events[-1][3])
        with closing(sqlite3.connect(self.store.path)) as connection:
            recipient_rows = connection.execute(
                "SELECT recipient_email, final_result FROM task_delivery_recipients ORDER BY recipient_ordinal"
            ).fetchall()
            operation_count = connection.execute(
                "SELECT COUNT(*) FROM task_delivery_operations"
            ).fetchone()[0]
        self.assertEqual(recipient_rows[0], ("a@example.com", "Uncertain"))
        self.assertEqual(recipient_rows[1:], [("b@example.com", "Pending"), ("c@example.com", "Pending")])
        self.assertEqual(operation_count, 1)

        task.status = "Stopped"
        resume_context = _Context(task)
        with self.assertRaisesRegex(ProviderRuntimeError, "daily quota reached"):
            runtime.make_task_runner(task, state, resume_remaining=True)(resume_context)
        resumed = runtime.delivery_summary(task)
        self.assertEqual(resumed.uncertain_recipients, ("a@example.com", "b@example.com"))
        self.assertEqual(resumed.pending_recipients, ("c@example.com",))
        with closing(sqlite3.connect(self.store.path)) as connection:
            operation_recipients = connection.execute(
                "SELECT recipient_ordinal FROM task_delivery_operations ORDER BY rowid"
            ).fetchall()
        self.assertEqual(operation_recipients, [(0,), (1,)])

    def test_external_nonfatal_recipient_error_still_continues_to_next_recipient(self):
        original = '''    def execute_recipient(self, context):
        result = context.request(
            stage="invoice_send", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST",
            url="https://external.invalid/invoices",
            json_data={"email": context.customer.email}, provider_reference_key="id",
        )
        return ExternalRecipientResult(provider_invoice_id=result["id"], final_stage="external_mutation:invoice_send")'''
        replacement = '''    def execute_recipient(self, context):
        if context.customer.email == "a@example.com":
            raise ProviderRuntimeError("recipient rejected", category="provider-mail", retryable=False)
        result = context.request(
            stage="invoice_send", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST",
            url="https://external.invalid/invoices",
            json_data={"email": context.customer.email}, provider_reference_key="id",
        )
        return ExternalRecipientResult(provider_invoice_id=result["id"], final_stage="external_mutation:invoice_send")'''
        source = self._adapter_source().replace(original, replacement)
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(
            project_root=self.root, domain_store=self.store,
            transport=lambda *args: self._transport(*args),
        )
        manager.load_external(
            self._bundle(adapter_source=source), allow_executable=True,
            adapter_validator=runtime.validate_external_adapter,
        )
        runtime.reload_external_adapters()
        state, task, _account, _template, _customers = self._state_task(("a@example.com", "b@example.com"))
        context = _Context(task)
        with self.assertRaisesRegex(ProviderRuntimeError, r"1 external recipient\(s\) failed"):
            runtime.make_task_runner(task, state)(context)
        summary = runtime.delivery_summary(task)
        self.assertEqual(summary.failed_recipients, ("a@example.com",))
        self.assertEqual(summary.success, 1)
        self.assertEqual(summary.processed, 2)
        self.assertIn("Resolved 2/2 external recipient(s)", context.progress_events[-1][3])

    def test_atomic_install_rolls_back_if_manifest_replace_fails(self):
        manager = ProviderManager(self.root)
        manifest_only = self._bundle(runtime=False)
        manager.load_external(manifest_only)
        original = (self.root / "providers" / "registry" / "external_demo.json").read_bytes()
        executable = self._bundle(runtime=True)
        runtime = ProviderRuntime(project_root=self.root)
        real_replace = os.replace
        calls = {"count": 0}

        def replace_once_then_fail(source, target):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("simulated manifest replace failure")
            return real_replace(source, target)

        with patch("src.core.provider_manager.manager.os.replace", side_effect=replace_once_then_fail):
            with self.assertRaisesRegex(ProviderManifestError, "Could not load external provider"):
                manager.load_external(
                    executable,
                    allow_executable=True,
                    adapter_validator=runtime.validate_external_adapter,
                )
        self.assertEqual((self.root / "providers" / "registry" / "external_demo.json").read_bytes(), original)
        self.assertFalse(manager.external_adapter_path("external_demo").exists())

    def test_manifest_only_replacement_removes_stale_external_adapter_file(self):
        manager, runtime = self._install_executable()
        self.assertTrue(manager.external_adapter_path("external_demo").exists())
        manifest_only = self._bundle(runtime=False)
        manager.load_external(manifest_only)
        self.assertFalse(manager.external_adapter_path("external_demo").exists())
        runtime.reload_external_adapters()
        self.assertEqual(runtime.external_adapter_status("external_demo")[0], ADAPTER_STATUS_MANIFEST_ONLY)

    def test_external_uninstall_rolls_back_manifest_if_adapter_move_fails(self):
        manager, _runtime = self._install_executable()
        manifest_path = manager.registry_dir / "external_demo.json"
        adapter_path = manager.external_adapter_path("external_demo")
        original_manifest = manifest_path.read_bytes()
        original_adapter = adapter_path.read_bytes()
        real_replace = os.replace
        calls = {"count": 0}

        def fail_adapter_move(source, target):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("simulated adapter move failure")
            return real_replace(source, target)

        with patch("src.core.provider_manager.manager.os.replace", side_effect=fail_adapter_move):
            with self.assertRaisesRegex(ProviderManifestError, "Could not uninstall provider"):
                manager.uninstall("external_demo")
        self.assertEqual(manifest_path.read_bytes(), original_manifest)
        self.assertEqual(adapter_path.read_bytes(), original_adapter)
        self.assertIsNotNone(manager.get_installed("external_demo"))

    def test_executable_validation_uses_staged_adapter_bytes(self):
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(project_root=self.root)
        manifest = self._bundle()
        validated_paths: list[Path] = []

        def validator(candidate, adapter_path):
            validated_paths.append(Path(adapter_path))
            runtime.validate_external_adapter(candidate, adapter_path)

        manager.load_external(manifest, allow_executable=True, adapter_validator=validator)
        self.assertEqual(len(validated_paths), 1)
        self.assertEqual(validated_paths[0].parent, manager.registry_dir)
        self.assertNotEqual(validated_paths[0], manifest.with_name("adapter.py"))
        self.assertTrue(validated_paths[0].name.endswith("_adapter.py"))

    def test_staged_adapter_cannot_change_after_validation_before_install(self):
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(project_root=self.root)
        manifest = self._bundle()

        def mutating_validator(candidate, adapter_path):
            runtime.validate_external_adapter(candidate, adapter_path)
            path = Path(adapter_path)
            path.write_text(path.read_text(encoding="utf-8") + "\n# mutated after validation\n", encoding="utf-8")

        with self.assertRaisesRegex(ProviderManifestError, "changed during validation"):
            manager.load_external(
                manifest, allow_executable=True, adapter_validator=mutating_validator
            )
        self.assertIsNone(manager.get_installed("external_demo"))
        self.assertFalse(manager.external_adapter_path("external_demo").exists())

    def test_create_adapter_sys_path_mutation_is_rejected_and_restored(self):
        source = self._adapter_source().replace(
            "def create_adapter():\n    return Adapter()",
            "def create_adapter():\n    import sys\n    sys.path.append('P13_ENTRYPOINT_FORBIDDEN')\n    return Adapter()",
        )
        manifest = ProviderManager(self.root).inspect_manifest(self._bundle(adapter_source=source))
        before = list(sys.path)
        with self.assertRaisesRegex(ExternalAdapterError, "create_adapter"):
            ExternalAdapterRegistry.validate_adapter(manifest, self.root / "bundle" / "adapter.py")
        self.assertEqual(sys.path, before)

    def test_system_exit_during_external_adapter_import_is_contained_at_startup(self):
        manager = ProviderManager(self.root)
        manifest = self._bundle()
        installed_manifest = manager.registry_dir / "external_demo.json"
        installed_manifest.write_bytes(manifest.read_bytes())
        manager.external_adapter_path("external_demo").write_text(
            "raise SystemExit('broken plugin')\n", encoding="utf-8"
        )
        runtime = ProviderRuntime(project_root=self.root)
        status, message = runtime.external_adapter_status("external_demo")
        self.assertEqual(status, ADAPTER_STATUS_INCOMPATIBLE)
        self.assertIn("SystemExit", message)

    def test_system_exit_during_adapter_metadata_validation_is_contained_at_startup(self):
        manager = ProviderManager(self.root)
        manifest = self._bundle()
        installed_manifest = manager.registry_dir / "external_demo.json"
        installed_manifest.write_bytes(manifest.read_bytes())
        manager.external_adapter_path("external_demo").write_text(
            """class Adapter:
    def __getattribute__(self, name):
        if name == 'interface_version':
            raise SystemExit('metadata crash')
        return object.__getattribute__(self, name)
def create_adapter():
    return Adapter()
""",
            encoding="utf-8",
        )
        runtime = ProviderRuntime(project_root=self.root)
        status, message = runtime.external_adapter_status("external_demo")
        self.assertEqual(status, ADAPTER_STATUS_INCOMPATIBLE)
        self.assertIn("metadata validation failed", message)
        self.assertIn("SystemExit", message)

    def test_external_api_test_requires_successful_host_managed_safe_read(self):
        source = self._adapter_source().replace(
            '''        context.request(
            stage="health", operation_kind=SAFE_READ, method="GET",
            url="https://external.invalid/health", headers={"Authorization": "Bearer " + context.credentials["token"]},
        )
        return "External API connection verified."''',
            '''        return "pretend verified"''',
        )
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(project_root=self.root, transport=lambda *args: self._transport(*args))
        manager.load_external(
            self._bundle(adapter_source=source),
            allow_executable=True,
            adapter_validator=runtime.validate_external_adapter,
        )
        runtime.reload_external_adapters()
        with self.assertRaisesRegex(ProviderRuntimeError, "SAFE_READ"):
            runtime.test_account("external_demo", {"token": "secret"}, mode="Default")

    def test_external_validation_and_execution_cannot_mutate_frozen_template_inputs(self):
        source = self._adapter_source().replace(
            "    def validate_task(self, context):\n        return ()",
            "    def validate_task(self, context):\n        context.template.name = 'MUTATED_BY_VALIDATION'\n        return ()",
        ).replace(
            "    def execute_recipient(self, context):\n        result = context.request(",
            "    def execute_recipient(self, context):\n        context.template.name = 'MUTATED_BY_EXECUTION'\n        result = context.request(",
        )
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(
            project_root=self.root,
            domain_store=self.store,
            transport=lambda *args: self._transport(*args),
        )
        manager.load_external(
            self._bundle(adapter_source=source),
            allow_executable=True,
            adapter_validator=runtime.validate_external_adapter,
        )
        runtime.reload_external_adapters()
        state, task, _account, template, _customers = self._state_task()
        original_name = template.name
        issues = runtime.external_task_validation_issues(
            "external_demo", template, list(state.customer_lists[task.customer_list_id].customers)
        )
        self.assertEqual(issues, ())
        self.assertEqual(template.name, original_name)
        runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(template.name, original_name)
        self.assertEqual(task.execution_snapshot.template.name, original_name)

    def test_external_recipient_success_requires_host_managed_mutating_operation(self):
        original = '''    def execute_recipient(self, context):
        result = context.request(
            stage="invoice_send", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST",
            url="https://external.invalid/invoices",
            json_data={"email": context.customer.email}, provider_reference_key="id",
        )
        return ExternalRecipientResult(provider_invoice_id=result["id"], final_stage="external_mutation:invoice_send")'''
        replacement = '''    def execute_recipient(self, context):
        return ExternalRecipientResult(provider_invoice_id="fake", final_stage="external_mutation:invoice_send")'''
        source = self._adapter_source().replace(original, replacement)
        self.assertNotEqual(source, self._adapter_source())
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(
            project_root=self.root,
            domain_store=self.store,
            transport=lambda *args: self._transport(*args),
        )
        manager.load_external(
            self._bundle(adapter_source=source),
            allow_executable=True,
            adapter_validator=runtime.validate_external_adapter,
        )
        runtime.reload_external_adapters()
        state, task, _account, _template, _customers = self._state_task()
        with self.assertRaisesRegex(ProviderRuntimeError, "failed"):
            runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(runtime.delivery_summary(task).failed_recipients, ("a@example.com",))

    def test_external_final_stage_must_match_last_host_managed_mutation(self):
        source = self._adapter_source().replace(
            'final_stage="external_mutation:invoice_send"',
            'final_stage="external_mutation:not_the_last_operation"',
        )
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(
            project_root=self.root,
            domain_store=self.store,
            transport=lambda *args: self._transport(*args),
        )
        manager.load_external(
            self._bundle(adapter_source=source),
            allow_executable=True,
            adapter_validator=runtime.validate_external_adapter,
        )
        runtime.reload_external_adapters()
        state, task, _account, _template, _customers = self._state_task()
        with self.assertRaisesRegex(ProviderRuntimeError, "uncertain provider outcomes"):
            runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(runtime.delivery_summary(task).uncertain_recipients, ("a@example.com",))

    def test_non_idempotent_success_followed_by_adapter_error_is_uncertain(self):
        source = self._adapter_source().replace(
            '        return ExternalRecipientResult(provider_invoice_id=result["id"], final_stage="external_mutation:invoice_send")',
            '        raise RuntimeError("adapter failed after provider accepted mutation")',
        )
        manager = ProviderManager(self.root)
        runtime = ProviderRuntime(
            project_root=self.root,
            domain_store=self.store,
            transport=lambda *args: self._transport(*args),
        )
        manager.load_external(
            self._bundle(adapter_source=source),
            allow_executable=True,
            adapter_validator=runtime.validate_external_adapter,
        )
        runtime.reload_external_adapters()
        state, task, _account, _template, _customers = self._state_task()
        with self.assertRaisesRegex(ProviderRuntimeError, "uncertain provider outcomes"):
            runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(runtime.delivery_summary(task).uncertain_recipients, ("a@example.com",))

    def test_restart_after_external_non_idempotent_success_before_recipient_commit_is_uncertain(self):
        state, task, account, _template, _customers = self._state_task()
        run = self.store.begin_delivery_run(task, execution_mode="First Run", recipients=("a@example.com",))
        self.store.begin_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="external_mutation:invoice_send",
            account_id=account.id,
            account_name=account.name,
            idempotency_key="",
        )
        self.store.finish_delivery_operation(
            run_id=run.run_id,
            recipient_ordinal=0,
            attempt_number=1,
            stage="external_mutation:invoice_send",
            status=DELIVERY_OPERATION_SUCCEEDED,
            provider_reference="ext_inv_crash",
        )
        recovered = self.store.load(self.credentials)
        recovered_task = recovered.tasks[task.id]
        runtime = ProviderRuntime(project_root=self.root, domain_store=self.store)
        summary = runtime.delivery_summary(recovered_task)
        self.assertEqual(summary.uncertain_recipients, ("a@example.com",))
        self.assertFalse(summary.retry_failed_available)


    def test_providers_ui_reports_runtime_adapter_state_and_trusted_code_guards(self):
        providers_page = (ROOT / "src" / "ui" / "pages" / "providers_page.py").read_text(encoding="utf-8")
        window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        tokens = (ROOT / "src" / "ui" / "tokens.py").read_text(encoding="utf-8")
        self.assertIn('self.runtime_adapter_status = runtime_adapter_status', providers_page)
        self.assertIn('self.runtime_capabilities = runtime_capabilities', providers_page)
        self.assertNotIn('f"Runtime:', providers_page)
        self.assertNotIn('"ProviderMeta"', providers_page)
        self.assertIn("is not sandboxed. Load only code you trust.", window)
        self.assertIn("Close all Tasks that reference external provider", window)
        self.assertIn("before loading, replacing,", window)
        self.assertIn("or removing its executable adapter contract", window)
        self.assertIn("before uninstalling it", window)
        self.assertNotIn('("External Providers",', tokens)



class Phase3ExternalSchedulingPolicyTests(P13ExternalAdapterTests):
    def test_external_scheduling_policy_requires_finite_positive_rate_and_ordered_cooldowns(self):
        source = self._adapter_source().replace(
            "ProviderCapabilityProfile, ProviderRuntimeError",
            "ProviderCapabilityProfile, ProviderRuntimeError, ProviderSchedulingPolicy",
        ).replace(
            "scheduling_policy = None",
            "scheduling_policy = ProviderSchedulingPolicy(float('inf'), 1, 5.0, 60.0, 5.0, 60.0)",
        )
        bundle = self._bundle(adapter_source=source)
        manifest = ProviderManager(self.root).inspect_manifest(bundle)
        with self.assertRaisesRegex(ExternalAdapterError, "requests_per_second_per_account"):
            ExternalAdapterRegistry.validate_adapter(manifest, bundle.parent / "adapter.py")

        source = self._adapter_source().replace(
            "ProviderCapabilityProfile, ProviderRuntimeError",
            "ProviderCapabilityProfile, ProviderRuntimeError, ProviderSchedulingPolicy",
        ).replace(
            "scheduling_policy = None",
            "scheduling_policy = ProviderSchedulingPolicy(2.0, 1, 10.0, 5.0, 5.0, 60.0)",
        )
        bundle = self._bundle(adapter_source=source)
        manifest = ProviderManager(self.root).inspect_manifest(bundle)
        with self.assertRaisesRegex(ExternalAdapterError, "account cooldown cap"):
            ExternalAdapterRegistry.validate_adapter(manifest, bundle.parent / "adapter.py")


if __name__ == "__main__":
    unittest.main()
