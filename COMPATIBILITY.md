# Compatibility

Target runtime: Python 3.12+ with PySide6 on Windows, Linux, and macOS desktop environments. Primary desktop validation target is Windows.

P02 adds `keyring>=25.7,<26` for protected credentials. Invio accepts only approved OS-protected keyring backend families: Windows Credential Locker, macOS Keychain, Freedesktop Secret Service/libsecret, or KWallet. If no approved backend is available, provider credentials fail closed and are not written to plaintext storage.

Linux keyring availability depends on the desktop/system secret-service configuration. No fallback file keyring is bundled or enabled by Invio.


## v1.0.0.1.11 P03 Verification Correction

No schema version, dependency, provider ID, credential field, UI page, Task model, Customer model, Invoice Template model, ProviderManager API, or WorkerManager architecture changes are introduced. SQLite remains schema v2. Migration backup creation now uses SQLite's live backup API so committed WAL state is included. Missing/unreadable protected credentials are durably recorded as `Not Verified`, and Account Edit uses a fail-closed durable safety marker across the SQLite/keyring boundary.

## v1.0.0.1.10 P03

Existing schema-v1 operational databases migrate transactionally to schema v2 with a pre-migration backup. Existing provider IDs, credential field keys, Account IDs, Task IDs, Customer Lists, Invoice Templates, WorkerManager behavior, and supported desktop platforms are unchanged. P03 adds no dependency.

## v1.0.0.1.12 P04

No platform, Python, PySide6, openpyxl, keyring, provider ID, credential field, WorkerManager architecture, or dependency requirement changes are introduced. SQLite advances from schema v2 to v3 by adding optional customer `name` and `country` columns to the existing ordered `customer_emails` table. Existing email-only rows migrate with blank metadata, so Stripe-compatible legacy lists remain usable without conversion.

## v1.0.0.1.13 P04 Verification Correction

No platform, Python, PySide6, openpyxl, keyring, provider ID, credential field, WorkerManager/ProviderManager architecture, schema version, or dependency requirement changes are introduced. The pre-P04 `CustomerList.emails` attribute was a mutable `list`; v1.0.0.1.13 restores in-place list mutation compatibility while keeping customer records authoritative. Structured/legacy import formats and Stripe email-only execution remain unchanged.
## v1.0.0.1.14 Windows Operational Storage Runtime Hotfix

No platform target, Python/PySide6/openpyxl/keyring requirement, SQLite schema version, provider ID, credential field, UI page, WorkerManager/ProviderManager architecture or provider execution contract changes are introduced. The migration backup destination connection is now explicitly closed before the temporary backup file is atomically replaced. This removes the Windows file-handle self-lock that could raise `WinError 32` during schema migration. SQLite remains schema v3 and continues to use the live backup API so committed WAL state is included.


## v1.0.0.1.15 P05

No Python, PySide6, openpyxl, keyring, provider ID, credential-field, ProviderManager, WorkerManager, packaged-provider, or platform-target change is introduced. SQLite advances from schema v3 to v4 with WAL-aware/Windows-safe pre-migration backup. Existing v3 Tasks are preserved but marked `LegacyUnavailable` because their historical creation-time recipients/template were never persisted; Invio does not guess those inputs. New Tasks persist immutable execution snapshots and continue using existing Stripe/provider send semantics.
## v1.0.0.1.16 P05 Verification Correction

No platform, Python, PySide6, openpyxl, keyring, provider ID, credential field, ProviderManager, WorkerManager, provider manifest or dependency change is introduced. SQLite remains schema v4. The release only hardens P05 snapshot creation/progress/total consistency and updates release metadata/documentation.

## v1.0.0.1.17 P06 Compatibility

P06 introduces no Python/platform/dependency/SQLite-schema change. Existing `ProviderManager`, `WorkerManager`, protected credential store, P05 Task snapshot storage, and external `register_task_runner(provider_id, runner)` API remain compatible. Packaged provider IDs are now reserved against external manifest replacement, and Refrens credential transport is restricted to the canonical HTTPS API origin before authentication.

## v1.0.0.1.18 P06 Verification Compatibility

No Python/platform/dependency/SQLite-schema/provider-manifest/WorkerManager/P05-snapshot change is introduced. Existing valid packaged provider installations behave the same. P06 now fails closed when a packaged manifest itself diverges from the built-in executable contract, when Task preflight receives Accounts different from the frozen assignment, or when Refrens uses a non-canonical explicit-port URL. Region-specific three-decimal Stripe currencies remain intentionally unsupported by the current Invio minor-unit sender.

## v1.0.0.1.19 P07 Compatibility

