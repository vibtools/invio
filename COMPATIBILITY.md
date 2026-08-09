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
