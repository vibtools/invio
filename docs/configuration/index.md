# Configuration

Invio `v1.0.0.1.11` separates Settings, durable operational data, provider registry state, and protected provider credentials.

## Settings

Settings includes Startup & Window, Confirmations, Live Logs, and File Locations. The default startup page remains Accounts.

The non-sensitive settings JSON uses atomic temporary-file replacement and never stores provider credential dictionaries.

Typical settings paths:

- Windows: `%APPDATA%\\Vib Tools\\Invio\\settings.json`
- macOS: `~/Library/Application Support/Vib Tools/Invio/settings.json`
- Linux: `$XDG_CONFIG_HOME/Vib Tools/Invio/settings.json`, otherwise `~/.config/Vib Tools/Invio/settings.json`

## Durable Operational Storage

P02 uses SQLite for non-sensitive operational state:

- Accounts metadata/status and credential reference;
- Customer Lists and ordered emails;
- Invoice Templates/items/terms;
- Tasks, account selection, counters/status/message;
- account reservations.

Typical database filename: `domain.sqlite3` in the same per-user Invio directory as `settings.json`.

The database uses schema version `1`, foreign keys, transactional writes, WAL journaling, and `synchronous=FULL`. Corrupt, newer, or unrecognized storage is not silently replaced.

## Protected Credentials

Provider credential values are stored with Python `keyring` through approved OS-protected backend families only. SQLite stores only `account:<account-id>` references. Invio has no plaintext credential fallback.

If the protected credential entry/backend is unavailable at startup, the Account metadata is still restored for visibility but its runtime status becomes **Not Verified**, so P01 Task gates block execution.

## Provider Registry

Bundled manifests remain under `providers/packages/`; installed manifests remain under ignored `providers/registry/`. P02 does not change ProviderManager behavior.


P03 uses SQLite schema v2 to persist Account verification timestamp and safe error summary. Provider secrets remain outside SQLite.
