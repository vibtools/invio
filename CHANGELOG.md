# Changelog

## v1.0.0.1.14 - Windows Operational Storage Runtime Hotfix

- Reproduced the reported Windows startup failure in the SQLite pre-migration backup path: the temporary backup database remained open when `Path.replace()` attempted `.bak.tmp -> .bak`, producing `WinError 32`.
- Root cause: Python's `sqlite3.Connection` context-manager protocol does not close the connection on `with` exit; it only commits/rolls back.
- Fixed `DomainStore._create_migration_backup()` to explicitly close the SQLite backup destination before the atomic replacement while preserving SQLite live-backup/WAL semantics.
- Added a regression test that fails if the migration backup destination is still open at replacement time.
- Kept SQLite schema v3, migration order, protected credential storage, ProviderManager, WorkerManager, provider send behavior, customer/import behavior, UI/UX and all P01-P04 features unchanged.
- Production phase progress remains **4/14**; P05 is still the next separately approved phase.

## v1.0.0.1.13 - P04 Verification & Correction

- Re-audited the exact shipped `v1.0.0.1.12` P04 baseline against the approved P04 plan and preserved the 4/14 production-phase status.
- Restored the pre-P04 mutable-list behavior of `CustomerList.emails` while retaining `CustomerRecord` as the authoritative customer representation and preserving existing name/country metadata for unchanged emails.
- Preserved source row numbers through structured/legacy imports so conflicts against existing Customer List metadata are row-numbered instead of email-only.
- Tightened explicit country validation to two ASCII alphabetic characters in both the customer contract and the Refrens payload helper; country is still never guessed.
- Converted malformed customer-workbook/parser failures into the existing caught `ValueError` import boundary so invalid files cannot escape as uncaught parser exceptions.
- Reverted the unrelated Dashboard `Customer Emails` label that P04 had changed outside the approved Customer Lists UI scope.
- Added regression coverage for all corrections; no P05+, Refrens Task enablement, dependency, provider manifest, WorkerManager/ProviderManager, Account/Invoice/Task model, or shared UI design-system change is included.

## v1.0.0.1.12 - P04 Customer Data Contract and Import Upgrade

- Added backward-compatible `CustomerRecord` data with mandatory normalized email plus optional explicit name/country; no name/country inference.
- Added structured CSV/TSV/XLSX/XLSM imports using `email`, `name`, `country` headers while preserving TXT and legacy email-extraction behavior.
- Added row-numbered validation, deterministic duplicate/conflict handling, and safe enrichment of previously blank customer metadata.
- Upgraded durable domain schema from v2 to v3 by adding customer `name`/`country` columns to the existing ordered `customer_emails` table with WAL-aware migration backup.
- Added transactional customer-record persistence and kept `CustomerList.emails`, `AppState.add_emails()` and `import_emails()` backward compatible.
- Upgraded task runtime snapshots to carry customer records while preserving the email-only view and unchanged Stripe customer/send behavior.
- Kept Refrens production Task execution disabled until P11 even when explicit name/country is available.
- Updated Customer Lists UI to display Email, Name and Country and provide bounded import-result diagnostics.
- No new page, dependency, Account/Invoice/Task model redesign, WorkerManager/ProviderManager architecture change, provider manifest change, or P05+ implementation is included.

## v1.0.0.1.11 - P03 Verification & Correction

