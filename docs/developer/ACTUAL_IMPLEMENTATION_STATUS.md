# Actual Implementation Status

**Baseline:** `Invio v1.0.0.1.5`  
**Purpose:** Record only behavior that exists in the frozen source, plus explicit production gaps.  
**Status values:** WORKING, PARTIAL, NOT IMPLEMENTED, BLOCKED.

## Current Summary

| Area | Status | Current reality |
|---|---|---|
| Vib Tools desktop shell/pages | WORKING | Dashboard, Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, Settings exist |
| Provider manifest install/load/uninstall | WORKING | Validated manifests copied to/deleted from local registry |
| Executable external provider plugin loading | NOT IMPLEMENTED | ProviderManager does not import/execute provider code |
| Stripe built-in invoice sending | WORKING locally by contract | Real HTTP request path exists; live provider certification still pending |
| Refrens API helper contract | PARTIAL | Auth/payload/create/email helper exists |
| Refrens normal Task sending | BLOCKED | Current email-only Customer List cannot supply country required by current adapter gate |
| Add Account API Test | PARTIAL | Required-field validation only; real `ProviderRuntime.test_account()` is not wired to UI |
| Account persistence | NOT IMPLEMENTED | Accounts/credentials are current-session memory only |
| Customer List persistence | NOT IMPLEMENTED | Lists/emails are current-session memory only |
| Invoice Template persistence | NOT IMPLEMENTED | Templates are current-session memory only |
| Task persistence/recovery | NOT IMPLEMENTED | Tasks/reservations/progress lost at restart |
| Dedicated worker thread per active Task | WORKING | One `QThread` per active Task |
| Multiple accounts per Task | WORKING | Deterministic sequential round-robin assignment |
| Parallel account workers inside one Task | NOT IMPLEMENTED | One Task runner processes recipients sequentially |
| Pause/Resume/Stop | WORKING with limitation | Cooperative; in-flight blocking request is not interrupted |
| Retry Failed | PARTIAL | Works from process-memory failed set; not restart-safe |
| Recipient delivery ledger | NOT IMPLEMENTED | No persistent per-recipient attempts/customer ID/invoice ID/status |
| Reports | PARTIAL | Aggregate task report + CSV export only |
| Logs | PARTIAL | Live/export logs; Stripe key masking only; emails remain visible |
| Settings persistence | WORKING | Non-sensitive per-user JSON with atomic write/fallback |

## Provider System

### WORKING

**Files:** `src/core/provider_manager/manager.py`, `providers/packages/*/provider.json`

- Bundled provider discovery.
- Manifest validation.
- Install packaged provider.
- Load external manifest.
- Uninstall installed manifest.
- Installed-provider visibility for Accounts/New Task selection.

### PARTIAL / NOT IMPLEMENTED

- Manifest install does not install executable Python adapter code.
- Unknown/external providers need a runner manually registered through `MainWindow.register_task_runner()`.
- Task start does not currently re-check that a built-in provider is still installed.
- An external manifest can reuse a built-in provider ID and change visible credential/capability declarations while dispatch still selects the hard-coded runtime by ID.

## Accounts

### WORKING

- Add account from installed provider manifest fields.
- Provider mode selection.
- Password-style fields visually hide secret entry.
- Accounts grouped by provider.
- Account reservation prevents one account from being assigned to two open Tasks.

### PARTIAL / MISSING

- UI `API Test` validates field presence only.
- Real `ProviderRuntime.test_account()` is not connected to Add Account.
- Existing Stripe `test_account()` does not receive the selected Test/Live mode, so current mode consistency validation remains send-time logic.
- Saved status is `API Test Pending`.
- No edit/delete/re-test workflow.
- No durable storage.
- No protected credential store.
- No verified-account Task gate.

## Customer Lists

### WORKING

- Create independent named lists.
- Import `.csv`, `.tsv`, `.xlsx`, `.xlsm`, `.txt`.
- Extract, lowercase and de-duplicate email addresses.
- Delete list if not referenced by a Task.

### PARTIAL / MISSING

- Email only; no name/country/provider metadata.
- No durable storage.
- No per-recipient edit/delete workflow.
- List can still be expanded after Task creation, which can make runtime recipient count differ from Task total.

## Invoice Templates

### WORKING

- Reusable content-only template.
- Currency validation/catalog.
- Due days 1-365.
- Invoice title/subtitle/type.
- Invoice note/memo.
- Customer note.
- Footer and terms.
- Automatic-tax and customer-reuse options.
- One or more invoice items with description/quantity/unit amount/tax rate.
- Bound template cannot be deleted while referenced by a Task.
- Current UI geometry/searchable currency behavior from v1.0.0.1.5.

### PARTIAL / MISSING

