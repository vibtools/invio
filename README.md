# Invio

**Invio** is a Vib Tools desktop application for provider-based invoice automation. **`v1.0.0.1.30`** is the owner-approved **P12 - Reports, Logs, Privacy and Operational Observability** release built on the explicitly frozen **`v1.0.0.1.29`** baseline. P12 is complete after automated private/public regression and fresh-overlay verification. The separate P11 live Refrens API/invoice/email acceptance gate remains pending and is not represented as passed. Completed acceptance phases are therefore **11/14**: P01-P10 plus P12.

## Current Application Scope

- **Dashboard**: live summary for installed providers, accounts, templates, customer count, task activity, account reservations, and next setup/action.
- **Accounts**: provider-grouped accounts with Add/Edit/Re-test/Delete lifecycle controls, real non-blocking API verification, durable verification health, protected credentials, and task reservation safety.
- **Invoice Templates**: reusable invoice-only content. Templates never store customer, billing, shipping, or payment details.
- **Customer Lists**: independent named bulk-customer lists. Email is mandatory; explicit name and country are optional. CSV/TSV/XLSX/XLSM structured imports and legacy email-only imports are supported.
- **Tasks**: installed provider -> one or more available verified accounts -> invoice template -> customer list, with P05 immutable execution inputs and P07 deterministic First Run / Resume Remaining / Retry Failed state semantics. One account cannot belong to two open tasks.
- **Providers**: manifest-based install/load/uninstall workflow with P06 declared-vs-executable capability visibility and packaged-runtime contract reconciliation. Built-in packaged runtime binding is resolved through one internal adapter registry. Stripe remains executable; the P11 implementation candidate enables built-in Refrens Task execution behind strict explicit customer-data, canonical-host, retry/no-replay, scheduling and P10-ledger safety contracts; packaged Agiled remains fail-closed until its current official API contract is authoritative. A provider is selectable in Accounts and Tasks only while installed.
- **Reports / Live Logs / Settings**: task summaries plus durable recipient reconciliation, structured privacy-redacted logs, spreadsheet-safe exports, closed-history retention controls, and persistent non-sensitive application preferences.
- **Threading**: each active Task runs through its own `QThread`; P08 keeps provider network sending and retry/backoff outside the GUI thread and uses cooperative worker shutdown without forced thread termination.

## P02 Durable Storage

Non-sensitive operational state now survives application restart in a per-user SQLite database:

- Accounts metadata and verification status;
- Customer Lists and ordered customer records (email, optional name, optional country);
- Invoice Templates, items, Decimal amounts/rates, and ordered terms;
- Tasks, account selections, status/counters/message;
- account reservations.

The database schema is versioned with SQLite `PRAGMA user_version`. Writes use explicit transactions, foreign keys, WAL journaling, and full synchronous durability. Corrupt/newer/unrecognized storage is not silently replaced. P03 introduced schema v2 verification-health metadata and WAL-aware migration backups. P04 upgrades to schema v3 for customer metadata. P05 introduced **schema v4**, adding durable immutable Task execution-snapshot tables for recipients, copied invoice-template content, provider identity, and the ordered account-assignment basis. P10 advances current storage to **schema v5** with exactly three durable delivery-ledger tables for execution runs, per-run recipients and provider operations while preserving all prior domain/snapshot tables.

Typical operational database paths use the same per-user Invio directory as Settings:

- Windows: `%APPDATA%\\Vib Tools\\Invio\\domain.sqlite3`
- macOS: `~/Library/Application Support/Vib Tools/Invio/domain.sqlite3`
- Linux: `$XDG_CONFIG_HOME/Vib Tools/Invio/domain.sqlite3`, otherwise `~/.config/Vib Tools/Invio/domain.sqlite3`

For Tasks with P10 delivery evidence, application restart reconciles interrupted runs from the durable ledger, derives exact `Succeeded` / `Failed` / `Pending` / `Uncertain` recipient outcomes, repairs lagging aggregate counters when evidence permits, and enables **Resume Remaining** / **Retry Failed** from durable state. Pre-P10 non-pristine Tasks still fail closed because Invio does not fabricate historical delivery evidence.

## Protected Provider Credentials

Provider credentials are not stored in SQLite or `settings.json`. P02 uses the owner-approved Python `keyring` integration and accepts only approved OS-protected backend families used by the keyring project for Windows Credential Locker, macOS Keychain, Freedesktop Secret Service/libsecret, or KWallet. There is **no plaintext fallback**.

