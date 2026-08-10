# Invio Project Structure

```text
.
├── .github/                  GitHub metadata and CI
├── assets/                   Static UI resources
├── config/                   Runtime configuration location
├── data/                     Runtime/import/export data location
├── docs/                     Public user/developer documentation
├── examples/                 Public examples
├── project/                  PRIVATE development material (Git ignored)
│   ├── planning/             Production roadmap, phase ledger and protocol
│   ├── research/             Forensic/readiness/implementation records
│   └── specifications/       Baseline/scope freeze records
├── providers/
│   ├── packages/             Bundled Stripe/Refrens/Agiled provider manifests
│   └── registry/             Locally installed provider manifests (Git ignored)
├── scripts/
│   ├── build/                Tracked P14 Windows distribution/release helpers
│   └── test/                 Repository audit and certification helpers
├── src/
│   ├── accounts/             Provider-account models
│   ├── core/
│   │   ├── provider_manager/ Provider manifest validation/install/load/uninstall
│   │   ├── provider_runtime/ Internal packaged-provider adapter registry, API runtime and P06 preflight contracts
│   │   ├── settings/         Persistent non-sensitive preferences
│   │   ├── state/            Domain invariants plus P02 persistence coordination
│   │   ├── storage/          SQLite domain store + protected credential store + schema-v5 delivery ledger persistence
│   │   └── worker_manager/   One QThread per active task
│   ├── customers/            Customer-list model and email importers
│   ├── invoices/templates/   Invoice template/currency models
│   ├── tasks/                Task model, immutable snapshots and P10 delivery-ledger contracts
│   └── ui/                   Vib Tools shell, dialogs, Dashboard and pages
├── tests/                    Unit/contract tests, including provider-adapter, P01-P07 storage/snapshot/preflight/state regressions
├── main.py
├── requirements.txt
└── pyproject.toml
```

## P02 Runtime Data Flow

1. `main.py` calls `src.app.main()`.
2. `MainWindow` loads Settings, opens `domain.sqlite3`, validates/migrates its schema, restores protected account credentials, and reconstructs `AppState`.
3. Existing pages read the restored `AppState`; no new P02 page is added.
4. Approved state mutations are committed transactionally to SQLite before becoming durable application state.
5. Account secrets are stored through `CredentialStore` in the approved OS keyring; SQLite stores only a credential reference.
6. Existing provider visibility, ProviderRuntime, and one-QThread-per-active-Task WorkerManager behavior remain unchanged.
7. Task status/progress signals update both `AppState` and durable task metadata. A persistence failure requests Task stop rather than silently continuing without durable state.

## Privacy

`project/` remains private internal material. Provider secrets are excluded from the operational database and Settings JSON.

## v1.0.0.1.9 P02 Verification Correction

No directory or module is renamed/reorganized. The corrective release changes only P02 recovery/failure-path logic, release tests/metadata, and synchronized documentation.


## v1.0.0.1.10 P03 Account Lifecycle

P03 extends the existing `Account` model and SQLite `accounts` table with verification-health metadata, adds lifecycle operations in `AppState`/`DomainStore`, and adds Edit/Re-test/Delete controls to the existing Accounts page. No new UI page or dependency is introduced.


## v1.0.0.1.11 P03 Verification Correction

No production folder/module/page/dependency structure changes are introduced. The corrective delta only hardens existing `AppState` Account Edit persistence and `DomainStore` migration/startup recovery behavior, adds regression tests, and synchronizes release/audit documentation.


## v1.0.0.1.12 P04 Customer Data Upgrade

P04 keeps the existing file/folder architecture. `src/customers/models/customer_list.py` now defines `CustomerRecord`; `src/customers/importers/email_importer.py` contains both the preserved email-only importer and the structured customer importer. Existing storage/runtime/UI modules are extended in place; no new application page or dependency is introduced.

## v1.0.0.1.13 P04 Verification Correction

