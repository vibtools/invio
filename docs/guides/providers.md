# Provider Guide

Packaged provider manifests live under `providers/packages/<provider>/provider.json`. Installing a provider copies its validated manifest into the local registry. Loading an external provider performs the same manifest validation before registration. Installed provider cards expose **Uninstall**, which removes that provider manifest from the local registry.

## Bundled providers

### Stripe

Packaged at `providers/packages/stripe/provider.json`.

Credential contract:

- `secret_key` — required password field.
- Accepted reference-app key families include `sk_test_`, `sk_live_`, `rk_test_`, and `rk_live_`.
- Account modes exposed by the manifest: `Test`, `Live`.

### Refrens

Packaged at `providers/packages/refrens/provider.json` and based on the supplied Refrens Invoice Sender v1.0.3 account/profile contract.

Credential contract:

- `base_url` — required API Base URL. Reference default: `https://api.refrens.com`.
- `url_key` — required Refrens business URL Key.
- `app_id` — required App ID.
- `app_secret` — required password field.

The current provider integrations validate required credential structure. Network authentication/API verification is available only when implemented by the selected provider integration.

## Visibility rule

A packaged provider may be listed as **Available** on the Providers page, but it is not selectable in Accounts or Tasks until the user installs it. Installed manifests live under `providers/registry/`. Uninstalling a bundled provider does not remove its package under `providers/packages/`, so it returns to the **Available** state and can be installed again. Existing in-memory accounts/tasks are not deleted by provider uninstall.
