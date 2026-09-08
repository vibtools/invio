from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

BUNDLE = Path(__file__).resolve().parents[1]

def load_adapter():
    spec = importlib.util.spec_from_file_location("browser_oauth_adapter_test", BUNDLE / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module, module.create_adapter()

class BrowserOAuthTests(unittest.TestCase):
    def test_authorization_code_flow_captures_realm_and_refresh_token(self):
        module, adapter=load_adapter()
        creds={"client_id":"CID","client_secret":"SECRET","redirect_uri":"https://example.com/qbo/callback"}
        auth=type("Auth",(),{"credentials":creds,"mode":"Production","redirect_uri":creds["redirect_uri"],"state":"STATE","code_challenge":""})()
        parsed=urlsplit(adapter.build_oauth_authorization_url(auth)); query=parse_qs(parsed.query)
        self.assertEqual(parsed.netloc,"appcenter.intuit.com")
        self.assertEqual(query["scope"],["com.intuit.quickbooks.accounting"])
        def request(**kwargs):
            self.assertTrue(kwargs["url"].endswith("/oauth2/v1/tokens/bearer"))
            return {"access_token":"ACCESS","refresh_token":"REFRESH"}
        ctx=type("Done",(),{"credentials":creds,"mode":"Production","callback_params":{"realmId":"REALM"},"authorization_code":"CODE","redirect_uri":creds["redirect_uri"],"code_verifier":"","request":staticmethod(request)})()
        result=adapter.complete_oauth_authorization(ctx)
        self.assertEqual(result.credential_updates,{"refresh_token":"REFRESH","realm_id":"REALM"})

    def test_production_rejects_loopback_or_ip_redirect(self):
        _module, adapter = load_adapter()
        for redirect in ("http://localhost:8768/callback", "https://127.0.0.1/qbo/callback", "https://192.0.2.10/qbo/callback"):
            with self.subTest(redirect=redirect):
                creds={"client_id":"CID","client_secret":"SECRET","redirect_uri":redirect}
                auth=type("Auth",(),{"credentials":creds,"mode":"Production","redirect_uri":redirect,"state":"STATE","code_challenge":""})()
                with self.assertRaises(Exception):
                    adapter.build_oauth_authorization_url(auth)

    def test_sandbox_allows_explicit_loopback_redirect(self):
        _module, adapter = load_adapter()
        redirect="http://localhost:8768/callback"
        creds={"client_id":"CID","client_secret":"SECRET","redirect_uri":redirect}
        auth=type("Auth",(),{"credentials":creds,"mode":"Sandbox","redirect_uri":redirect,"state":"STATE","code_challenge":""})()
        self.assertIn("appcenter.intuit.com", adapter.build_oauth_authorization_url(auth))

    def test_latest_rotating_refresh_token_is_persisted_for_next_use(self):
        module, adapter=load_adapter()
        class Store:
            saved={}
            @staticmethod
            def credential_ref(account_id): return "account:"+account_id
            def get_credentials(self, reference): return self.saved.get(reference)
            def set_credentials(self, account_id, credentials):
                self.saved[self.credential_ref(account_id)] = dict(credentials)
                return self.credential_ref(account_id)
        module.CredentialStore=Store
        seen=[]
        def oauth(url, *, headers, body):
            seen.append(body.decode())
            return {"access_token":"ACCESS","refresh_token":"LATEST","expires_in":3600}
        adapter._direct_oauth_json=oauth
        token=adapter._access_token(("CID","SECRET","ORIGINAL","Production","REALM",""))
        self.assertEqual(token,"ACCESS")
        self.assertIn("refresh_token=ORIGINAL", seen[0])
        self.assertTrue(any(value.get("refresh_token")=="LATEST" for value in Store.saved.values()))

if __name__ == "__main__": unittest.main()
