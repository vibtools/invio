## v1.0.0.1.48.4 Installation Note

Installation requirements and commands are unchanged. The compact New Task modal does not add dependencies or configuration steps.

## Upgrade to v1.0.0.1.48.3

Apply the replace-ready v1.48.3 delta directly over the exact `Invio_v1.0.0.1.48.02_CL_FIx_Baseline.zip` project root. No runtime dependency, database schema, provider configuration or user-data migration is introduced. The update changes CI/repository-contract files, release identity markers, directly related tests and synchronized documentation only. After replacement, commit/push the tracked files and use a non-tag GitHub Actions run to confirm the full Windows wheel/Nuitka/WiX/artifact pipeline before creating the exact `v1.0.0.1.48.3` tag.

## v1.0.0.1.47.0 Distribution Note

No installation or dependency change is introduced. The Windows/wheel resource inventory now includes the packaged navigation, window-control and dropdown SVG assets required by the approved design system.

# Installation

## v1.0.0.1.45.0 note

No installation, dependency, provider-bundle, database or credential-store change is introduced. This candidate is a Providers Page presentation/lifecycle hotfix only.

## v1.0.0.1.44.0 note

Installation/runtime requirements are unchanged from v1.0.0.1.43.0. This candidate changes only static intro/subtitle presentation.

## Upgrade to v1.0.0.1.43.0

Apply the replace-ready v1.43.0 delta over the exact owner-frozen `v1.0.0.1.42.0` project root. The update adds only UI source/tests/docs plus `assets/icons/search.svg`; dependencies and SQLite schema remain unchanged. Rebuild the wheel/portable/MSI normally after owner visual acceptance and green non-tag CI.


## Upgrade to v1.0.0.1.42.0

Apply the replace-ready delta only to an exact `v1.0.0.1.41.1` project root. No dependency, database, provider-registry, credential or settings-file migration is required. Existing local Settings values remain compatible.


## v1.0.0.1.41.1 provider logo resources

The Providers Page logo assets are packaged with Invio under `assets/icons/providers/`. No separate icon download or runtime network access is required. Wheel and Windows portable release audits require all four current provider-logo files.

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

## Upgrade to v1.0.0.1.41.1

Apply the replace-ready v1.41.1 delta only over the exact owner-frozen `v1.0.0.1.41` project root. No dependency, database-schema, credential-store, provider-registry or configuration migration is required. The delta adds only Providers-page UI/resources plus directly required packaging/tests/docs/version synchronization.

## Upgrade to v1.0.0.1.41

`v1.0.0.1.41` is a Providers-page UI/UX-only candidate over the `v1.0.0.1.40.2` production baseline. No dependency, database-schema, credential-store, provider-registry or configuration migration is required. Apply the replace-ready delta over the exact v1.0.0.1.40.2 project root; existing provider installation/account/task data remains untouched.

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


## Windows portable and MSI distribution (v1.0.0.1.38)

The approved GitHub Windows build creates two end-user forms from the same Nuitka OneDir payload:

- `Invio_v1.0.0.1.38_windows_x64_portable.zip` — extract the `Invio/` folder to a writable location and launch `Invio.exe`.
- `Invio_v1.0.0.1.38_windows_x64_setup.msi` — per-user install under `%LOCALAPPDATA%\Vib Tools\Invio`, requiring no system-wide Program Files write access.

The wheel remains available for Python/packaging verification and advanced Python-environment installation. End users do not need Python when using the Nuitka portable/MSI distributions.

GitHub release tags must exactly match the application version, e.g. `v1.0.0.1.38`. A tag mismatch fails before release publication. Build outputs are currently unsigned; Windows may therefore show normal unsigned-application reputation warnings. No code-signing capability is included in this approved scope.

> **Portable naming:** the portable ZIP means no MSI installation is required. It does not relocate Invio's existing per-user SQLite/settings/keyring state into the executable folder.


### v1.0.0.1.38 release inventory note

The supported Windows release payloads remain the versioned portable ZIP and per-user MSI, with the Python wheel and `SHA256SUMS.txt` retained for packaging verification. WiX debug-symbol `.wixpdb` files are build diagnostics and are intentionally not produced in the release directory by v1.38.
## v1.0.0.1.39 pre-release validation note

For the current compiled-credential correction, keep `v1.0.0.1.38` as the installed/released reference and test the v1.39 delta from an exact v1.38 **source root** first. Use a fresh Windows Python 3.12 virtual environment, install the unchanged `requirements.txt`, and run `python main.py`. Do not tag or publish v1.39 until source/live Account persistence and a later non-tagged Windows build artifact are both accepted.

## v1.0.0.1.40 application icon prerequisite

The source/runtime/build contract now consumes owner branding from `assets/icons/app.png` and `assets/icons/app.ico`. Place both files at those exact paths before icon verification or a Windows build. The Windows Nuitka build specifically requires `assets/icons/app.ico`; the patch intentionally does not fabricate or replace owner branding assets.

## v1.0.0.1.40.1 Windows build correction

The application/runtime dependency set is unchanged. For the Windows CI build, pinned Nuitka 4.1.3 now uses its own standard `keyring` package configuration; Invio no longer passes the historical duplicate `.github/nuitka-keyring.nuitka-package.config.yml` as a user package config. Explicit keyring package inclusion and compiled protected-credential smoke remain required. Do not publish a tagged build until the non-tagged candidate CI and downloaded portable/MSI acceptance pass.

## v1.0.0.1.40.2 provider credential note

Agiled still uses the existing single protected `API Key` credential field. A successful Agiled API Test requires the key to be valid for the current Agiled Public API and the `GET https://api.agiled.ai/public/v1/me` scope. No Agiled base URL is user-configured in Invio; the verified endpoint is fixed by the built-in adapter. Agiled Task sending remains unavailable in this candidate.


## Bundled Odoo external provider — v1.0.0.1.40.2 production release

The production release includes the validated Odoo Provider v1.0.0 under `providers/plugins/odoo/`. It is deliberately not auto-installed because P13 requires explicit trusted-code approval for executable external adapters. After Invio is installed, use **Providers → Load Provider** and select the bundled `provider.json`, then approve the sibling `adapter.py` only if the bundle is trusted.