SQLite stores only an opaque account credential reference such as `account:<account-id>`. At startup, credentials are restored into runtime memory from the protected store. If a protected credential is missing or unavailable, the account remains visible but is restored as **Not Verified**, so existing P01 Task creation/Start/Retry gates block provider execution.


## P03 Account Lifecycle and Provider Consistency

- Account metadata/credentials can be edited only while the account is not referenced by an open Task, and every edit requires a fresh successful API Test before commit.
- **Re-test** verifies the current protected credentials on a dedicated `QThread`; success/failure, UTC verification time, and a secret-scrubbed error summary are persisted.
- **Delete** is blocked for reserved/Task-referenced accounts and removes protected credentials with rollback/restore handling if durable deletion fails.
- Provider uninstall never deletes Accounts, protected credentials, Tasks, or reservations. Accounts remain visible under a **Not Installed** provider group.
- A provider with an active Task cannot be uninstalled. Existing inactive Tasks remain preserved, but Start/Retry is blocked until the provider is installed again.
- No age-based verification expiry or background health polling is introduced.

## P04 Verification Corrections in v1.0.0.1.13

The v1.0.0.1.12 P04 implementation was re-audited against the approved plan. v1.0.0.1.13 keeps the P04 architecture and feature scope unchanged while correcting four P04 contract defects and one out-of-scope UI drift:

- the historical mutable `CustomerList.emails` list behavior is restored through a customer-record-backed compatibility view;
- conflicts against existing Customer List metadata now retain the source row number in import diagnostics;
- explicit country values are restricted to two ASCII alphabetic characters so provider-required two-letter codes cannot accept non-ASCII lookalikes;
- malformed workbook/parser failures are converted to the existing user-facing import error contract instead of escaping as uncaught parser exceptions;
- the unrelated Dashboard metric label is restored to its pre-P04 wording.

No P05 immutable Task behavior, Refrens Task enablement, provider/worker architecture change, dependency change, or new page is included.

## v1.0.0.1.14 Operational Storage Runtime Hotfix

A Windows startup failure was reproduced in the schema-migration backup path. `DomainStore` created the WAL-aware SQLite backup into a temporary `.bak.tmp` database using the SQLite connection context manager and then immediately attempted to atomically replace the final `.bak` file. Python's `sqlite3.Connection` context manager commits or rolls back but does **not** close the connection, so Windows could keep the temporary backup file locked and raise `WinError 32` during `Path.replace()`.

`v1.0.0.1.14` explicitly closes the temporary backup destination connection before the atomic replacement. The migration sequence, WAL-aware live-backup semantics, schema version **3**, corruption/future-schema fail-closed rules, protected credentials, provider runtime, Task workers, UI and production roadmap are otherwise unchanged. A platform-neutral regression test now verifies that the destination handle is closed before replacement.


## P05 Immutable Task Execution Snapshots

Every newly created Task now captures and durably stores the exact execution inputs approved at Task creation time:

- ordered customer records (`email`, optional `name`, optional `country`);
- a complete immutable copy of the selected Invoice Template, its items and terms;
- provider ID;
- ordered selected Account IDs and the existing round-robin assignment strategy;
- `Task.id` as the canonical logical run identity.

`Task.total` is derived from the frozen recipient set. Start and Retry reconstruct provider-runtime input from the same durable snapshot rather than reading the current Customer List or current Invoice Template. Later customer imports/enrichment or template edits therefore do not silently change an existing Task. A different logical execution requires creating a new Task, which receives a new Task ID and a new snapshot.

Existing pre-P05 Tasks are preserved during schema-v3-to-v4 migration but are marked **LegacyUnavailable** because their historical creation-time recipients/template were never stored. Invio does not invent those missing inputs from current data. Such Tasks remain visible and closable, but Start/Retry fail closed; create a new Task to execute current inputs. Provider credentials are never copied into snapshot storage.

## v1.0.0.1.16 P05 verification correction

The P05 re-audit found three consistency gaps not covered by the v1.0.0.1.15 suite. New post-P05 Task persistence now requires a real captured snapshot and can no longer silently create `LegacyUnavailable` records; captured Task progress is validated against the frozen recipient count; and routine status/progress persistence no longer rewrites the immutable Task total. SQLite remains schema v4 and no P06 behavior is introduced.

## Packaged Providers

### Stripe