No folder/module architecture is added or renamed. The correction stays inside the existing P04 customer model/import/state/runtime/UI integration files plus tests/release documentation. `src/ui/pages/dashboard_page.py` is restored to its pre-P04 content because its label change was outside the approved P04 UI file scope.
## v1.0.0.1.14 Runtime/Storage Hotfix

No folder or module is renamed/reorganized. The hotfix changes only the existing `DomainStore` migration-backup handle lifecycle, regression/release tests, version metadata and synchronized documentation/private forensic records. No new runtime package, page, provider adapter, dependency or database table is introduced.


## v1.0.0.1.15 P05 Immutable Task Snapshot

No new top-level folder, application page, dependency, provider adapter or worker subsystem is introduced. The existing `src/tasks/models/task.py`, `AppState`, `DomainStore`, `ProviderRuntime`, Tasks page and tests are extended in place. SQLite schema v4 adds Task execution-snapshot tables; the existing Task/account/customer/template tables remain.
## v1.0.0.1.16 P05 Verification Correction

No folder, module, page, provider adapter, dependency, worker subsystem or database table is added/renamed. The correction stays inside the existing `AppState`/`DomainStore` P05 consistency boundary plus regression tests and synchronized release documentation. SQLite remains schema v4.

## v1.0.0.1.17 P06 Provider Preflight

P06 adds one focused module, `src/core/provider_runtime/preflight.py`, inside the existing provider-runtime package. ProviderManager is extended in place only for packaged-manifest lookup and reserved packaged-ID protection; MainWindow and the existing Providers page integrate preflight/capability display without adding a new application page. SQLite remains schema v4 and no storage table, worker subsystem, provider manifest, dependency, or top-level folder is added.

## v1.0.0.1.18 P06 Verification Note

No folder/module/page is renamed or reorganized. Corrections remain in the existing ProviderManager/ProviderRuntime/MainWindow/ProvidersPage P06 surfaces plus regression tests and synchronized documentation. SQLite remains schema v4.

## v1.0.0.1.19 P07 State-Machine Note

P07 adds `src/tasks/state_machine.py` inside the existing Task package. No top-level folder, UI page, database table, worker subsystem, or provider adapter is added. Existing Task, AppState, ProviderRuntime, DomainStore, MainWindow and Tasks page modules are extended in place. SQLite remains schema v4 and WorkerManager remains one QThread per active Task.

## v1.0.0.1.20 P07 verification note

No folder, page, database table, worker subsystem or provider adapter is added. The correction stays inside the existing P07 `src/tasks/state_machine.py` and `MainWindow` integration surfaces plus regression tests/release documentation. WorkerManager itself and SQLite schema v4 remain unchanged.

## v1.0.0.1.21 Provider Adapter Foundation

`src/core/provider_runtime/adapters.py` is the only new runtime module. It registers packaged execution contracts for Stripe, Refrens and Agiled. `ProviderManager` remains in its existing module and remains manifest-only. `providers/packages/agiled/provider.json` is the only new provider package. No folder/module is renamed or reorganized.

## v1.0.0.1.22 Verification Structure Note

No application folder/module architecture is added, removed, renamed, or reorganized. The existing `src/core/provider_runtime/adapters.py` and `providers/packages/agiled/provider.json` from `v1.0.0.1.21` are retained unchanged. This release adds only verification/release records and test coverage plus version markers.

## v1.0.0.1.23 P08 Structure Note

P08 changes no folder architecture and adds no runtime package. Reliability logic remains in `src/core/provider_runtime/runtime.py`, task-thread lifecycle remains in `src/core/worker_manager/manager.py`, and shutdown coordination remains in `src/ui/main_window.py`. `tests/test_p08_reliability.py` adds P08 regression coverage. No UI page, schema package or dependency is added.


## v1.0.0.1.24 P08 Verification-Correction Structure Note

No folder, runtime package, UI page, schema module, dependency or architecture boundary is added/removed/renamed. The transport correction remains in `src/core/provider_runtime/runtime.py`; regression coverage extends `tests/test_p08_reliability.py` and repository consistency checks. New files are documentation/release/forensic records only.


