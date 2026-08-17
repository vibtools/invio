from __future__ import annotations

import ssl
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from http.client import IncompleteRead
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

from src.core.provider_runtime import ProviderRuntime, ProviderRuntimeError
from src.core.provider_runtime.runtime import (
    DEFAULT_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_READ_TIMEOUT_SECONDS,
    MAX_TOTAL_ATTEMPTS,
    _cooperative_retry_wait,
    _parse_retry_after,
    _stdlib_transport,
    _verified_urlopen,
    _windows_native_tls_context,
)
from src.core.state import AppState


class _Context:
    def __init__(self, task):
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


class P08ReliabilityTests(unittest.TestCase):
    def _stripe_state(self, emails=None):
        state = AppState()
        account = state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_contractkey"}, status="Verified"
        )
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, emails or ["a@example.com"])
        template = state.save_invoice_template(
            template_id=None,
            name="Monthly",
            currency="usd",
            days_until_due=30,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            invoice_title="Invoice",
            invoice_subtitle="",
            customer_note="",
            terms=[],
            items=[("Service", "1", "10.00", "0")],
        )
        task = state.create_task("stripe", "Stripe", [account.id], customer_list.id, template.id)
        return state, task

    def _successful_transport_with_send_hook(self, hook):
        invoice_counter = {"value": 0}
        def transport(method, url, headers, body, timeout):
            path = urlparse(url).path
            form = parse_qs((body or b"").decode())
            if method == "GET" and path.endswith("/customers"):
                return {"data": []}
            if method == "POST" and path.endswith("/customers"):
                return {"id": "cus_1"}
            if method == "POST" and path.endswith("/invoices"):
                invoice_counter["value"] += 1
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/invoiceitems"):
                return {"id": "ii_1"}
            if method == "POST" and path.endswith("/finalize"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/send"):
                return hook(headers, form)
            raise AssertionError((method, url))
        return transport

    def test_default_connect_and_read_policy_is_explicitly_thirty_seconds(self):
        self.assertEqual(DEFAULT_CONNECT_TIMEOUT_SECONDS, 30.0)
        self.assertEqual(DEFAULT_READ_TIMEOUT_SECONDS, 30.0)
        runtime = ProviderRuntime()
        self.assertEqual(runtime.connect_timeout, 30.0)
        self.assertEqual(runtime.read_timeout, 30.0)
        self.assertEqual(runtime.timeout, 30.0)

    def test_retry_after_parses_seconds_and_http_date(self):
        self.assertEqual(_parse_retry_after("5"), 5.0)
        future = datetime.now(timezone.utc) + timedelta(seconds=3)
        parsed = _parse_retry_after(format_datetime(future, usegmt=True))
        self.assertIsNotNone(parsed)
        self.assertGreaterEqual(parsed, 1.0)
        self.assertLessEqual(parsed, 3.5)

    def test_transport_classifies_429_and_5xx_as_retryable_and_4xx_as_permanent(self):
        for status, expected in ((429, True), (500, True), (502, True), (503, True), (504, True), (400, False), (401, False), (403, False), (404, False), (409, False), (422, False)):
            headers = {"Retry-After": "0"} if status == 429 else {}
            error = HTTPError("https://api.example.test", status, "error", headers, None)
            error.read = lambda: b'{"error":{"message":"failure"}}'  # type: ignore[method-assign]
            with patch("src.core.provider_runtime.runtime.urlopen", side_effect=error):
                with self.assertRaises(ProviderRuntimeError) as raised:
                    _stdlib_transport("GET", "https://api.example.test", {}, None, 30.0)
            self.assertEqual(raised.exception.http_status, status)
            self.assertEqual(raised.exception.retryable, expected)
            if status == 429:
                self.assertEqual(raised.exception.retry_after_seconds, 0.0)

    def test_transport_classifies_timeout_and_transient_disconnect_as_retryable(self):
        for exc in (TimeoutError("timed out"), URLError(ConnectionResetError("reset"))):
            with patch("src.core.provider_runtime.runtime.urlopen", side_effect=exc):
                with self.assertRaises(ProviderRuntimeError) as raised:
                    _stdlib_transport("GET", "https://api.example.test", {}, None, 30.0)
            self.assertTrue(raised.exception.retryable)

    def test_transport_classifies_incomplete_response_body_as_retryable_disconnect(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                raise IncompleteRead(b'{"partial":', 4)

        with patch("src.core.provider_runtime.runtime.urlopen", return_value=Response()):
            with self.assertRaises(ProviderRuntimeError) as raised:
                _stdlib_transport("GET", "https://api.example.test", {}, None, 30.0)
        self.assertEqual(raised.exception.category, "network")
        self.assertTrue(raised.exception.retryable)

    def test_http_error_with_incomplete_body_keeps_status_classification_and_retry_after(self):
        error = HTTPError(
            "https://api.example.test",
            503,
            "service unavailable",
            {"Retry-After": "2"},
            None,
        )
        error.read = lambda: (_ for _ in ()).throw(IncompleteRead(b'{"error":', 10))  # type: ignore[method-assign]
        with patch("src.core.provider_runtime.runtime.urlopen", side_effect=error):
            with self.assertRaises(ProviderRuntimeError) as raised:
                _stdlib_transport("GET", "https://api.example.test", {}, None, 30.0)
        self.assertEqual(raised.exception.http_status, 503)
        self.assertTrue(raised.exception.retryable)
        self.assertEqual(raised.exception.retry_after_seconds, 2.0)

    def test_tls_eof_disconnect_is_retryable_but_certificate_failure_remains_permanent(self):
        import ssl

        for reason in (ssl.SSLEOFError(8, "EOF occurred in violation of protocol"), ssl.SSLZeroReturnError(6, "TLS closed")):
            with patch("src.core.provider_runtime.runtime.urlopen", side_effect=URLError(reason)):
                with self.assertRaises(ProviderRuntimeError) as raised:
                    _stdlib_transport("GET", "https://api.example.test", {}, None, 30.0)
            self.assertEqual(raised.exception.category, "network")
            self.assertTrue(raised.exception.retryable)

        failure = URLError(ssl.SSLCertVerificationError(1, "certificate verify failed"))
        with patch("src.core.provider_runtime.runtime.urlopen", side_effect=failure):
            with self.assertRaises(ProviderRuntimeError) as raised:
                _stdlib_transport("GET", "https://api.example.test", {}, None, 30.0)
        self.assertEqual(raised.exception.category, "tls")
        self.assertFalse(raised.exception.retryable)


    def test_windows_https_transport_uses_native_truststore_with_verification_and_hostname_checks(self):
        class FakeContext:
            def __init__(self, protocol):
                self.protocol = protocol
                self.verify_mode = None
                self.check_hostname = False
                self.alpn = None

            def set_alpn_protocols(self, protocols):
                self.alpn = list(protocols)

        class FakeTruststore:
            SSLContext = FakeContext

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"{}"

        _windows_native_tls_context.cache_clear()
        try:
            with (
                patch("src.core.provider_runtime.runtime.sys.platform", "win32"),
                patch("src.core.provider_runtime.runtime._truststore", FakeTruststore),
                patch("src.core.provider_runtime.runtime.urlopen", return_value=Response()) as mocked_open,
            ):
                result = _stdlib_transport("GET", "https://api.example.test", {}, None, 30.0)
            self.assertEqual(result, {})
            context = mocked_open.call_args.kwargs["context"]
            self.assertEqual(context.protocol, ssl.PROTOCOL_TLS_CLIENT)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.alpn, ["http/1.1"])
        finally:
            _windows_native_tls_context.cache_clear()

    def test_windows_https_transport_fails_closed_when_native_trust_backend_is_missing(self):
        _windows_native_tls_context.cache_clear()
        try:
            with (
                patch("src.core.provider_runtime.runtime.sys.platform", "win32"),
                patch("src.core.provider_runtime.runtime._truststore", None),
                patch("src.core.provider_runtime.runtime.urlopen") as mocked_open,
            ):
                with self.assertRaises(ProviderRuntimeError) as raised:
                    _stdlib_transport("GET", "https://api.example.test", {}, None, 30.0)
            self.assertEqual(raised.exception.category, "tls")
            self.assertFalse(raised.exception.retryable)
            self.assertIn("native TLS trust backend is unavailable", str(raised.exception))
            mocked_open.assert_not_called()
        finally:
            _windows_native_tls_context.cache_clear()

    def test_non_windows_https_transport_preserves_existing_stdlib_urlopen_path(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"{}"

        request = __import__("urllib.request", fromlist=["Request"]).Request("https://api.example.test")
        with (
            patch("src.core.provider_runtime.runtime.sys.platform", "linux"),
            patch("src.core.provider_runtime.runtime.urlopen", return_value=Response()) as mocked_open,
        ):
            with _verified_urlopen(request, timeout=30.0) as response:
                self.assertEqual(response.read(), b"{}")
        self.assertNotIn("context", mocked_open.call_args.kwargs)

    def test_retryable_recipient_failure_retries_at_most_three_total_attempts_and_counts_once(self):
        attempts = {"send": 0}
        keys: list[str] = []
        def hook(headers, _form):
            attempts["send"] += 1
            keys.append(headers["Idempotency-Key"])
            if attempts["send"] < MAX_TOTAL_ATTEMPTS:
                raise ProviderRuntimeError("temporary", category="http", retryable=True, http_status=503, retry_after_seconds=0)
            return {"id": "in_1"}

        state, task = self._stripe_state()
        runtime = ProviderRuntime(transport=self._successful_transport_with_send_hook(hook), retry_jitter_source=lambda: 0.0)
        runtime._retry_delay_seconds = lambda *_args: 0.0  # type: ignore[method-assign]
        context = _Context(task)
        runtime.make_task_runner(task, state)(context)
        self.assertEqual(attempts["send"], 3)
        self.assertEqual(len(set(keys)), 1)
        self.assertEqual(context.progress_events[-1][:3], (1, 1, 0))

    def test_permanent_failure_is_not_automatically_retried(self):
        attempts = {"send": 0}
        def hook(_headers, _form):
            attempts["send"] += 1
            raise ProviderRuntimeError("permanent", category="http", retryable=False, http_status=400)

        state, task = self._stripe_state()
        runtime = ProviderRuntime(transport=self._successful_transport_with_send_hook(hook))
        context = _Context(task)
        with self.assertRaises(ProviderRuntimeError):
            runtime.make_task_runner(task, state)(context)
        self.assertEqual(attempts["send"], 1)
        self.assertEqual(context.progress_events[-1][:3], (1, 0, 1))

    def test_stop_during_retry_prevents_next_attempt_and_preserves_pending_recipient(self):
        attempts = {"send": 0}
        def hook(_headers, _form):
            attempts["send"] += 1
            raise ProviderRuntimeError("temporary", category="timeout", retryable=True, retry_after_seconds=0)

        state, task = self._stripe_state()
        runtime = ProviderRuntime(transport=self._successful_transport_with_send_hook(hook), retry_jitter_source=lambda: 0.0)
        runtime._retry_delay_seconds = lambda *_args: 0.1  # type: ignore[method-assign]
        context = _Context(task)
        original_log = context.log
        def stop_on_retry(message: str):
            original_log(message)
            if "Retrying in" in message:
                context.stop_flag.set()
        context.log = stop_on_retry  # type: ignore[method-assign]
        runtime.make_task_runner(task, state)(context)
        self.assertEqual(attempts["send"], 1)
        summary = runtime.delivery_summary(task)
        self.assertTrue(summary.continuation_safe)
        self.assertEqual(summary.pending_recipients, ("a@example.com",))
        self.assertEqual(summary.failed, 0)

    def test_cooperative_retry_wait_pauses_without_consuming_delay(self):
        class Ctx:
            pass
        ctx = Ctx()
        ctx.pause_gate = threading.Event()
        ctx.stop_flag = threading.Event()
        done = threading.Event()
        result = {"value": False}
        def target():
            result["value"] = _cooperative_retry_wait(ctx, 0.05)
            done.set()
        thread = threading.Thread(target=target)
        thread.start()
        time.sleep(0.08)
        self.assertFalse(done.is_set())
        ctx.pause_gate.set()
        thread.join(1.0)
        self.assertTrue(done.is_set())
        self.assertTrue(result["value"])



    def test_retry_reuses_original_round_robin_account_assignment(self):
        state = AppState()
        account_a = state.add_account("stripe", "Stripe", "A", "Test", {"secret_key": "sk_test_accountA"}, status="Verified")
        account_b = state.add_account("stripe", "Stripe", "B", "Test", {"secret_key": "sk_test_accountB"}, status="Verified")
        customer_list = state.create_customer_list("Customers")
        state.add_emails(customer_list.id, ["first@example.com", "second@example.com"])
        template = state.save_invoice_template(
            template_id=None, name="Monthly", currency="usd", days_until_due=30, memo="", footer="",
            automatic_tax=False, reuse_customer=True, invoice_title="Invoice", invoice_subtitle="",
            customer_note="", terms=[], items=[("Service", "1", "10.00", "0")],
        )
        task = state.create_task("stripe", "Stripe", [account_a.id, account_b.id], customer_list.id, template.id)
        send_auth: list[str] = []
        send_count = {"value": 0}
        def transport(method, url, headers, body, timeout):
            path = urlparse(url).path
            if method == "GET" and path.endswith("/customers"):
                return {"data": []}
            if method == "POST" and path.endswith("/customers"):
                return {"id": "cus_1"}
            if method == "POST" and path.endswith("/invoices"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/invoiceitems"):
                return {"id": "ii_1"}
            if method == "POST" and path.endswith("/finalize"):
                return {"id": "in_1"}
            if method == "POST" and path.endswith("/send"):
                send_auth.append(headers["Authorization"])
                send_count["value"] += 1
                if send_count["value"] in {2, 3}:
                    raise ProviderRuntimeError("temporary", category="http", retryable=True, http_status=503, retry_after_seconds=0)
                return {"id": "in_1"}
            raise AssertionError((method, url))
        runtime = ProviderRuntime(transport=transport, retry_jitter_source=lambda: 0.0)
        runtime._retry_delay_seconds = lambda *_args: 0.0  # type: ignore[method-assign]
        runtime.make_task_runner(task, state)(_Context(task))
        self.assertEqual(len(send_auth), 4)
        self.assertNotEqual(send_auth[0], send_auth[1])
        self.assertEqual(send_auth[1], send_auth[2])
        self.assertEqual(send_auth[2], send_auth[3])

    def test_retry_exhaustion_stops_after_three_total_attempts_and_counts_failure_once(self):
        attempts = {"send": 0}
        keys: list[str] = []
        def hook(headers, _form):
            attempts["send"] += 1
            keys.append(headers["Idempotency-Key"])
            raise ProviderRuntimeError("temporary", category="http", retryable=True, http_status=503, retry_after_seconds=0)

        state, task = self._stripe_state()
        runtime = ProviderRuntime(transport=self._successful_transport_with_send_hook(hook), retry_jitter_source=lambda: 0.0)
        runtime._retry_delay_seconds = lambda *_args: 0.0  # type: ignore[method-assign]
        context = _Context(task)
        with self.assertRaisesRegex(ProviderRuntimeError, r"1 recipient\(s\) failed"):
            runtime.make_task_runner(task, state)(context)
        self.assertEqual(attempts["send"], MAX_TOTAL_ATTEMPTS)
        self.assertEqual(len(set(keys)), 1)
        self.assertEqual(context.progress_events[-1][:3], (1, 0, 1))

    def test_retry_after_overrides_shorter_exponential_delay(self):
        runtime = ProviderRuntime(retry_jitter_source=lambda: 0.0)
        exc = ProviderRuntimeError(
            "rate limited",
            category="rate-limit",
            retryable=True,
            http_status=429,
            retry_after_seconds=4.0,
        )
        self.assertEqual(runtime._retry_delay_seconds(1, exc), 4.0)
        self.assertEqual(runtime._retry_delay_seconds(2, exc), 4.0)

    def test_tls_certificate_verification_failure_is_permanent(self):
        import ssl
        failure = URLError(ssl.SSLCertVerificationError(1, "certificate verify failed"))
        with patch("src.core.provider_runtime.runtime.urlopen", side_effect=failure):
            with self.assertRaises(ProviderRuntimeError) as raised:
                _stdlib_transport("GET", "https://api.example.test", {}, None, 30.0)
        self.assertEqual(raised.exception.category, "tls")
        self.assertFalse(raised.exception.retryable)

    def test_worker_and_shutdown_source_contract_never_force_terminates_or_accepts_close_while_active(self):
        root = Path(__file__).resolve().parents[1]
        manager = (root / "src" / "core" / "worker_manager" / "manager.py").read_text(encoding="utf-8")
        window = (root / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertEqual(manager.count("all_stopped = Signal()"), 1)
        self.assertIn("def has_active_workers", manager)
        self.assertNotIn(".terminate()", manager)
        self.assertNotIn("thread.wait(", manager)
        close = window.split("def closeEvent", 1)[1]
        self.assertIn("self.worker_manager.has_active_workers()", close)
        self.assertIn("event.ignore()", close)
        self.assertIn("self.worker_manager.stop_all()", close)
        self.assertIn("event.accept()", close)
        self.assertLess(close.index("event.ignore()"), close.index("event.accept()"))


if __name__ == "__main__":
    unittest.main()
