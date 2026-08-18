# Invio v1.0.0.1.49.9 — Patch Manifest

## Parent baseline

- Application: `Invio v1.0.0.1.49.8`
- Git commit: `c9712add5ac6b4b41b3c1bc999a21e1767bc3822`
- Uploaded baseline ZIP SHA-256: `9ff5ef92d3743f523d3ccb7c9dd37f8264ccad4cff998944f38f8899e7c3cb54`

## Scope

Windows Phase-3 migration regression-fixture / GitHub CI correction only, plus version and required release/documentation records.

Confirmed failing remote evidence: GitHub Actions run `32097949119`, Windows job `95592816900`. Linux passed. Windows reached the 629-test full regression and failed only when `Phase3SendingControlStorageTests.test_schema_v5_migrates_to_v6_with_baseline_safe_defaults` left its own SQLite fixture connection open through `TemporaryDirectory` cleanup, causing `WinError 32`.

## Correction

- Replace both `with sqlite3.connect(db_path)` blocks in the Phase-3 migration fixture with `closing(sqlite3.connect(db_path))` so Windows releases the file handles before temp-directory cleanup.
- Keep production `DomainStore` migration/connection logic unchanged; it already closes operational connections in `finally`.
- Keep SQLite schema `v6` and all Phase-3 sending-control semantics unchanged.
- Synchronize application `1.0.0.1.49.9`, PE `1.0.1.4909`, MSI `1.1.4909`, wheel `1.0.0.1.49.9` and active release records.

## Frozen boundaries

No functional change to providers/Odoo, Phase-1 TLS, Phase-2 fatal-limit circuit breaker, Phase-3 timeout/attempt/delay/rate semantics, WorkerManager/QThread, Task state machine, delivery ledger, CredentialStore, OAuth/Easy Onboarding, IVX, customer/invoice behavior, dependencies, non-Settings UI/UX, or Phase 4 Dynamic Tags.

## Delta inventory

- Added: 5
- Modified: 22
- Removed: 0
- Total: 27

The Replace-Ready delta is a direct project-root overlay with no wrapper directory. `.git`, `__pycache__`, `.pyc`, generated build metadata and unrelated local files are excluded.

## Release gate

Do not tag/release until a new non-tag GitHub Actions run passes `test`, `windows-build`, the Windows P14 distribution audit and artifact upload.
