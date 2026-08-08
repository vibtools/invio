# Provider Manifest Contract

Provider manifests are validated JSON files describing provider identity, credentials, account modes, and declared capabilities. Manifest loading itself does not execute provider code.

## Schema

```json
{
  "id": "provider-id",
  "name": "Provider Name",
  "version": "1.0.0",
  "description": "Provider description",
  "credential_fields": [
    {
      "key": "secret_key",
      "label": "Secret key",
      "kind": "password",
      "required": true,
      "placeholder": "credential placeholder"
    }
  ],
  "account_modes": ["Test", "Live"],
  "capabilities": ["invoice", "send_invoice", "api_test"]
}
```

## Rules

- `id` must use lowercase letters, digits, hyphens, or underscores.
- `name` and `version` are required.
- Credential field `kind` must be `text` or `password`.
- A provider is selectable by Accounts and Tasks only when its validated manifest exists in `providers/registry`.
- `ProviderManager.uninstall(provider_id)` removes only the installed registry manifest after validated lookup; it does not delete the packaged provider manifest or current in-memory domain data.
- Provider execution is supplied separately through the existing task-runner boundary; loading a manifest alone never executes provider code.
- `ProviderManifestError` is part of the public `src.core.provider_manager` package surface so UI code can safely catch manifest validation/install errors.

## Current packaged manifests

- `stripe` `v1.0.0`: `secret_key`; modes `Test`, `Live`.
- `refrens` `v1.0.3`: `base_url`, `url_key`, `app_id`, `app_secret`; mode `Default`.