Stripe remains bundled with Test and Live modes. The built-in runtime can find/create customers by email, create draft `send_invoice` invoices, create line items, finalize invoices, call Stripe's invoice-send endpoint, and retain current-session exact failed/pending recipient state for **Retry Failed** and **Resume Remaining**. Successful recipients are excluded from those continuation sets. Stripe documents that test-mode send requests do not emit real customer emails, so test-mode API success must not be interpreted as inbox delivery.

### Refrens

Refrens remains bundled with API Base URL, URL Key, App ID, and App Secret. Authentication, invoice payload construction, invoice creation, and create-time email-delivery helpers remain implemented. P04 can now store explicit customer name/country data required by the Refrens payload contract, but **normal Refrens Task sending remains deliberately disabled until the separately approved P11 pipeline**.

## Invoice Template Contract

A template can contain reusable invoice content only: template name, uppercase currency, due period, title/subtitle/type, invoice note, customer note, footer, terms, provider options, and line items. Customer identity, billing, shipping, and payment details remain outside templates.

## Settings

Settings remain a separate non-sensitive per-user JSON file. They control startup/window behavior, confirmations, Live Logs, and file-dialog locations. Provider secrets are never written to Settings.

## Requirements

- Python 3.12+
- PySide6 6.7+
- openpyxl 3.1+
- keyring 25.7+

P02 adds `keyring>=25.7,<26`. The current keyring release line supports Python 3.12 and provides the approved system-keyring APIs used by Invio. Provider HTTP calls still use Python's standard library. 

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

Install a packaged provider from **Providers**, add and verify its account, create an Invoice Template, create/import a Customer List, then create a Task.

## Tests

```bash
python -m unittest discover -s tests -v
python scripts/test/audit.py
```

The current suite covers P01-P09 regressions plus P10 schema-v5 migration, write-ahead delivery evidence, durable attempt/account/idempotency/provider-ID records, interruption uncertainty, restart-safe continuation, aggregate recovery, ledger retention, Refrens P11 blocking, Agiled fail-close, and the one-task-one-QThread boundary.

## Documentation

- User guide: `docs/user/usage.md`
- Provider guide: `docs/guides/providers.md`
- Task guide: `docs/guides/tasks.md`
- Architecture: `docs/developer/architecture.md`
- Actual implementation status: `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- Error handling: `docs/developer/ERROR_HANDLING.md`
- Configuration: `docs/configuration/index.md`
- Troubleshooting: `docs/troubleshooting/index.md`
- Release notes: `docs/release-notes/1.0.0.1.26.md`

## Private Project Material

`project/` contains private development, architecture, scope-lock, forensic, phase, and baseline records. It remains Git-ignored and is not public documentation.

## Production Readiness Program

`v1.0.0.1.25` is the current P09-complete baseline. Production progress is **9/14 phases complete**. The next separately approved phase is **P10 - Persistent Delivery Ledger, Idempotency and Recovery**.

P02 makes operational metadata restart-durable, but it does **not** claim exact provider-side crash reconciliation. Per-recipient provider IDs, attempts, run identities, and durable retry/idempotency evidence remain P10 scope.

## License

MIT License. See `LICENSE`.

Maintained by **Vib Tools** - https://vib.tools/

## P06 Provider Capability and Preflight Validation

Before a new Task is persisted, and again before Start or Retry creates a runner, Invio now performs a deterministic local preflight over the provider installation, packaged manifest/runtime binding, Account verification health, P05 immutable template/customer snapshot, and provider-specific capability rules. A failed preflight creates no Task/reservation at the New Task boundary and performs no provider-side invoice/customer mutation.

For packaged providers, declared manifest capabilities are now distinguished from executable runtime capability. Stripe currently has executable API Test + invoice/send support. Refrens has executable API Test support, but its normal Task invoice/send pipeline remains deliberately disabled until P11. External loaded manifests still require the existing injected runner API; P06 does not introduce the P13 external-adapter architecture.

Packaged IDs (`stripe`, `refrens`, `agiled`) are reserved against external-manifest collision. An already-installed packaged-ID manifest whose execution-relevant credential/mode/capability contract does not match the bundled package fails closed and is never silently rewritten.

The current Stripe adapter is preflighted as standard `INVOICE` only. Automatic Tax and non-zero template line tax are blocked before network execution because the current Invio customer/send contract does not supply the location/tax-rate object semantics needed to guarantee those behaviors. Customer reuse and the existing description/footer/customer-note/terms mappings remain supported.

Refrens authentication is now allowed only to the canonical `https://api.refrens.com` origin. URL trust is validated before App ID/App Secret authentication payload construction. No Refrens Task sending is enabled by P06.

