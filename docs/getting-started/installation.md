# Installation

## Requirements

- Python 3.12+
- Windows, Linux, or macOS with a desktop environment
- an available approved OS-protected credential service for saving provider credentials

## Install dependencies

```bash
python -m pip install -r requirements.txt
```

`v1.0.0.1.8` adds `keyring>=25.7,<26`. Invio uses it only for OS-protected provider credentials. No provider SDK is added; Stripe/Refrens HTTP execution continues to use Python's standard library.

On Linux, a usable Secret Service/libsecret or KWallet environment must be available for account credentials. Invio does not enable an insecure/plaintext keyring fallback.

## Start Invio

```bash
python main.py
```

On first P02 launch, Invio creates the version-1 operational SQLite schema in the same per-user application directory used by Settings. An existing empty version-0 database is backed up before migration.

## Upgrade from v1.0.0.1.7

The previous release did not persist Accounts, Customer Lists, Invoice Templates, Tasks, or reservations. Therefore there is no prior domain-state file to migrate from `v1.0.0.1.7`; only data created after P02 is durable. Existing `settings.json` and provider registry behavior are preserved.

## Upgrade to v1.0.0.1.14

`v1.0.0.1.14` is a replace-ready runtime/storage hotfix and does not change dependencies or SQLite schema version. On Windows it explicitly closes the temporary SQLite migration-backup connection before the backup file is atomically renamed, preventing the `WinError 32` startup failure seen in earlier builds during supported schema migration. Existing `domain.sqlite3`, protected credentials, Settings and provider registry state must be left in place; no manual database deletion is required.

## Upgrade to v1.0.0.1.15

`v1.0.0.1.15` advances operational storage from schema v3 to schema v4. Keep the existing `domain.sqlite3`, protected credentials, Settings, and provider registry files in place. Invio creates a WAL-aware pre-migration backup using the Windows-safe close-before-replace path from `v1.0.0.1.14`, then creates the immutable Task snapshot tables.

Tasks created before P05 are preserved but marked `LegacyUnavailable`; their historical creation-time recipients/template cannot be reconstructed safely. They remain visible/closable but cannot Start/Retry. New Tasks created after upgrade receive durable immutable execution snapshots. No dependency change is required.