## v1.0.0.1.25 P09 Structure Note

P09 adds no runtime package, page, schema package, worker subsystem or dependency. Provider scheduling policy remains in `src/core/provider_runtime/adapters.py`; rate/health/failover behavior remains in `src/core/provider_runtime/runtime.py`; successful account re-verification clears runtime-only health through the existing `src/ui/main_window.py` account lifecycle. `tests/test_p09_scheduling.py` adds P09 regression coverage.


## v1.0.0.1.26 CI Verification Structure Note

No runtime folder/module/page structure is added, removed, renamed, or reorganized. `project/` remains intentionally Git-ignored private development material. Public CI repository-contract tests now depend only on tracked public records, while private project records are checked only when the full private baseline is present.

## v1.0.0.1.27 P10 Structure Note

P10 adds one focused runtime model module, `src/tasks/delivery_ledger.py`, inside the existing Task package. `DomainStore`, `ProviderRuntime` and MainWindow are extended in place; SQLite schema v5 adds exactly three delivery-ledger tables. No top-level folder, UI page, WorkerManager subsystem, provider package or dependency is added or renamed.

## v1.0.0.1.28 P10 Verification-Correction Structure Note

No folder/module/page/schema/dependency structure is added, removed, renamed or reorganized. The P10 correction remains inside the existing `DomainStore` durable-summary/reconciliation boundary plus tests and release/documentation records. `src/tasks/delivery_ledger.py`, the three schema-v5 P10 tables, WorkerManager and UI page inventory are unchanged.

## v1.0.0.1.29 P11 Structure Note

P11 adds no application folder, runtime package, UI page, customer field, database table, dependency or worker subsystem. Refrens adapter capability/scheduling stays in `src/core/provider_runtime/adapters.py`; provider/customer/host preflight stays in `preflight.py`; the batch/auth/invoice Task flow stays in `runtime.py`; existing schema-v5 ledger interpretation is extended in `src/tasks/delivery_ledger.py` and `src/core/storage/domain_store.py`; existing MainWindow action messaging prevents uncertain-only Refrens automatic Resume. `tests/test_p11_refrens_task.py` adds focused regression coverage.

## v1.0.0.1.30 P12 Structure Note

P12 adds `src/core/observability.py` as a focused non-persistent observability/privacy/export helper. Existing Reports and Live Logs pages are extended in place; no new application page, database table, provider package, Settings control or dependency is added.


## v1.0.0.1.31 P12 verification correction

No folders or runtime modules are renamed/reorganized. `src/core/observability.py` and `src/core/storage/domain_store.py` remain in their existing P12 locations; the correction only tightens their redaction/report interpretation behavior. No new application page, storage table, provider package or dependency is introduced.

## v1.0.0.1.32 P13 external adapter additions

- `src/core/provider_runtime/external.py` — interface-v1 external adapter contract, staged-code validation, discovery, trusted in-process loading and runtime state.
- `providers/registry/<provider>_adapter.py` — runtime-installed executable adapter copy; registry runtime files remain Git-ignored.
- `src/core/storage/domain_store.py` — existing schema-v5 store with a P13-only external-mutation restart interpretation: successful non-idempotent external mutation without provider idempotency evidence remains unresolved if recipient finalization was interrupted; no new table/schema is added.
- `tests/test_p13_external_adapters.py` — P13 executable/manifest-only/fail-closed/API-test/Task/P10 integration and external-code containment contracts.

No new application page, schema table, dependency or provider-package folder was introduced.

## v1.0.0.1.33 P13 verification correction

No folder/module/page/schema/dependency structure is added, removed, renamed or reorganized. The correction remains inside existing `src/core/provider_runtime/external.py` adapter validation and `src/core/provider_manager/manager.py` uninstall lifecycle handling, plus focused tests and release/documentation records. External adapter installation location, provider registry layout and UI page inventory remain unchanged.


## v1.0.0.1.34 P14 packaging/certification additions