## v1.0.0.1.18 P06 Verification Corrections

The exact v1.0.0.1.17 P06 baseline was re-audited. v1.0.0.1.18 keeps SQLite schema v4 and the approved P06 architecture while correcting five contract gaps: built-in packaged manifests are now checked against hard-coded executable credential/mode/capability truth; Task preflight verifies the supplied Account sequence matches the P05 frozen Account assignment; Refrens currency validation uses the existing safe invoice-currency catalogue; the trusted Refrens URL accepts only the canonical host with no explicit port; and Providers cards display the actual installed manifest with effective runtime capability rather than a packaged look-alike.

Stripe documentation is account-country sensitive and can expose additional region-specific three-decimal currencies such as BHD/JOD/KWD/OMR/TND. Invio does not silently add them in this correction because the existing sender's minor-unit contract supports the frozen zero/two-decimal set only. Those currencies therefore remain preflight-blocked rather than being mis-scaled.

## P07 Task State Machine and Resend Safety

P07 makes every execution action deterministic without changing the P05 immutable input snapshot, P06 provider preflight, SQLite schema v4, or WorkerManager architecture.

- **Start** is a first-run action only for a pristine `Ready` Task.
- `Running -> Paused -> Running` resumes the same active worker and does not build a new send set.
- A safely stopped built-in Stripe run exposes **Resume Remaining**, which contains only the exact current-session union of failed recipients and recipients that were never attempted. Previously successful recipients are excluded.
- A `Failed` built-in Stripe run exposes **Retry Failed** only when the exact current-session failed-recipient set is available. Repeated retries shrink to the still-unresolved failures.
- `Completed` Tasks cannot Start/Retry/Resume again; another full execution requires a new Task and therefore a new `Task.id`/P05 snapshot.
- Stop reconciliation keeps runtime continuation state, persisted counters, and UI counts aligned: `success + failed == processed`, while `remaining == total - processed`.
- If the process restarts, exact recipient continuation identities are intentionally considered unavailable. Invio never reconstructs or guesses them from aggregate counters; Retry/Resume fail closed until P10 adds durable recipient-level recovery.
- The existing injected/external runner API remains first-run compatible, but P07 blocks Retry/Resume continuation for injected runners because that API does not expose a trustworthy recipient subset.
- Account reservations remain held until **Close Task**. No new database table, worker pool, network retry/backoff, or provider-send behavior is introduced.

## v1.0.0.1.20 P07 verification correction

The exact shipped `v1.0.0.1.19` P07 implementation was re-audited without advancing the production roadmap. Three P07 integration gaps were corrected while preserving the approved state table, P05 immutable snapshots, P06 preflight, SQLite schema v4 and WorkerManager architecture:

- a late queued worker `Completed` signal is reconciled to `Stopped` when the GUI has already accepted a valid late Pause/Stop state, avoiding an invalid `Paused/Stopping -> Completed` transition;
- Pause/Resume/Stop are enabled and accepted only while the Task's existing WorkerManager thread is still active, preventing stale controls from mutating state after the worker has already exited;
- a safe current-session continuation that is proven to be empty is distinguished from an unavailable continuation set, so the UI reports that nothing remains instead of falsely claiming recipient identities were lost.

No recipient ledger, automatic network retry/backoff, new Task status, database migration, provider-send change or P08 behavior is introduced.

## v1.0.0.1.21 Pre-P08 Provider Adapter Foundation and Agiled Package

The packaged-provider runtime contract now has one internal `ProviderAdapterContract` registry for execution-relevant manifest truth, capability profiles, API-test handler binding and Task batch handler binding. `ProviderManager` remains manifest-only and existing external-manifest loading remains metadata-only unless the historical injected runner API is used. This release does not implement the dynamic external provider loading architecture planned for P13.

Stripe API Test and invoice create/finalize/send continue through the same existing runtime functions. Refrens API Test remains executable and its normal Task path remains deliberately blocked until P11. Agiled is now bundled as a packaged provider with a protected `API Key` field, but its executable capabilities are intentionally empty: the accessible current Agiled product page and its linked API reference disagree on authentication/base-URL semantics, the owner-supplied candidate base URL was not independently verified, and an authoritative current invoice-send operation was not established. Agiled API Test and Task execution therefore fail before network transport, so the key is not sent to a guessed endpoint.

See `project/research/AGILED_API_CONTRACT_REVALIDATION_v1.0.0.1.21.md` for the exact evidence gate.