- Re-audited the exact shipped `v1.0.0.1.10` P03 baseline without introducing P04 functionality.
- Fixed schema-v1 migration backup fidelity: backups now use SQLite live-backup semantics so committed data still present in WAL is included instead of copying only the main database file.
- Fixed credential-loss recovery durability: missing/unreadable protected credentials now persist the Account `Not Verified` state and safe error summary before startup completes, so a later-restored secret cannot silently resurrect a stale durable `Verified` state.
- Hardened Account Edit across SQLite and protected credential storage by staging a durable `Not Verified` safety state before replacing credentials. Successful edits finish as `Verified`; fully successful rollback restores the prior Account; failed compensation remains explicitly non-executable in memory and durable storage.
- Added regression coverage for committed-WAL migration backups, durable credential-loss downgrade, final Account Edit database rollback, and fail-closed compensation failure.
- Updated runtime/release metadata to `v1.0.0.1.11` and synchronized README, roadmap, error-handling, implementation-status, architecture, phase ledger, release notes and private forensic records.
- P03 remains the completed production phase; progress remains **3/14** and P04 is not implemented.
- No provider manifest, provider runtime behavior (except release User-Agent), WorkerManager, ProviderManager, Customer/Invoice/Task model, UI page/design, dependency, credential-storage technology, or SQLite schema-version change is included.

## v1.0.0.1.10 - P03 Account Lifecycle, Verification Health and Provider-Install Consistency

- Added reservation-safe Account **Edit**, **Re-test**, and **Delete** workflows without adding a new page.
- Account Edit keeps provider identity immutable and requires a new successful real API Test before saving metadata/credential changes. Failed candidate verification does not overwrite the saved account.
- Added durable `last_verification_at` and secret-scrubbed `verification_error_summary` metadata with SQLite schema v2 and transactional v1-to-v2 migration backup.
- Added protected-credential compensation for Account update/delete failure paths; no plaintext fallback is introduced.
- Provider uninstall now blocks while a provider Task has an active worker, preserves existing accounts/tasks/reservations/credentials when inactive, and keeps those accounts visible as **Not Installed**.
- Task Start/Retry now fail closed when the Task provider is not currently installed.
- Re-test failure persists `Not Verified`, so existing P01 creation/Start/Retry gates prevent execution with known-invalid credentials.
- If a failed Re-test cannot be persisted, the current process still fails the Account closed to `Not Verified`; a successful Re-test never elevates an Account unless its durable verification-health write commits.
- Corrected the Accounts credential label from the stale `Stored in memory` text to the actual protected-storage state.
- No verification-age expiry, background health polling, WorkerManager change, provider manifest change, invoice/customer/task model redesign, or P04+ feature is included.


## v1.0.0.1.9 - P02 verification corrective release

- Re-audited the exact `Invio_v1.0.0.1.8.zip` P02 baseline against the approved P02 implementation plan.
- Fixed a re-entrant persistence-failure path in `MainWindow._task_persistence_failure()` by recording the task fault before requesting WorkerManager Stop, preventing recursive Stop/status persistence handling while storage remains unavailable.
- Hardened startup domain validation so persisted Task account selections and `account_reservations` must match exactly; missing or conflicting reservation state now fails closed instead of restoring a task/account exclusivity mismatch.
- Added regression coverage for both corrections while retaining every pre-existing test method under the no-removal baseline contract.
- Corrected stale production-roadmap summary metadata that still reported P01-only progress after P02 completion.
- Corrected `vibproject.ygit` P02 dependency/release metadata so the approved `keyring>=25.7,<26` dependency and current release version are represented consistently with `requirements.txt` and `pyproject.toml`.
- No P03-or-later feature, UI redesign, provider behavior, WorkerManager architecture, domain model field, provider manifest, or credential-storage technology change is included.

## 1.0.0.1.8 - 2026-08-08

