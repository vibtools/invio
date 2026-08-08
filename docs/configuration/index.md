# Configuration

Invio `v1.0.0.1.3` keeps application preferences separate from provider credentials and runtime domain data.

## Settings

Settings includes Startup & Window, Confirmations, Live Logs, and File Locations. Startup choices now include Dashboard plus the existing pages and **Last page used**. The default remains Accounts.

Checked controls use the Vib Tools compact checkbox treatment with a visible checkmark. Existing settings semantics are unchanged.

## Storage

The non-sensitive per-user settings JSON never stores account credential dictionaries/provider secrets. Writes remain atomic and malformed settings fall back to defaults with a Live Logs warning.

Typical paths:

- Windows: `%APPDATA%\\Vib Tools\\Invio\\settings.json`
- macOS: `~/Library/Application Support/Vib Tools/Invio/settings.json`
- Linux: `$XDG_CONFIG_HOME/Vib Tools/Invio/settings.json`, otherwise `~/.config/Vib Tools/Invio/settings.json`

## Provider runtime

Packaged manifests are under `providers/packages/`; installed manifests are under ignored `providers/registry/`. Built-in provider execution code is in `src/core/provider_runtime/` and uses standard-library HTTPS requests, so `v1.0.0.1.3` adds no dependency.

Account credentials remain in memory for the active session.
