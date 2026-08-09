# Configuration

Invio `v1.0.0.1.16` separates Settings, durable operational data, provider registry state, and protected provider credentials.

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
- Customer Lists and ordered customer records (email, optional name/country);
- Invoice Templates/items/terms;
- Tasks, account selection, counters/status/message;
- account reservations;
- P05 immutable Task execution snapshots (ordered recipients, copied template/items/terms, provider ID and assignment strategy).

Typical database filename: `domain.sqlite3` in the same per-user Invio directory as `settings.json`.

The database uses schema version `4`, foreign keys, transactional writes, WAL journaling, and `synchronous=FULL`. Schema v3 added optional customer `name` and `country`; schema v4 adds immutable Task execution-snapshot tables. Corrupt, newer, partial, or unrecognized storage is not silently replaced.

Migration backups use SQLite live-backup semantics. The `v1.0.0.1.14` close-before-replace correction remains active for the v3-to-v4 P05 migration, preventing Windows from self-locking the temporary backup file during startup.

## Protected Credentials

Provider credential values are stored with Python `keyring` through approved OS-protected backend families only. SQLite stores only `account:<account-id>` references. Invio has no plaintext credential fallback.

If the protected credential entry/backend is unavailable at startup, the Account metadata is still restored for visibility but its runtime status becomes **Not Verified**, so P01 Task gates block execution.

## Provider Registry

Bundled manifests remain under `providers/packages/`; installed manifests remain under ignored `providers/registry/`. P02 does not change ProviderManager behavior.


P03 uses SQLite schema v2 to persist Account verification timestamp and safe error summary. Provider secrets remain outside SQLite.