### P02 - Durable Domain Storage and Protected Credentials
- Added SQLite-backed durable operational storage for Accounts metadata, Customer Lists/emails, Invoice Templates/items/terms, Tasks, task-account ordering, task counters/messages, and account reservations.
- Added schema version 1 with foreign-key enforcement, WAL journal mode, synchronous FULL durability, transactional writes, ordered migration handling, pre-migration backup, future-schema rejection, and corruption-safe startup that does not overwrite an unsafe database.
- Added protected provider credential storage through the owner-approved `keyring` mechanism. Operational SQLite/settings data stores only an opaque credential reference; there is no plaintext-file fallback.
- Added compensation handling so an Account is not committed to memory/database if protected credential persistence or Account metadata persistence fails. If automatic protected-secret cleanup also fails, the failure is surfaced rather than silently ignored.
- Added startup recovery. Persisted Accounts/Lists/Templates/Tasks/Reservations are reconstructed before pages are built; missing/unreadable protected credentials restore the Account as `Not Verified`, and previously active Tasks recover as existing status `Stopped` without automatic sending.
- Integrated transactional persistence into approved AppState mutations and task status/progress updates. An active Task receives a stop request if its operational-state persistence fails.
- Kept P01 verification gates, provider runtimes, provider manifests, one-QThread-per-active-Task WorkerManager architecture, existing pages, and invoice/customer/task domain behavior unchanged outside the P02 persistence boundary.

### Security / dependencies
- Added approved dependency `keyring>=25.7,<26`. Production credential access fails closed unless an approved OS-protected keyring backend is active; injected test backends are used only by deterministic unit tests.
- Provider secret values are not persisted in `domain.sqlite3`, `settings.json`, project files, or P02 logs.

### Verification boundary
- Added P02 storage/migration/rollback/recovery/secret-boundary tests.
- Full native PySide6 launch and native OS-keyring integration are not claimed in the audit container where those runtime packages/backends are unavailable; final live/native certification remains P14.
- P02 does not implement the P10 recipient-level delivery ledger or provider-side crash reconciliation.

## Production Readiness Documentation - 2026-08-08 (runtime remained v1.0.0.1.5)

### Documentation
- Frozen `v1.0.0.1.5` as the production-hardening planning baseline without changing runtime code or the application version.
- Added a forensic production-readiness report covering Provider, Accounts/API Test, Customer Lists, Invoice Templates, Tasks, worker threading, Stripe/Refrens execution, retry, persistence, reports/logs, shutdown safety, and test-certification gaps.
- Added an ordered `G0 + P01-P14` production roadmap, phase completion ledger, and strict production update protocol.
- Added developer-facing Actual Implementation Status and Error Handling inventories so working/partial/missing behavior is updated after every future phase.
- Added the missing `BASELINE_FREEZE_v1.0.0.1.5.md` private baseline record.

### Scope protection
- Documentation-only delta: no file under `src/`, `providers/`, `tests/`, `assets/`, `requirements.txt`, `pyproject.toml`, or runtime metadata is changed.
- No production phase is authorized by these planning documents; each phase still requires a separate explicit owner scope lock.

## 1.0.0.1.7 - 2026-08-08

### P01 verification correction
- Re-audited the exact uploaded `v1.0.0.1.6` full artifact against the approved P01 plan.
- Confirmed the P01 runtime implementation itself is present: real Stripe/Refrens API Test adapters, Stripe Test/Live mode check, dedicated Add Account verification `QThread`, current-session `Verified` state, and New Task/create/start/retry gates.
- Fixed stale shipped Refrens installed-registry metadata that still exposed `1.0.3-ui` and deferred-backend wording even though the bundled provider manifest was already production-clean.
- Corrected the runtime-surface production-marker test to exclude mutable Git-ignored provider registry state while retaining source and bundled-provider checks.
- Corrected the stale release-metadata test name and synchronized release metadata/documentation to `v1.0.0.1.7`.
- Added truthful post-release errata to the `v1.0.0.1.6` verification records: the exact uploaded full artifact initially ran 61/62 tests because of the stale registry state.

### Scope protection
- No P01 provider API behavior, credential field, provider ID/mode, task-worker architecture, invoice-send workflow, Customer List/Invoice Template model, persistence mechanism, page design, or dependency was expanded or replaced.
- Production phase count remains 1/14; P02 remains the next separately approved phase.

## 1.0.0.1.6 - 2026-08-08

