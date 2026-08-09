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

## Execution binding in v1.0.0.1.3

Manifest installation and executable provider behavior remain separate concerns. `MainWindow` first checks the existing explicitly registered task-runner extension point; when none is registered, packaged Stripe/Refrens behavior is resolved by `src.core.provider_runtime.ProviderRuntime`.

A manifest capability therefore describes supported intent but does not make arbitrary external provider code executable by itself. Custom/external providers still require an owner-approved runner implementation.


## Executable API-test capability

A manifest capability named `api_test` is declarative metadata only. In `v1.0.0.1.6`, Add Account treats API Test as available only when `ProviderRuntime.supports_api_test(provider_id)` confirms an executable built-in adapter. A loaded manifest alone cannot turn required-field validation into a successful provider verification.

## P06 manifest/runtime reconciliation

A manifest capability remains a **declaration**, not proof of executable code. P06 compares packaged-ID installed manifests with the canonical packaged manifest across execution-relevant fields: provider ID, ordered credential key/kind/required contract, account modes, and declared capabilities. Display-only name/version/description differences do not define the runtime binding.

The packaged IDs `stripe` and `refrens` are reserved. `ProviderManager.load_external()` rejects external manifests using a packaged ID rather than overwriting `providers/registry/<id>.json`. Existing conflicting packaged-ID registry state is preserved on disk but Account/Test/Task operations fail closed until the owner explicitly uninstalls/reinstalls the packaged provider.

Current executable capabilities are reported separately from declared capabilities. Stripe currently executes `invoice`, `send_invoice`, and `api_test`; Refrens currently executes `api_test` only because its normal Task pipeline remains P11 scope. External manifests do not gain executable capability from declaration alone; the historical injected task-runner API remains the only existing external execution boundary until P13.
