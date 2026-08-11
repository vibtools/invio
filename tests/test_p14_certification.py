from __future__ import annotations

import csv
import tempfile
import threading
import unittest
import subprocess
import sys
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.core.paths import application_root, required_runtime_resources, validate_runtime_resources
from src.core.provider_runtime import ProviderRuntime
from src.core.state import AppState
from src.customers.importers import import_customers


class _Context:
    def __init__(self, task):
        self.task = task
        self.pause_gate = threading.Event()
        self.pause_gate.set()
        self.stop_flag = threading.Event()
        self.progress_events: list[tuple[int, int, int, str]] = []
        self.logs: list[str] = []

    def progress(self, processed: int, success: int, failed: int, message: str) -> None:
        self.progress_events.append((processed, success, failed, message))

    def log(self, message: str) -> None:
        self.logs.append(message)


class P14CertificationTests(unittest.TestCase):
    def test_runtime_resource_root_contains_exact_required_packaged_assets(self):
        root = application_root()
        self.assertTrue((root / "src").is_dir())
        validate_runtime_resources()
        required = required_runtime_resources()
        self.assertEqual(len(required), 20)
        self.assertTrue(all(path.is_file() for path in required))

    def test_setuptools_inventory_covers_existing_settings_and_runtime_resources(self):
        import tomllib

        config = tomllib.loads((application_root() / "pyproject.toml").read_text(encoding="utf-8"))
        packages = set(config["tool"]["setuptools"]["packages"])
        for package in (
            "src.core.settings",
            "providers",
            "providers.packages",
            "providers.packages.stripe",
            "providers.packages.refrens",
            "providers.packages.agiled",
            "assets",
            "assets.icons",
        ):
            self.assertIn(package, packages)
        package_data = config["tool"]["setuptools"]["package-data"]
        self.assertEqual(
            package_data["assets.icons"],
            ["checkmark.svg", "search.svg", "chevron-*.svg", "app.png", "app.ico", "providers/*.png", "nav/*.svg", "window/*.svg"],
        )
        for provider in ("stripe", "refrens", "agiled"):
            self.assertEqual(package_data[f"providers.packages.{provider}"], ["provider.json"])

    def test_large_10000_recipient_import_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "customers.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["email", "name", "country"])
                for index in range(10_000):
                    writer.writerow([f"user{index}@example.com", f"User {index}", "US"])
            result = import_customers(path)
        self.assertTrue(result.structured)
        self.assertEqual(len(result.records), 10_000)
        self.assertEqual(result.issues, [])
        self.assertEqual(result.duplicates_skipped, 0)

    def _stripe_state(self, count: int):
        state = AppState()
        account = state.add_account(
            "stripe", "Stripe", "P14", "Test", {"secret_key": "sk_test_p14contract"}, status="Verified"
        )
        customer_list = state.create_customer_list("P14 Soak")
        state.add_emails(customer_list.id, [f"soak{index}@example.com" for index in range(count)])
        template = state.save_invoice_template(
            template_id=None,
            name="P14 Soak",
            currency="usd",
            days_until_due=30,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=False,
            invoice_title="Invoice",
            invoice_subtitle="",
            customer_note="",
            terms=[],
            items=[("Service", "1", "1.00", "0")],
        )
        task = state.create_task("stripe", "Stripe", [account.id], customer_list.id, template.id)
        return state, task

    def test_1000_recipient_injected_transport_execution_soak(self):
        calls = 0

        def transport(method, url, headers, body, timeout):
            nonlocal calls
            calls += 1
            path = urlparse(url).path
            form = parse_qs((body or b"").decode("utf-8"))
            if method == "POST" and path.endswith("/customers"):
                email = form["email"][0]
                return {"id": "cus_" + email.split("@", 1)[0]}
            if method == "POST" and path.endswith("/invoices"):
                return {"id": f"in_{calls}"}
            if method == "POST" and path.endswith("/invoiceitems"):
                return {"id": f"ii_{calls}"}
            if method == "POST" and path.endswith("/finalize"):
                return {"id": path.split("/")[-2]}
            if method == "POST" and path.endswith("/send"):
                return {"id": path.split("/")[-2], "status": "open"}
            raise AssertionError(f"Unexpected request {method} {url}")

        state, task = self._stripe_state(1_000)
        runtime = ProviderRuntime(transport=transport)
        runtime._wait_for_provider_health = lambda *_args, **_kwargs: True  # type: ignore[method-assign]
        runtime._await_account_rate_slot = lambda *_args, **_kwargs: True  # type: ignore[method-assign]
        context = _Context(task)
        runtime.make_task_runner(task, state)(context)
        self.assertEqual(context.progress_events[-1][:3], (1_000, 1_000, 0))
        self.assertEqual(calls, 5_000)


    def test_subprocess_crash_after_write_ahead_recovers_mutation_as_uncertain(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "domain.sqlite3"
            child = r"""
import os, sys
from pathlib import Path
from src.core.storage import DomainStore, CredentialStore
from src.core.state import AppState
class K:
    def __init__(self): self.values = {}
    def set_password(self, s, u, p): self.values[(s, u)] = p
    def get_password(self, s, u): return self.values.get((s, u))
    def delete_password(self, s, u): self.values.pop((s, u), None)
store = DomainStore(Path(sys.argv[1]))
creds = CredentialStore(K())
state = AppState(domain_store=store, credential_store=creds, loaded=store.load(creds))
account = state.add_account("stripe", "Stripe", "Crash A", "Test", {"secret_key": "sk_test_p14crash"}, status="Verified")
customers = state.create_customer_list("Crash Customers")
state.add_emails(customers.id, ["crash@example.com"])
template = state.save_invoice_template(template_id=None, name="Crash Template", currency="USD", days_until_due=30, memo="", footer="", automatic_tax=False, reuse_customer=False, items=[("Service", "1", "1", "0")])
task = state.create_task("stripe", "Stripe", [account.id], customers.id, template.id)
run = store.begin_delivery_run(task, execution_mode="First Run", recipients=("crash@example.com",))
store.begin_delivery_operation(run_id=run.run_id, recipient_ordinal=0, attempt_number=1, stage="invoice_send", account_id=account.id, account_name=account.name, idempotency_key="p14-crash-key")
os._exit(17)
"""
            completed = subprocess.run([sys.executable, "-c", child, str(db_path)], cwd=application_root())
            self.assertEqual(completed.returncode, 17)
            from src.core.storage import CredentialStore, DomainStore

            class EmptyKeyring:
                def set_password(self, *_args): pass
                def get_password(self, *_args): return None
                def delete_password(self, *_args): pass

            DomainStore(db_path).load(CredentialStore(EmptyKeyring()))
            with closing(sqlite3.connect(db_path)) as connection:
                run_status = connection.execute("SELECT status FROM task_delivery_runs").fetchone()[0]
                operation_status = connection.execute("SELECT status FROM task_delivery_operations").fetchone()[0]
                recipient_result = connection.execute("SELECT final_result FROM task_delivery_recipients").fetchone()[0]
            self.assertEqual(run_status, "Interrupted")
            self.assertEqual(operation_status, "Uncertain")
            self.assertEqual(recipient_result, "Uncertain")



if __name__ == "__main__":
    unittest.main()