### Added / Changed
- Completed production phase **P01 - Real Account API Verification**.
- Wired the existing `ProviderRuntime.test_account()` adapter into Add Account instead of treating required-field presence as a successful API test.
- Added executable API-test capability detection for built-in Stripe/Refrens adapters; providers without a real test adapter now show API Test as unavailable.
- Added a dedicated dialog-owned `QThread` for account API verification so network calls do not execute on the GUI thread.
- Made Stripe API verification mode-aware: Test mode accepts test keys and Live mode accepts live keys before provider requests are attempted.
- Successful API verification now creates the account with current-session status `Verified`; changing provider/mode/credential input invalidates the prior verification.
- Added verified-account gates to New Task selection, backend Task creation, and Start/Retry preparation.
- Added secret-safe API-test success/failure logging and user-facing provider/network failure messages.

### Tests / Verification
- Added provider-runtime tests for executable API-test support, Stripe real permission-request flow, Stripe mode mismatch fail-closed behavior, Refrens auth/access verification, and unsupported adapter rejection.
- Added state regression coverage proving unverified accounts cannot create Tasks.
- Added UI source contracts for threaded Add Account verification and selection/start gating.
- Existing provider sending, Invoice Template, Settings, provider registry, account reservation, and per-task worker contracts remain covered.

### Scope protection
- No provider credential fields, provider IDs, account modes, provider manifests, Customer List schema, Invoice Template behavior, persistence mechanism, task worker architecture, or third-party dependency was changed.
- P02 and later production phases remain pending and require separate owner approval.

## 1.0.0.1.5 - 2026-08-08

### Fixed
- Repaired the Invoice Template editor's broken vertical geometry introduced by the previous anti-stretch sizing override.
- Removed Invoice Template card-level `QSizePolicy.Maximum` overrides that allowed compact scroll-area layouts to shrink cards below the height required by their controls and wrapped helper text.
- Added an Invoice-Template-local minimum-height/height-for-width text contract so wrapped descriptions and captions retain the space required for their rendered text without changing shared application widget behavior.
- Moved Currency and Invoice Type helper text onto dedicated full-width grid rows so narrow form columns cannot make those notes collide with the following label/control.
- Wrapped the two-column upper form region in a bounded minimum-height host and top-aligned the Invoice Template cards so surplus scroll viewport space is absorbed only by the terminal stretch instead of creating broken gaps between sections.
- Applied a minimum-size constraint to the Invoice Template scroll content layout so the resizable scroll area scrolls when content needs more height instead of compressing the form below its minimum geometry.
- Fixed the compact note/footer text editors to a stable 52 px height so their controls cannot collapse under layout pressure.

### Verification
- Replaced the prior source contract that required the faulty `QSizePolicy.Maximum` behavior with regression checks for minimum-content sizing, dedicated caption rows, top-aligned bounded cards, and stable multiline editor heights.
- Re-ran the complete project test suite and repository audit after applying the update to the frozen `v1.0.0.1.4` baseline.
- Updated release metadata, README, versioning, Invoice Template documentation, release notes, patch manifest, and private forensic/update records.

### Scope protection
- This release changes only Invoice Template UI geometry plus mandatory release metadata/documentation/tests.
- Invoice-template fields, validation, currency catalog/search behavior, provider mapping, task binding, account/customer models, provider runtimes, worker-thread behavior, other pages, dependencies, and public APIs are unchanged.

## 1.0.0.1.4 - 2026-08-07

### Fixed
- Removed Windows light/white scroll-content surfaces from Settings and the Invoice Template editor by explicitly applying the frozen Vib Tools page background to application scroll viewports/content hosts.
- Corrected Invoice Template card/stretch behavior so compact sections keep their intended height and spacing instead of expanding into broken empty gaps.
- Rebalanced the Currency and Days until due controls so the Currency field is intentionally narrower and aligned with the compact template form.

### Changed
- Currency selection is now editable type-to-search with case-insensitive contains matching and a maximum of eight visible results instead of an oversized full currency popup.
- Currency input is still validated against the existing approved uppercase currency catalog before the template can be saved; provider/task invoice creation and send bindings are unchanged.

