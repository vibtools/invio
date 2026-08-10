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
## Upgrade to v1.0.0.1.16

`v1.0.0.1.16` is a replace-ready P05 verification/correction release. It does not change dependencies or SQLite schema version; schema remains v4. Keep `domain.sqlite3`, protected credentials, Settings and provider registry state in place. The release hardens normal post-P05 Task snapshot creation and captured Task progress/total consistency; no manual database reset is required.

## v1.0.0.1.17 upgrade note

P06 does not change Python, PySide6, openpyxl, keyring, or SQLite storage requirements. Apply the replace-ready delta over the exact v1.0.0.1.16 baseline. Existing packaged provider manifests remain unchanged; external manifests may no longer use the reserved packaged IDs `stripe` or `refrens`.

## Agiled Package Availability

A normal `v1.0.0.1.21` installation includes `providers/packages/agiled/provider.json`. Install it through the existing Providers workflow if you need the provider represented in Invio. Installation alone does not enable Agiled API execution; current API Test/Task execution remains fail-closed pending contract revalidation.

## v1.0.0.1.22 Provider Verification

A normal source installation continues to include the packaged Agiled manifest introduced in `v1.0.0.1.21`. `v1.0.0.1.22` verifies the package install/uninstall round trip without enabling network execution. No installation dependency or platform requirement changes.

## v1.0.0.1.27 schema-v5 upgrade

`v1.0.0.1.27` advances operational storage from schema v4 to schema v5. Keep the existing `domain.sqlite3`, protected credentials, Settings and provider registry in place. Invio uses the same WAL-aware pre-migration backup and transactional migration path, then adds exactly three delivery-ledger tables. Existing Task snapshots and domain rows are preserved; pre-P10 non-pristine Tasks do not receive fabricated historical delivery records.

## v1.0.0.1.28 compatibility note

No schema migration is added after `v1.0.0.1.27`; operational storage remains schema v5. Apply the release normally over `v1.0.0.1.27`. Existing P10 ledger rows are reinterpreted using the corrected uncertainty-reconciliation rules; no ledger data is fabricated or rewritten during installation.


## P14 wheel candidate (v1.0.0.1.34)

The supported candidate packaging format remains the existing setuptools wheel; no standalone EXE/MSI framework is introduced. Build and audit it with:

```bash
python -m pip install --upgrade setuptools wheel
python -m pip wheel . --no-deps --no-build-isolation -w dist
python scripts/test/p14_wheel_audit.py dist/*.whl
```

Install the resulting wheel into a clean Python 3.12 environment with normal dependency resolution. The wheel now includes `src.core.settings`, the packaged Stripe/Refrens/Agiled manifests and `assets/icons/checkmark.svg`. Source checkout execution remains supported. The clean Windows/native PySide6/keyring certification job is defined in GitHub Actions but must actually pass before this candidate can be called production-ready.