- No durable storage.
- Bound template can still be edited.
- Task runtime snapshots the current template at Start/Retry, so post-Task edits can change execution.
- No provider-specific template capability preflight.
- Stripe sender does not use template line `tax_rate` or `invoice_type` in its current mapping.

## Tasks

### WORKING

- Requires installed provider during task creation UI.
- Requires account(s), Customer List and Invoice Template.
- Rejects mixed-provider accounts.
- Reserves each selected account until Task close.
- Shows provider/template/accounts/customer-list summary.
- Start/Pause/Resume/Stop/Retry Failed/Close actions.

### PARTIAL / MISSING

- No persistent Task/run state.
- No immutable stored execution snapshot.
- No recipient-level status.
- Completed and Failed Task cards still allow normal Start.
- Normal Start is a full current-list run, not a protected continuation.
- Stop can leave unattempted emails in the runtime failed set without a matching final `task.failed` update, so Retry Failed can be disabled even when internal retry recipients exist.
- No verified-account gate.

## Threading / Worker

### WORKING

**File:** `src/core/worker_manager/manager.py`

- Separate `QThread` per active Task.
- Worker object moves to task thread.
- Worker signals return status/progress/log events to UI.
- Pause/Resume/Stop control flags are thread-safe events.
- Uncaught task-runner exceptions are isolated from GUI thread.

### PARTIAL / MISSING

- Provider calls inside a Task are sequential.
- No automatic transient retry/backoff/rate limiting.
- No per-account health/failover.
- Stop is cooperative and does not interrupt current `urlopen()`.
- Shutdown wait (1500 ms) is shorter than provider HTTP timeout (30 s).

## Stripe Runtime

### WORKING

**File:** `src/core/provider_runtime/runtime.py`

- Validate key prefix and Test/Live mode.
- Optional exact-email customer lookup.
- Customer creation sends uploaded email only: `email=<address>`; no derived username/name field is sent.
- Draft send-invoice creation.
- Invoice line item creation.
- Currency normalization/minor-unit handling.
- Finalize invoice.
- Send invoice.
- Deterministic task/email/stage idempotency key generation.
- Per-recipient `ProviderRuntimeError` handling and in-memory failed set.
- Retry Failed selects only failed recipient emails retained for the current process/task.

### PARTIAL / MISSING

- No live certification recorded in baseline.
- No automatic network retry/backoff/rate-limit handling.
- No persistent provider customer/invoice IDs.
- No persistent idempotency/delivery ledger.
- Idempotency keys are based on Task ID/email/stage without a separate run ID, while the UI currently allows rerunning the same Task.
- Line template `tax_rate` is not applied by the current Stripe sender.
- Template `invoice_type` is not applied by the current Stripe sender.

## Refrens Runtime

### WORKING/PARTIAL

- Authentication helper.
- API connection-test helper.
- Invoice payload builder.
- Customer country validation in helper.
- Customer name fallback is the **full email address** when name is blank.
- Invoice create request plus create-time email payload.
- Refrens base URL is user-entered and currently checked only for an `https://` prefix before authentication credentials are sent.
- Contract tests with injected transport.

### BLOCKED

Normal Refrens Task runner is blocked before create/send because current Customer Lists do not provide `billedTo.country`. No country is guessed.

## Reports and Logs

### WORKING

- Aggregate report page from current Task state.
- CSV report export.
- Live Logs page.
- Text log export.
- Optional timestamps, auto-scroll and line retention.
- Stripe-shaped secret/restricted key masking.

### PARTIAL / MISSING

- No recipient-level delivery report.
- No provider customer/invoice IDs.
- No attempt/error taxonomy columns.
- Email addresses appear in execution logs.
- Export write errors are not converted to user-facing warnings.
- CSV export is not neutralized against spreadsheet formula injection in user/provider-controlled text fields.
- `Success` represents successful provider API send/create acceptance in the current runner; the app does not independently confirm inbox delivery.

## Settings

### WORKING

- Startup page/last page.
- Optional window geometry memory.
- confirmations.
- Live Log display/retention options.
- default/last file folder.
- JSON validation, corruption fallback and atomic writes.
- Settings payload excludes account credentials.

## Baseline Test Status

- Compile: PASS.
- Unit/contract suite: 55/55 PASS.
- Repository audit: PASS.
- Native PySide6 runtime test in current audit container: unavailable because PySide6 is not installed.
- Live provider API certification: not recorded by the baseline test suite.

## Update Rule

After every production phase, update this file by moving only genuinely implemented/verified behavior from PARTIAL/NOT IMPLEMENTED/BLOCKED to WORKING and recording any remaining limitation. Do not mark a feature WORKING based only on UI presence or a mock/injected-transport test when live certification is required by the claim.