### Verification
- Added UI regression contracts for dark scroll backdrops, searchable currency completion, valid-currency enforcement, and compact Invoice Template card sizing.
- Updated README, release notes, version metadata, baseline/update records, and forensic verification documentation.

### Scope protection
- No page, provider, task, account, customer-list, invoice-template field, provider runtime operation, worker-thread behavior, provider manifest, or dependency was removed, renamed, replaced, or expanded.

## 1.0.0.1.3 - 2026-08-07

### Added
- Added the Dashboard page using only live Invio state: provider/account/template/customer counts, task activity, account reservation summary, and context-sensitive next step.
- Added reusable invoice-template fields for invoice title, optional subtitle, invoice type, invoice note, customer note, terms, and per-line tax rate without adding customer, billing, shipping, or payment details to templates.
- Added an uppercase provider-compatible invoice currency catalog and provider-bound currency normalization.
- Added required invoice-template selection to task creation and persisted the template ID/name on each task.
- Added `src/core/provider_runtime/` with built-in Stripe and Refrens REST contracts using the Python standard library.
- Added deterministic Stripe idempotency keys and failed-recipient state used by Retry Failed.

### Changed
- Reworked the Invoice Template dialog into compact, scroll-safe sections with corrected table/header presentation and provider-oriented template fields.
- Compacted Settings text sizing/spacing and added an explicit visual checkmark asset for checked checkboxes.
- Restyled Live Logs and Reports to the approved compact Vib Tools reference layout while preserving their existing Invio actions.
- Reports now identify the invoice template assigned to each task.
- Settings startup-page choices now include Dashboard; the default remains Accounts.

### Provider execution
- Stripe tasks now run real draft-invoice -> line-item -> finalize -> send-invoice operations inside the task-owned worker thread.
- Refrens authentication, payload, create, and documented create-time email delivery are implemented; task execution is intentionally blocked before any create/send call when `billedTo.country` is unavailable from the approved email-only Customer List model. No country is guessed.
- External/custom providers continue to use the existing registered task-runner extension point.

### Verification
- Added provider-runtime execution tests, invoice-template/task binding tests, Dashboard/UI contracts, and Refrens required-data protection tests.
- Updated README, public user/developer/configuration/troubleshooting documentation, release metadata, patch manifest, and private forensic records.

### Scope protection
- No existing feature/page was removed or renamed.
- Existing Step-40J core color and sizing tokens remain frozen.
- No provider manifest/credential schema was changed.
- No customer-list schema, billing/shipping/payment data model, account reservation rule, or per-task QThread model was replaced.
- No new third-party dependency was added.

## 1.0.0.1.2 - 2026-08-07

### Added / Fixed
- Added working provider Uninstall actions while keeping bundled provider packages available for reinstall.
- Made Add Account credentials compact and two-column when a provider declares more than two credential fields.
- Applied compact responsive sizing to application-owned modal and message dialogs.
- Preserved all provider IDs, credential fields, account reservation behavior, page inventory, and worker-thread architecture.

### Verification
- Added provider uninstall and compact-dialog regression contracts and recorded the replace-ready `v1.0.0.1.2` delta.

## 1.0.0.1.1 - 2026-08-07

### Added
- Replaced the informational Settings page with persistent, user-facing application preferences backed by a dedicated non-sensitive settings manager.
- Added startup selection for a fixed page or the last page used.
- Added optional window size/position memory.
- Added individual confirmation controls for exiting with active tasks, closing tasks, deleting invoice templates, deleting customer lists, and clearing Live Logs.
- Added Live Logs preferences for timestamps, automatic scrolling, and an optional maximum retained line count (`0` = unlimited).
- Added file-location preferences for a default file folder and optional last-used-folder memory. These settings are used by provider manifest loading, customer email import, report export, and log export dialogs.
- Added Restore Defaults and Save Changes controls with validation and user-facing save feedback.

