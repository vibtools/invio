# Easy Onboarding V1 provider example

A trusted external provider that needs more than a simple API key can opt into the generic account-setup contract without changing Invio UI code.

```json
{
  "credential_fields": [
    {"key":"client_id","label":"Client ID","kind":"text","required":true,"ownership":"user_required"},
    {"key":"refresh_token","label":"Refresh Token","kind":"password","required":true,"ownership":"generated"},
    {"key":"tenant_id","label":"Tenant ID","kind":"text","required":true,"ownership":"discovered"},
    {"key":"default_item_id","label":"Default Item ID","kind":"text","required":false,"ownership":"managed"}
  ],
  "runtime_adapter": {"interface_version":1,"adapter_version":"1.2.0","entrypoint":"create_adapter"},
  "browser_auth": {"interface_version":1},
  "onboarding": {"interface_version":1}
}
```

The adapter exposes `onboarding_profile = ProviderOnboardingProfile(...)` and `prepare_account(context)`. `prepare_account` should discover authoritative account metadata, reuse existing compatible provider resources first, create only narrowly required resources when safe, and return only manifest-declared credential updates. The host rejects access-token persistence.

Quick Connect keeps `generated`, `discovered`, `managed`, and `user_choice` fields hidden while retaining them internally for protected account persistence. Legacy providers that omit `onboarding` keep the existing credential UI unchanged.
