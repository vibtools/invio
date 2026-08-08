# Troubleshooting

## `ImportError: cannot import name 'ProviderManifestError'`

This was caused by the provider-manager package not re-exporting `ProviderManifestError`. The package exports it from `src.core.provider_manager`, matching the existing import used by `MainWindow`.

## Sidebar navigation appears light on Windows

Release `v1.0.0.1` explicitly applies the Vib Tools sidebar background to the sidebar scroll area, its viewport, and the navigation host. Confirm the updated `src/ui/main_window.py` and `src/ui/styles.py` are both present.

## Provider does not appear in Accounts or Tasks

Install it from **Providers** or load a valid provider JSON manifest. A bundled provider may be visible as `Available` on the Providers page while still being intentionally absent from Accounts and Tasks until installation.

## Stripe or Refrens does not appear on the Providers page

Confirm these files exist:

- `providers/packages/stripe/provider.json`
- `providers/packages/refrens/provider.json`

Then restart Invio.

## Add Account says API Test Pending

Run **API Test** after completing all required provider credential fields. The current provider integrations perform credential-structure validation; network verification is unavailable unless implemented by that provider integration.

## Start Task does not send

The selected provider has no registered task runner. Invio reports the provider as unavailable and sends nothing. This prevents a missing integration from being represented as a successful operation.

## Account cannot be selected for a new task

The account is reserved by another task. Close the owning task to release it.
