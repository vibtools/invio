# User Guide

## 1. Dashboard

Dashboard shows installed providers, accounts, templates, customer count, task activity, account usage, and next setup/action. P02-restored state appears automatically after startup.

## 2. Providers

Install Stripe/Refrens or load an approved external manifest. Provider install/uninstall behavior is unchanged by P02.

## 3. Accounts

Open **Accounts** to Add, Edit, Re-test, or Delete a provider account. Add/Edit require a successful real API Test before commit. Edit is blocked while an account is assigned to an open Task. Re-test checks the current protected credentials without changing them and records the latest UTC test time plus a safe failure summary. Delete is blocked while a Task still references the account.

If a provider is uninstalled, its existing accounts remain visible under **Not Installed** and are not deleted. Edit/Re-test require reinstalling the provider; Delete remains available when the account is not Task-protected. Credentials remain in the approved OS-protected keyring and are never displayed.

If protected credentials cannot be safely saved or restored, the Account is not Task-ready. A missing protected credential restores and durably records the Account as **Not Verified**; restoring the secret later does not make the Account executable until a real Re-test succeeds.

## 4. Invoice Templates

Create reusable invoice content. Templates are now restart-durable. Customer/billing/shipping/payment identity data remains outside templates.

## 5. Customer Lists

Create independent named lists and import CSV, TSV, XLSX, XLSM, or TXT customer data. Email is mandatory. Name is optional. Country is optional and must be supplied explicitly as a two-letter ASCII alphabetic code when a provider requires it; Invio never guesses country or derives a name from email.

CSV/TSV/XLSX/XLSM files with a first usable header row containing `email` use structured `email`, `name`, `country` import. Files without that header and TXT files retain the legacy email-extraction workflow. Duplicate email identity is case-insensitive. Existing blank metadata can be enriched by explicit imported data, while conflicting nonblank metadata is reported with the source row number instead of overwritten silently. Malformed workbook/parser failures are reported as import errors rather than escaping the import workflow.

## 6. Tasks

Choose Provider, Verified Account(s), Invoice Template, and Customer List. Tasks and account reservations survive restart. A Task that was actively Running/Paused/Stopping when the app ended is recovered as **Stopped** and is never auto-resumed. Because exact continuation recipient identities are not durable until P10, Resume Remaining/Retry Failed is disabled after process restart rather than guessing recipients.

P07 formalizes Task actions: **Start** is first-run-only for pristine Ready Tasks; **Pause/Resume** continues the same active worker; **Resume Remaining** on a safely stopped current-session run sends only failed plus never-attempted recipients; **Retry Failed** on a Failed current-session run sends only exact failures; **Completed** cannot resend. **Close Task** remains the action that releases Account reservations.

### P05 immutable Task inputs

For a new Task, Invio freezes the selected customer records, a complete copy of the selected Invoice Template, the provider ID, and the ordered selected Account basis at the moment the Task is created. `Task.total` comes from that frozen recipient count.

After the Task exists, later Customer List imports/enrichment or Invoice Template edits do **not** change that Task. Start and Retry Failed reuse the same frozen inputs. To run different data/configuration, create a new Task. The new Task receives a new Task ID; the existing `Task.id` is the canonical identity for the existing logical run.

Tasks created before P05 cannot be given a trustworthy historical snapshot because older releases did not save one. After migration, those Tasks remain visible and can be closed, but Start/Retry are disabled and backend-blocked. Create a new Task for current data.

## 7. Reports and Live Logs

Reports use the restored Task state. Live Logs remain current-session display data; P02 does not add durable log storage or recipient-level delivery records.

## 8. Settings

Settings remain separate non-sensitive JSON preferences. Provider credentials are never written into `settings.json`.

## 9. Operational Storage Startup

Invio checks and, when required, migrates the per-user `domain.sqlite3` before the normal pages open. `v1.0.0.1.14` corrected the Windows-specific migration-backup handle issue. `v1.0.0.1.15` advances the domain schema to v4 for immutable Task execution snapshots while retaining the same WAL-aware, Windows-safe backup path. Supported databases migrate automatically and fail closed if storage is genuinely unavailable or unsafe.

## Provider preflight in v1.0.0.1.17

When you click **Create Task**, Invio checks the installed provider/runtime contract, selected verified Accounts, Invoice Template, and Customer List before saving the Task. When you later click **Start** or **Retry Failed**, Invio checks the same provider/account rules again against the Task's frozen P05 snapshot.

If a combination is unsupported, Invio shows **Preflight Failed** with a correction instead of beginning provider execution. Typical corrections include reinstalling a conflicting packaged provider, re-testing an unhealthy Account, using Stripe `INVOICE` instead of `BOS`, disabling Stripe Automatic Tax, setting unsupported Stripe line tax to zero, or restoring the canonical Refrens API Base URL.


## v1.0.0.1.18 provider preflight note

If a packaged provider manifest is inconsistent, Invio shows no safe effective runtime capability and blocks Task execution until the provider is reinstalled. Refrens API Base URL must be exactly `https://api.refrens.com` or the same URL with a trailing slash; explicit ports are rejected.

## P07 deterministic Task actions

Use the action shown for the current state:

- **Ready:** Start. The Task must have no prior progress.
- **Running:** Pause or Stop.
- **Paused:** Resume the same worker, or Stop.
- **Stopping:** wait for the worker to reach a terminal state.
- **Stopped:** Resume Remaining only when Invio still has the exact current-session continuation set.
- **Failed:** Retry Failed only when Invio still has the exact current-session failed set.
- **Completed:** Close Task; create a new Task for another full execution.

A Stop does not turn the next action into a full resend. Invio retains current-session failed and never-attempted recipients separately and excludes known successes. If the app restarts, those recipient identities are intentionally not inferred from the saved counts. Close the Task and create a new Task if continuation is unavailable; P10 is the planned durable recipient-recovery phase.