- Existing Task status names remain `Ready`, `Running`, `Paused`, `Stopping`, `Stopped`, `Failed`, and `Completed`; P07 formalizes their transitions rather than renaming them.
- Existing button inventory and page layout remain; the existing Start button displays **Resume Remaining** for a safe Stopped continuation.
- Existing `register_task_runner(provider_id, runner)` remains source-compatible for first runs. Retry/Resume continuation is fail-closed for injected runners because the existing callback contract cannot expose an exact safe recipient subset.
- SQLite remains schema v4; no recipient delivery ledger is introduced. Exact failed/pending identities are current-session memory only, so restart continuation is intentionally unavailable until P10.
- P05 immutable snapshot format, P06 preflight, Stripe/Refrens provider-send contracts, account reservation rules, and dependency versions remain unchanged.

## v1.0.0.1.20 P07 Verification Compatibility

- Existing Task statuses, button inventory, First Run / Resume Remaining / Retry Failed semantics and `Task.id` identity remain unchanged.
- WorkerManager remains source/behavior compatible and still owns one QThread per active Task; the controller now refuses Pause/Resume/Stop once that worker is no longer active.
- A late `Completed` signal that races with an accepted Pause/Stop is resolved to existing `Stopped`, not to a new status or an expanded transition.
- Safe empty continuation sets remain valid current-session knowledge but expose no send action because there are no unresolved recipients.
- No SQLite migration, provider contract, dependency, P08 network-reliability behavior or P10 durable recipient ledger is introduced.

## v1.0.0.1.21 Provider Compatibility

- Stripe: existing API Test and invoice create/finalize/send runtime preserved.
- Refrens: existing API Test preserved; normal Task sending remains blocked until P11.
- Agiled: package/credential entry supported, but API Test and Task execution intentionally unavailable until the current base URL, authentication and invoice-send contract are authoritative.
- Existing externally loaded manifest + injected-runner compatibility is preserved. No arbitrary external Python adapter loading is introduced.
- SQLite schema remains v4; dependencies and supported Python/Qt ranges are unchanged.

## v1.0.0.1.22 Provider Verification Compatibility

- No provider credential schema, packaged provider ID, API request payload, invoice-send sequence, WorkerManager interface, SQLite schema, dependency, page inventory, Task state, or external injected-runner API changes are introduced.
- Stripe and Refrens runtime behavior remains the same as `v1.0.0.1.21` except for the release User-Agent marker.
- Agiled remains package/install compatible but non-executable; API Test and Task execution still fail before network transport.
- The release adds verification tests and documentation only beyond required version markers.

## v1.0.0.1.23 P08 Compatibility

P08 preserves the existing Python 3.12, PySide6 6.7-<7, `urllib`, keyring and openpyxl technology set. No dependency or SQLite schema change is introduced. One task-owned QThread remains the concurrency boundary. Existing Stripe/Refrens/Agiled provider contracts are unchanged; Agiled remains fail-closed and Refrens normal Task sending remains P11-gated.


## v1.0.0.1.24 P08 Verification-Correction Compatibility

`v1.0.0.1.24` preserves the `v1.0.0.1.23` Python 3.12+, PySide6 6.7-<7, standard-library `urllib`, keyring and openpyxl technology set. The correction only extends P08 transient-disconnect classification for incomplete HTTP bodies and TLS EOF/clean-close conditions and preserves HTTP status/Retry-After when an error body is truncated. No API/provider payload, schema, dependency, page, QThread boundary, account assignment, idempotency, or P09+ compatibility contract changes.


## v1.0.0.1.26 P09 CI Verification Compatibility

`v1.0.0.1.26` changes no provider API, scheduling policy, Task state, WorkerManager interface, SQLite schema, dependency, Settings key, page/layout, account assignment, Stripe idempotency, Refrens gate, Agiled fail-close or plugin contract. The only behavioral correction is to the repository test boundary: public CI no longer requires intentionally Git-ignored private `project/` files.

## v1.0.0.1.27 P10 Compatibility

SQLite advances from schema v4 to schema v5 through the existing backup/transaction migration path; all pre-existing domain and P05 snapshot tables remain. P10 adds exactly three non-secret delivery-ledger tables and no dependency/provider manifest/UI page change. `Task.id`, P05 snapshot format, P07 actions/status names, P08 retry count and P09 scheduling/account-failover rules remain compatible. Pre-P10 non-pristine Tasks are preserved without fabricated ledger history and continue fail-closed where exact continuation cannot be proven.

## v1.0.0.1.28 P10 Verification Compatibility

No storage schema, table, provider API, dependency, page, Task action/status, WorkerManager or Stripe business-flow compatibility boundary changes from `v1.0.0.1.27`. Existing schema-v5 databases remain directly compatible. The correction only tightens how existing P10 operation history is interpreted: exact matching successful stage/idempotency evidence resolves ambiguity, while unmatched historical mutating ambiguity remains fail-closed/observable.

## v1.0.0.1.29 P11 compatibility

The P11 implementation candidate keeps Python/PySide6/keyring/openpyxl requirements unchanged, preserves SQLite schema v5, one Task = one QThread, the existing Task state machine and customer model, and does not alter Stripe or Agiled packaged provider manifests. Refrens Task execution requires explicit email/name/country, rejects India under the current model because GST State is unavailable, and uses only the canonical `https://api.refrens.com` endpoint. P11 remains live-acceptance pending.

