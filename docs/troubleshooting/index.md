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


## Provider Uninstall does not remove Stripe/Refrens from the Providers page

This is expected for bundled providers. **Uninstall** removes the installed copy from `providers/registry/`, so the provider changes from **Installed** to **Available**. Its packaged manifest remains under `providers/packages/` so it can be installed again. Current in-memory accounts/tasks are not deleted.

## A modal looks wider than before

Release `v1.0.0.1.2` intentionally uses wider, shorter application-owned dialogs for more compact workflows. Add Account uses two credential columns only when the selected provider declares more than two credential fields. Native operating-system file/folder picker windows are not resized by Invio.

## Add Account says API Test Pending

Run **API Test** after completing all required provider credential fields. The current provider integrations perform credential-structure validation; network verification is unavailable unless implemented by that provider integration.

## Start Task does not send

The selected provider has no registered task runner. Invio reports the provider as unavailable and sends nothing. This prevents a missing integration from being represented as a successful operation.

## Account cannot be selected for a new task

The account is reserved by another task. Close the owning task to release it.

## Settings do not save

Select **Save Changes** and read the message at the bottom of the Settings page. If the selected **Default file folder** does not exist, choose an existing folder or leave the field blank. Invio also reports filesystem write errors instead of silently accepting an unsaved preference.

## Invio starts with default settings after a settings-file problem

If the per-user settings JSON is malformed or cannot be parsed, Invio uses baseline defaults so the desktop app can still start. A warning is written to Live Logs. Correct or remove the damaged settings file, then save preferences again from **Settings**.

## Invio did not restore my previous window position

**Remember window size and position** must be enabled before exit. Invio intentionally ignores a saved position that is not on a currently available screen, which prevents an old multi-monitor position from reopening the window off-screen.

## File dialogs do not open in the expected folder

Check **Settings → File Locations**. A valid remembered last folder takes priority when **Remember the last folder I used** is enabled. Otherwise Invio uses the configured default folder, or the operating-system default when the field is blank.