## v1.0.0.1.22 Provider Adapter Verification Correction

`v1.0.0.1.22` re-audits the exact shipped `v1.0.0.1.21` provider-adapter/Agiled implementation. No functional provider, invoice-send, UI, WorkerManager, storage, or Task-state defect was found in the approved scope. The release adds explicit regression coverage for packaged Agiled install/uninstall, executable handler binding integrity, and the generic manifest-driven UI/API-test gate, and revalidates that Agiled remains fail-closed before transport while the official Agiled materials still conflict on the executable API contract. Runtime changes are limited to release-version/User-Agent markers.

## v1.0.0.1.23 P08 Worker and Network Reliability

P08 adds structured provider/network failure metadata, bounded automatic retry with at most three total recipient attempts, exponential backoff with jitter, `Retry-After` handling, and an explicit 30-second shared urllib socket timeout policy for connection establishment and response reads. Retry remains recipient-scoped, preserves the original round-robin account assignment, and reuses the existing deterministic Stripe stage idempotency keys.

Retry waits are cooperative with existing Pause/Stop events. Stop never starts a new retry or recipient after cancellation is observed. Application shutdown is now asynchronous: active task workers receive Stop, the initial close event is ignored, and the window closes only after all task-owned `QThread`s have actually finished. Unexpected per-recipient exceptions are isolated and counted once without corrupting aggregate progress.

P08 does not add account failover, intra-task concurrency, rate-per-second scheduling, persistent attempt ledgers, Refrens Task sending, Agiled execution, external plugin loading, schema changes, dependency changes, or new UI pages.


## v1.0.0.1.24 P08 Verification Correction

The exact shipped `v1.0.0.1.23` P08 implementation was re-audited against its approved transient/permanent failure contract. Two transport-classification gaps were reproduced and corrected without changing retry count, backoff policy, provider business semantics, Task state, WorkerManager architecture, schema, dependencies, or UI workflow:

- a successful-status response whose body terminates with `http.client.IncompleteRead` is now classified as a retryable transient network disconnect instead of escaping as an unexpected per-recipient exception;
- TLS EOF/clean-close transport interruptions (`SSLEOFError` / `SSLZeroReturnError`) are treated as retryable disconnects while certificate verification and other non-transient TLS failures remain permanent;
- if an HTTP error response body is itself truncated, the known HTTP status and `Retry-After` header still drive the existing P08 classification instead of losing the status boundary.

The re-audit also corrected stale private P08 completion summaries/error-handling inventory that still described P08 as pending. P08 remains **COMPLETE**, production progress remains **8/14**, and P09 remains separately approval-gated.


## v1.0.0.1.25 P09 Multi-Account Scheduling, Limits and Health

P09 keeps the immutable round-robin primary assignment but adds a conservative runtime scheduler around the existing Stripe Task runner. Stripe Task requests are paced to 20 API requests/second/account with burst capacity 1. Recognized account-scoped Stripe rate-limit failures create runtime-only account cooldowns; timeout/disconnect/408/5xx failures create provider-wide cooldowns and never trigger account hopping.

Only recipients that have not yet entered provider execution may route deterministically to the next healthy frozen account when their primary account is temporarily cooling. Once any provider request has started for a recipient, the recipient remains bound to its original/selected account for P08 retry and future current-session Resume/Retry safety. HTTP 401/403 blocks further network use of that account until successful re-verification clears the runtime-only health state. No persistent attempt ledger, schema migration, intra-Task concurrency, provider-send semantic change, Refrens enablement, Agiled execution, plugin change, Settings control or new UI page is included.


## v1.0.0.1.26 P09 CI Verification Correction

GitHub Actions exposed a repository-contract test that directly opened files under the intentionally Git-ignored private `project/` tree. The full baseline ZIP contains those private records, so local/full-baseline audits passed, but a clean public GitHub checkout correctly omits `project/` and the test failed with `FileNotFoundError`.

`v1.0.0.1.26` makes the public tracked `README.md`, `ROADMAP.md`, and P09 release notes the mandatory CI completion records. The richer private `project/` records are still verified when the full private baseline is present. No P09 scheduler, provider, Task, WorkerManager, SQLite, dependency, Settings, page, layout, invoice-send, Refrens, Agiled, plugin, or P10 behavior changes.

## P10 Persistent Delivery Ledger and Restart Recovery