## v1.0.0.1.30 P12 compatibility

No dependency, provider ID, credential field, Task/customer/template model, provider manifest, scheduling policy or SQLite schema change is introduced. SQLite remains schema v5 with exactly three P10 delivery-ledger tables. Existing task CSV remains available; recipient CSV and structured logs are additive. WorkerManager retains one QThread per Task and plain `TaskExecutionContext.log` compatibility while adding optional structured log metadata transport.


## v1.0.0.1.31 P12 Verification-Correction Compatibility

No dependency, Python/PySide6/keyring/openpyxl range, provider manifest, provider API request, Task/customer/template model, scheduling policy, WorkerManager interface, page inventory or SQLite schema changes from v1.0.0.1.30. Existing schema-v5 databases remain directly compatible. The correction only strengthens non-persistent/durable diagnostic redaction and ledger-backed report interpretation.

## v1.0.0.1.32 P13 Compatibility

- Existing manifest-only external providers remain installable and visible but are explicitly non-executable until a compatible adapter is supplied.
- Existing packaged Stripe/Refrens adapters remain on the static built-in registry; Agiled remains fail-closed.
- Existing `register_task_runner()` injection API remains available with its historical continuation limitations.
- Existing SQLite schema v5 and P10 ledger tables are unchanged.
- External adapter code is trusted in-process Python and receives no automatic dependency installation or remote download support.

## v1.0.0.1.33 P13 Verification-Correction Compatibility

- External adapter interface remains version 1; existing valid v1.0.0.1.32 adapter bundles remain compatible.
- Manifest-only, Missing, Incompatible and Executable runtime states are unchanged.
- Packaged Stripe/Refrens adapters and Agiled fail-close are unchanged.
- Provider Task/API Test execution, P06/P08/P10 semantics, SQLite schema v5 and the three P10 ledger tables are unchanged.
- External uninstall now uses rollback-safe registry moves; successful uninstall remains user-visible behavior-compatible while partial filesystem failure leaves the original provider installed instead of half-uninstalled.
- No dependency, page, Settings, provider manifest, Task/customer/template or WorkerManager interface changes are introduced.


## v1.0.0.1.34 P14 candidate compatibility

- Python/runtime dependency ranges are unchanged.
- SQLite remains schema v5 with the same three P10 ledger tables.
- Packaged Stripe/Refrens/Agiled manifests are byte-unchanged; the wheel now includes them and the existing checkmark asset.
- Existing source-checkout layout remains supported. `src/core/paths.py` resolves the same resource root after clean wheel installation.
- External adapter interface remains version 1 and provider business flows are unchanged.
- No PyInstaller/Briefcase/MSI technology or runtime dependency is introduced.
- Production certification remains pending until live-provider and native-Windows gates execute successfully.


## v1.0.0.1.35 P14 distribution compatibility

- Python/runtime dependency ranges and `requirements.txt` are unchanged; Nuitka and WiX are CI build-only tools.
- Existing source-checkout and wheel execution remain supported. `application_root()` adds only an exact executable-directory fallback when the four frozen runtime resources exist there.
- Nuitka output is OneDir, not onefile; no PyInstaller or Briefcase path is added.
- MSI is per-user under LocalAppData to preserve the existing writable provider registry and P13 Load/Install/Uninstall workflow without UAC.
- SQLite schema v5, the three P10 ledger tables, one-Task/one-QThread ownership, provider API/send behavior, P13 external adapter interface v1, Settings, Reports/Logs and page inventory are unchanged.
- The wheel remains supported and is included in CI/release output as a Python packaging/certification artifact.
- P11/P14 certification status is unchanged until live provider and executed Windows evidence passes.


## v1.0.0.1.36 P14 CI Verification Compatibility

No platform target, Python/PySide6/openpyxl/keyring runtime requirement, provider ID/manifest/API/send contract, SQLite schema, P10 ledger table, P13 interface, WorkerManager, Task/customer/template model, UI page, Settings, Reports/Logs or business workflow changes are introduced. The release changes only Git publication of the existing `scripts/build` helper source, deterministic SQLite handle closure on exceptional/test cleanup paths, current version metadata, regression tests and synchronized documentation. Nuitka `4.1.3` and WiX `6.0.2` remain CI build-only tools.


## v1.0.0.1.37 P14 WiX Verification Compatibility

No supported platform, Python/PySide6/openpyxl/keyring range, runtime dependency, provider ID/manifest/API/send contract, SQLite schema/table, P10 ledger behavior, P13 interface, WorkerManager/Task/customer/template model, UI page, Settings, Reports/Logs, Nuitka configuration, WiX package pin or MSI layout changes are introduced. The workflow only treats an optional WiX `+build-metadata` suffix as informational when checking that the installed canonical tool version is the pinned `6.0.2`; mismatched core versions still fail closed.
