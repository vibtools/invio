# Browser OAuth Provider Example — Interface v1

This example documents the optional authorization extension only. Existing External Provider Adapter v1 task methods remain unchanged.

```json
{
  "runtime_adapter": {"interface_version": 1, "adapter_version": "1.1.0", "entrypoint": "create_adapter"},
  "browser_auth": {"interface_version": 1}
}
```

Adapter outline:

```python
from src.core.provider_runtime import BrowserOAuthProfile, ExternalOAuthConnectionResult

class Adapter:
    browser_oauth_profile = BrowserOAuthProfile(
        button_label="Connect Provider",
        redirect_uri="http://127.0.0.1:8765/oauth/callback/provider",
        pkce_required=True,
        connect_required_credential_keys=("client_id",),
    )

    def build_oauth_authorization_url(self, context):
        # Return the provider HTTPS authorization endpoint with context.state,
        # redirect_uri and PKCE challenge. Never put a client secret in this URL.
        ...

    def complete_oauth_authorization(self, context):
        # Exchange context.authorization_code using context.request, discover
        # the provider account, and return refresh/bootstrap credentials only.
        return ExternalOAuthConnectionResult(
            credential_updates={"refresh_token": "..."},
            message="Provider connected.",
        )
```

The host validates callback state/redirect identity and refuses undeclared credential fields or access-token persistence.
