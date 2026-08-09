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