- `src/core/paths.py` — deterministic source/install resource-root and required-runtime-resource validation.
- `tests/test_p14_certification.py` — deterministic large-import, injected execution soak, packaging inventory and subprocess crash/recovery gates.
- `scripts/test/p14_wheel_audit.py` — built-wheel content integrity check.
- `scripts/test/p14_windows_smoke.py` — Windows-native installed-wheel PySide6/keyring/resource/page/three-QThread smoke.
- `.github/workflows/ci.yml` — existing Ubuntu audit retained plus Windows/Python-3.12 clean-wheel/native-smoke job.

No new application page, storage schema/table, provider package contract, runtime dependency or installer framework is added.


## v1.0.0.1.35 Windows distribution build additions

- `scripts/build/version_info.py` — canonical five-part release to PE/MSI/tag mapping and tag validation.
- `scripts/build/prepare_windows_distribution.py` — copies Nuitka `main.dist`, renames `main.exe` to `Invio.exe`, verifies frozen runtime resources and creates the versioned portable ZIP.
- `scripts/build/generate_wix_source.py` — deterministic WiX v4-schema source generator for the exact prepared OneDir inventory and per-user LocalAppData installation.
- `scripts/build/finalize_release_checksums.py` — final release SHA-256 inventory.
- `scripts/test/p14_distribution_audit.py` — portable/MSI/wheel/checksum release-payload audit.
- `tests/test_p14_distribution_pipeline.py` — version/resource/portable/WiX/workflow distribution contracts.

No new runtime package tree, application page, provider package, schema table or application dependency is introduced.


## v1.0.0.1.36 P14 CI publication correction

`scripts/build/` is an intentional tracked source directory, not generated root `build/` output. `.gitignore` now explicitly re-includes this approved directory so GitHub Actions receives the v1.35/v1.36 version, portable, WiX and checksum helpers. No application module/folder is renamed or reorganized.


## v1.0.0.1.37 P14 WiX verification correction

No project path, module, package, page or runtime structure changes are introduced. The only executable configuration change is inside `.github/workflows/ci.yml`; the related P14 workflow contract test and version/error-fix records are synchronized in their existing locations.


## v1.0.0.1.38 P14 release inventory correction

No folder/module reorganization is introduced. The existing WiX build still consumes `build/Invio.wxs` and writes the MSI to `dist/release`; v1.38 prevents the default sibling `.wixpdb` from being generated there so the frozen release payload inventory remains exact.
### v1.0.0.1.39 build-only credential packaging contract

- `.github/nuitka-keyring.nuitka-package.config.yml` preserves the existing `keyring` distribution metadata required by compiled backend discovery.
- `.github/workflows/ci.yml` explicitly includes the existing keyring runtime dependency graph and runs protected-credential set/get/delete smoke checks from both the compiled OneDir executable and MSI-installed executable.
- No runtime package/module/folder architecture was renamed or reorganized.

### v1.0.0.1.40 owner icon and customer-default correction resources

- `assets/icons/app.png` — owner-supplied runtime/application icon source.
- `assets/icons/app.ico` — owner-supplied Windows executable icon source; required by the Nuitka build option.
- `docs/api/refrens-runtime.md` — scoped Refrens request mapping note for the v1.40 live correction.
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.40.md` — private root-cause record.

### v1.0.0.1.40.1 correction records

- `docs/release-notes/1.0.0.1.40.1.md` — public candidate release note.
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.40.1.md` — scoped root-cause record.
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.40.1.md` — final verification record.
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.40.1.md` — next-baseline candidate record.
- `project/specifications/P11_LIVE_ACCEPTANCE_PENDING_v1.0.0.1.40.1.md` — mailbox acceptance gate.
- `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.40.1.md` — compiled/release certification gate.

The historical `.github/nuitka-keyring.nuitka-package.config.yml` file is retained under the no-removal baseline rule but is no longer passed to Nuitka because pinned Nuitka 4.1.3 already provides the standard `keyring` package configuration.
