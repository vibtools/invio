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
    def test_browser_oauth_pkce_exchange_and_org_discovery(self):
        module, adapter = load_adapter()
        auth = type("Auth", (), {"credentials":{"accounts_server_url":"https://accounts.zoho.com","client_id":"CID","client_secret":"SECRET"},"redirect_uri":adapter.browser_oauth_profile.redirect_uri,"state":"STATE","code_challenge":"CHALLENGE"})()
        parsed=urlsplit(adapter.build_oauth_authorization_url(auth)); query=parse_qs(parsed.query)
        self.assertIn("ZohoInvoice.invoices.CREATE", query["scope"][0])
        calls=[]
        def request(**kwargs):
            calls.append(kwargs)
            if kwargs["url"].endswith("/oauth/v2/token"): return {"access_token":"ACCESS","refresh_token":"REFRESH"}
            if kwargs["url"].endswith("/invoice/v3/organizations"): return {"organizations":[{"organization_id":"456","name":"Vib Invoice"}]}
            raise AssertionError(kwargs)
        ctx=type("Done",(),{"credentials":auth.credentials,"callback_params":{},"authorization_code":"CODE","redirect_uri":auth.redirect_uri,"code_verifier":"VERIFIER","request":staticmethod(request)})()
        result=adapter.complete_oauth_authorization(ctx)
        self.assertEqual(result.choices[0].value,"456")
        self.assertEqual(result.credential_updates["refresh_token"],"REFRESH")

if __name__ == "__main__": unittest.main()