P10 keeps `Task.id` as the canonical logical provider/idempotency identity and adds a separate durable execution `run_id` for every First Run, Resume Remaining and Retry Failed invocation. Supported Stripe Task operations are write-ahead recorded before transport with recipient, primary/actual account, stage, P08 attempt number, existing deterministic idempotency key and timestamps. Provider customer/invoice IDs and sanitized failure evidence are persisted when available.

On restart, unfinished runs are marked interrupted and any unresolved mutating operation is classified `Uncertain`. The latest durable recipient outcomes become the authoritative source for continuation and aggregate Task reconciliation. A recipient that previously entered provider execution retains its exact P09 account binding across restart; genuinely unattempted recipients may still use the existing deterministic P09 failover policy. Historical ledger rows survive Close Task. P12 still owns recipient-level report/export/retention UX.

## v1.0.0.1.28 P10 Verification Correction

The exact `v1.0.0.1.27` P10 baseline was re-audited against the approved durable-ledger plan. The audit reproduced a historical uncertainty-reconciliation defect: a mutating operation recorded `Uncertain` could remain incorrectly unresolved after a later successful replay of the exact same stage and non-empty deterministic idempotency key, while an unresolved uncertainty from an earlier run could also be hidden by a later unrelated deterministic failure. `v1.0.0.1.28` corrects only that P10 ledger-reconciliation boundary. A later matching successful operation now resolves the prior ambiguity; unrelated failures cannot erase unresolved mutating uncertainty. Historical recipient/account/primary-assignment consistency is also validated fail-closed. SQLite remains schema v5 with the same three P10 tables, production progress remains **10/14**, and P11 remains unimplemented.

## v1.0.0.1.29 P11 Refrens implementation candidate

P11 is **IMPLEMENTED / LIVE ACCEPTANCE PENDING**. The built-in Refrens adapter now enters the same Task pipeline as Stripe while preserving the existing one-Task-one-QThread architecture, P05 immutable snapshots, P07 action semantics, P08 worker/network rules, P09 account binding/health framework and P10 schema-v5 delivery ledger.

Refrens Task execution requires explicit customer `email`, `name` and two-letter `country`; Invio never substitutes the email for a missing name or infers country. The exact `https://api.refrens.com` destination is validated before App ID/App Secret payload construction or transmission. Indian billing recipients are blocked before invoice creation because the current approved customer model has no Refrens-required GST State field. The candidate uses an owner-approved Invio safety pace of 1 API request/second/account with burst 1, retries only the authentication stage under the existing P08 maximum-three-attempt policy, and never blindly replays an ambiguous invoice-create/email mutation. Such an outcome remains durable `Uncertain` evidence in the P10 ledger and is excluded from automatic Refrens replay.

No new page, customer field, schema migration, dependency, WorkerManager architecture, Stripe behavior, Agiled execution or P12+ feature is included. The production phase count remains **10/14** until an owner-supplied Refrens environment proves: (1) live API Test, (2) real invoice creation, and (3) actual recipient email delivery.

## v1.0.0.1.30 P12 Reports, Logs, Privacy and Operational Observability

- Existing Task report is preserved and Reports now adds a recipient-level durable ledger view with safe status, distinct attempts, actual/planned account reference, provider invoice reference, last stage/error code, provider-send acceptance and independent email-delivery state.
- `Succeeded` delivery-ledger state is presented as **Provider Accepted**, never as independently confirmed email delivery when no delivery-confirmation event exists.
- Live Logs now carry `INFO/WARNING/ERROR` severity plus `APPLICATION/TASK/PROVIDER/STORAGE/EXPORT/RECOVERY/PRIVACY` category metadata and mask recipient email addresses.
- Central redaction covers provider password values, Stripe keys, Refrens App Secret, Agiled API keys, Authorization/Bearer/Basic/token forms and runtime-provided secret values before display/new durable error persistence.
- Task/recipient CSV and Live Logs exports use atomic replacement; user/provider-controlled CSV text is spreadsheet-formula neutralized and export failures are shown to the user instead of escaping the event handler.
- Delivery history is retained indefinitely by default. **Clear Delivery History** deletes only already-closed Task ledger history; open Task recovery data is never deleted. **Clear Logs** clears only the in-memory view.
- SQLite remains schema v5 with exactly the existing three P10 delivery-ledger tables. Provider send semantics, P09 scheduling and P10 idempotency/recovery are unchanged.
- P11 remains **IMPLEMENTED / LIVE ACCEPTANCE PENDING**; P12 completion does not fabricate live Refrens acceptance.