### Backend
- Added `src/core/settings/` with validated JSON settings storage, cross-platform per-user configuration paths, atomic writes, corruption-safe fallback to baseline defaults, runtime last-page/folder/window state, and no credential persistence.
- Settings defaults preserve the behavior of the frozen `v1.0.0.1` baseline until the user explicitly changes a preference.
- Settings are applied to the existing application actions without changing provider, account, invoice, customer-list, task, report, or worker architecture.

### Fixed
- Added a guarded viewport-size chip update so restoring a saved window size cannot access the header chip before it exists.
- Added off-screen protection for restored window position by applying saved coordinates only when they are on a currently available screen.

### Verification
- Added settings backend and wiring tests covering defaults, persistence, invalid settings recovery, folder/window opt-in behavior, credential exclusion, UI controls, and runtime action hooks.
- Updated README, configuration, user, architecture, installation, troubleshooting, versioning, release notes, patch manifest, and private forensic/update records for `v1.0.0.1.1`.

### Scope protection
- No existing page was added, removed, renamed, or reordered.
- No provider manifest, provider credential field, provider ID, capability, account mode, install/load contract, or provider execution contract was changed.
- No account, invoice-template, customer-list, task, report, or worker model was removed, renamed, or replaced.
- No provider network adapter, invoice-sending backend, credential persistence, domain-data persistence, or unrelated feature was added.

## 1.0.0.1 - 2026-08-07

### Fixed
- Fixed the Windows sidebar navigation surface so the scroll area, viewport, and navigation host use the official Vib Tools `#090D14` sidebar background instead of the platform default light surface.
- Corrected the repository audit so an existing validated installed-provider registry state is audited rather than incorrectly treated as a failure.

### Updated
- Restyled the Providers page cards to the official Vib Tools Plugin Page visual contract while preserving the existing provider install/load workflow and provider behavior.
- Removed development-stage and UI-only wording from current runtime labels, provider descriptions, dialogs, Reports, Settings, and current source documentation without enabling or simulating unavailable provider operations.
- Removed the `-ui` suffix from the bundled Stripe and Refrens provider package version labels; credential fields, modes, capabilities, and provider IDs are unchanged.
- Marked the desktop shell as the Invio production build `v1.0.0.1`.
- Synchronized public documentation and release metadata with the production UI baseline.

### Scope protection
- No page was added, removed, or renamed.
- No provider credential field, capability, account mode, provider ID, or install/load behavior was changed.
- No task, account, customer-list, invoice-template, report, log, or settings feature was removed or replaced.
- No provider network adapter or invoice-sending backend was added.

## 1.0.0 - 2026-08-07

### Baseline freeze
- Frozen the user-supplied `Invio_v1.0.0.zip` as the immutable source baseline for subsequent delta updates.
- Baseline SHA-256: `50188d56d416ccd359e748e69996fb3a5566dbeefb469d3d7cf7f7f41336636b`.
- The frozen baseline already includes the `ProviderManifestError` export fix, bundled Stripe and Refrens provider manifests, provider visibility rules, account reservation, and per-task worker-thread architecture.

## 0.1.0 - 2026-08-07

### Added
- New Invio desktop project created from the Vib Tools project template.
- Vib Tools Step-40J compliant dark desktop shell and all requested pages.
- Provider manifest install/load flow with installed-provider-only visibility.
- Provider-grouped account UI and dynamic credential fields.
- Invoice-only template editor without customer/billing/shipping fields.
- Named customer lists with bulk email import.
- Multi-account task creation with strict account reservation exclusivity.
- Dedicated `QThread` worker slot architecture per active task.
- Reports, live logs, and settings UI.
- Public user/developer documentation and private `project/` forensic records.

### Deferred
- Provider API networking and real invoice sending.
- Durable account/credential persistence.
- Provider-specific backend adapters and retry/idempotency implementation.
