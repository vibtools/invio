from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from src.core.provider_manager import ProviderManager, ProviderManifestError
from src.core.provider_runtime import (
    BrowserOAuthError,
    ExternalAdapterRegistry,
    LoopbackOAuthReceiver,
    ProviderRuntime,
    ProviderRuntimeError,
    parse_oauth_callback,
    validate_redirect_uri,
)


class BrowserOAuthHostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "providers" / "packages").mkdir(parents=True)
        (self.root / "providers" / "registry").mkdir(parents=True)

    def _bundle(self, *, browser_auth: bool = True) -> Path:
        bundle = self.root / "bundle"
        bundle.mkdir(exist_ok=True)
        manifest = {
            "id": "oauth_demo",
            "name": "OAuth Demo",
            "version": "1.1.0",
            "description": "OAuth host contract test",
            "credential_fields": [
                {"key": "client_id", "label": "Client ID", "kind": "text", "required": True},
                {"key": "redirect_uri", "label": "Redirect URI", "kind": "text", "required": True},
                {"key": "refresh_token", "label": "Refresh Token", "kind": "password", "required": True},
                {"key": "tenant_id", "label": "Tenant", "kind": "text", "required": True},
            ],
            "account_modes": ["Default"],
            "capabilities": ["invoice", "send_invoice", "api_test"],
            "runtime_adapter": {"interface_version": 1, "adapter_version": "1.1.0", "entrypoint": "create_adapter"},
        }
        if browser_auth:
            manifest["browser_auth"] = {"interface_version": 1}
        (bundle / "provider.json").write_text(json.dumps(manifest), encoding="utf-8")
        (bundle / "adapter.py").write_text(
            '''from urllib.parse import urlencode\nfrom src.core.provider_runtime import (\n BrowserOAuthProfile, ExternalOAuthAccountChoice, ExternalOAuthConnectionResult,\n ExternalRecipientResult, NON_IDEMPOTENT_MUTATION, SAFE_READ, ProviderCapabilityProfile\n)\n\nclass Adapter:\n    interface_version=1\n    provider_id="oauth_demo"\n    adapter_version="1.1.0"\n    scheduling_policy=None\n    profile=ProviderCapabilityProfile(\n        provider_id="oauth_demo", executable_capabilities=frozenset({"invoice","send_invoice","api_test"}),\n        task_execution_enabled=True, task_unavailable_message="", invoice_types=frozenset({"INVOICE"}),\n        currencies=None, supports_automatic_tax=False, supports_line_tax=False, supports_customer_reuse=False,\n        supports_memo=True, supports_footer=True, supports_customer_note=True, supports_terms=True,\n        required_customer_fields=("email",),\n    )\n    browser_oauth_profile=BrowserOAuthProfile(\n        button_label="Connect OAuth Demo", redirect_uri_credential_key="redirect_uri", pkce_required=True,\n        connect_required_credential_keys=("client_id","redirect_uri"), timeout_seconds=60,\n    )\n    def build_oauth_authorization_url(self, context):\n        return "https://auth.example/authorize?" + urlencode({\n            "client_id": context.credentials["client_id"], "redirect_uri": context.redirect_uri,\n            "response_type": "code", "state": context.state, "code_challenge": context.code_challenge,\n            "code_challenge_method": "S256",\n        })\n    def complete_oauth_authorization(self, context):\n        token = context.request(\n            stage="oauth_token", method="POST", url="https://auth.example/token",\n            json_data={"code": context.authorization_code, "code_verifier": context.code_verifier},\n        )\n        return ExternalOAuthConnectionResult(\n            credential_updates={"refresh_token": token["refresh_token"]},\n            message="OAuth Demo connected.",\n            choices=(ExternalOAuthAccountChoice("tenant-1", "Tenant One"), ExternalOAuthAccountChoice("tenant-2", "Tenant Two")),\n            choice_credential_key="tenant_id",\n        )\n    def test_account(self, context):\n        context.request(stage="health", operation_kind=SAFE_READ, method="GET", url="https://api.example/health")\n        return "ok"\n    def validate_task(self, context): return ()\n    def execute_recipient(self, context):\n        context.request(stage="send", operation_kind=NON_IDEMPOTENT_MUTATION, method="POST", url="https://api.example/send")\n        return ExternalRecipientResult(final_stage="external_mutation:send")\n\ndef create_adapter(): return Adapter()\n''',
            encoding="utf-8",
        )
        return bundle / "provider.json"

    @staticmethod
    def _transport(method, url, headers, body, timeout):
        del headers, body, timeout
        if method == "POST" and url == "https://auth.example/token":
            return {"refresh_token": "REFRESH-1"}
        if method == "GET" and url == "https://api.example/health":
            return {"ok": True}
        if method == "POST" and url == "https://api.example/send":
            return {"ok": True}
        raise AssertionError((method, url))

    def _runtime(self):
        runtime = ProviderRuntime(project_root=self.root, transport=self._transport)
        manager = ProviderManager(self.root)
        manager.load_external(self._bundle(), allow_executable=True, adapter_validator=runtime.validate_external_adapter)
        runtime.reload_external_adapters()
        return manager, runtime

    def test_manifest_browser_auth_requires_runtime_adapter(self):
        path = self._bundle(browser_auth=False)
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw.pop("runtime_adapter")
        raw["browser_auth"] = {"interface_version": 1}
        path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ProviderManifestError, "requires an executable runtime_adapter"):
            ProviderManager(self.root).inspect_manifest(path)

    def test_external_adapter_browser_oauth_contract_validates_and_is_discoverable(self):
        manager, runtime = self._runtime()
        manifest = manager.get_installed("oauth_demo")
        self.assertIsNotNone(manifest)
        self.assertIsNotNone(manifest.browser_auth)
        self.assertTrue(runtime.supports_browser_oauth("oauth_demo"))
        self.assertEqual(runtime.browser_oauth_profile("oauth_demo").button_label, "Connect OAuth Demo")

    def test_oauth_session_uses_state_pkce_registered_redirect_and_returns_only_declared_credentials(self):
        _manager, runtime = self._runtime()
        credentials = {"client_id": "CLIENT", "redirect_uri": "https://app.example/oauth/callback"}
        session = runtime.create_browser_oauth_session("oauth_demo", credentials, mode="Default")
        self.assertEqual(session.callback_mode, "manual")
        self.assertGreaterEqual(len(session.state), 32)
        self.assertGreaterEqual(len(session.code_verifier), 43)
        self.assertTrue(session.code_challenge)
        callback = f"https://app.example/oauth/callback?code=AUTH-CODE&state={session.state}"
        result = runtime.complete_browser_oauth("oauth_demo", session, callback, credentials, mode="Default")
        self.assertEqual(result.credential_updates, {"refresh_token": "REFRESH-1"})
        self.assertEqual(result.choice_credential_key, "tenant_id")
        self.assertEqual([choice.value for choice in result.choices], ["tenant-1", "tenant-2"])

    def test_registered_redirect_uri_rejects_fixed_query_string(self):
        with self.assertRaisesRegex(BrowserOAuthError, "must not contain a query string"):
            validate_redirect_uri("http://127.0.0.1:8765/oauth/callback?fixed=value")

    def test_callback_rejects_wrong_state_redirect_and_provider_error(self):
        redirect = "https://app.example/callback"
        with self.assertRaisesRegex(BrowserOAuthError, "state validation failed"):
            parse_oauth_callback(f"{redirect}?code=x&state=wrong", redirect_uri=redirect, expected_state="expected")
        with self.assertRaisesRegex(BrowserOAuthError, "does not match"):
            parse_oauth_callback("https://evil.example/callback?code=x&state=expected", redirect_uri=redirect, expected_state="expected")
        with self.assertRaisesRegex(BrowserOAuthError, "not completed"):
            parse_oauth_callback(f"{redirect}?error=access_denied&state=expected", redirect_uri=redirect, expected_state="expected")

    def test_oauth_array_response_transport_supports_provider_account_discovery(self):
        calls = []

        def transport(method, url, headers, body, timeout):
            calls.append((method, url, headers, body, timeout))
            if url == "https://api.example/connections":
                return [{"tenantId": "tenant-1"}]
            raise AssertionError((method, url))

        runtime = ProviderRuntime(project_root=self.root, transport=transport)
        result = runtime._external_oauth_request(
            stage="oauth_account_discovery",
            method="GET",
            url="https://api.example/connections",
            response_kind="array",
        )
        self.assertEqual(result, [{"tenantId": "tenant-1"}])
        self.assertEqual(calls[0][0:2], ("GET", "https://api.example/connections"))

    def test_oauth_array_response_rejects_wrong_shape(self):
        def transport(method, url, headers, body, timeout):
            del method, url, headers, body, timeout
            return {"not": "an array"}

        runtime = ProviderRuntime(project_root=self.root, transport=transport)
        with self.assertRaisesRegex(ProviderRuntimeError, "unexpected response format"):
            runtime._external_oauth_request(
                stage="oauth_account_discovery",
                method="GET",
                url="https://api.example/connections",
                response_kind="array",
            )

    def test_loopback_receiver_cancellation_is_fail_closed(self):
        import socket

        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        receiver = LoopbackOAuthReceiver(f"http://127.0.0.1:{port}/oauth/callback")
        errors: list[BaseException] = []

        def wait():
            try:
                receiver.wait(10)
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=wait)
        thread.start()
        time.sleep(0.05)
        receiver.cancel()
        thread.join(2)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], BrowserOAuthError)
        self.assertIn("cancelled", str(errors[0]).lower())

    def test_loopback_receiver_accepts_exact_callback_once(self):
        # Bind an ephemeral socket first only to choose a currently available port.
        import socket
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        redirect = f"http://127.0.0.1:{port}/oauth/callback"
        receiver = LoopbackOAuthReceiver(redirect)
        result: list[str] = []
        error: list[BaseException] = []

        def wait():
            try:
                result.append(receiver.wait(10))
            except BaseException as exc:
                error.append(exc)

        thread = threading.Thread(target=wait)
        thread.start()
        time.sleep(0.05)
        with urlopen(f"{redirect}?code=abc&state=xyz", timeout=2) as response:  # noqa: S310 - local test receiver
            self.assertEqual(response.status, 200)
        thread.join(2)
        self.assertFalse(error)
        self.assertEqual(result, [f"{redirect}?code=abc&state=xyz"])


if __name__ == "__main__":
    unittest.main()
