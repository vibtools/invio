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

Choose Provider, Verified Account(s), Invoice Template, and Customer List. Tasks, account reservations, immutable P05 inputs and P10 delivery evidence survive restart. An interrupted Task is never auto-resumed. For P10-ledger Tasks, Invio reconstructs exact `Succeeded`, `Failed`, `Pending` and `Uncertain` recipient outcomes and enables Resume Remaining / Retry Failed only when the durable evidence proves the continuation safe. Pre-P10 non-pristine Tasks still fail closed rather than guessing historical recipient outcomes.

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
- **Stopped:** Resume Remaining only when Invio has an exact safe continuation set from current-session or P10 durable evidence.
- **Failed:** Retry Failed only when Invio has the exact durable/current-session failed set and no unfinished Pending/Uncertain work blocks that action.
- **Completed:** Close Task; create a new Task for another full execution.

A Stop does not turn the next action into a full resend. P10 persists recipient outcomes and exact attempted-account binding, so restart continuation excludes known successes and does not infer identities from aggregate counters. An interrupted side-effecting operation is surfaced as `Uncertain`; Invio reuses the same Task-derived idempotency identity and exact bound account only when the durable record is sufficient. Pre-P10 Tasks without trustworthy delivery history remain fail-closed.

## v1.0.0.1.20 Task-control verification note

Pause, Resume and Stop are now actionable only while the Task's worker thread is actually active. This prevents a stale button click after a worker has already finished. If a Stop/Pause is accepted at the same time a completion signal is arriving, the Task safely settles as **Stopped** under the existing P07 state rules.

If a safe Stopped Task has no failed or pending recipients left, **Resume Remaining** stays disabled and Invio explains that no unresolved recipients remain. This is different from restart recovery, where exact identities are unavailable and continuation intentionally fails closed.

## Agiled in v1.0.0.1.21

Agiled appears as a packaged provider and can be installed. Its Account dialog accepts the protected `API Key` field, but **API Test is intentionally unavailable** and the account cannot become Task-ready while the current Agiled API contract remains unresolved. Invio does not transmit the API key to an unverified endpoint and does not attempt an Agiled invoice create/send request in this release. Stripe and Refrens behavior is unchanged.

## Agiled verification in v1.0.0.1.22

The user-facing behavior is unchanged from `v1.0.0.1.21`: install Agiled through Providers to expose its manifest-driven Account form, but API Test remains unavailable and the account cannot become Task-ready. No API key or invoice request is transmitted. This release verifies that the UI remains generic and does not contain an Agiled-specific execution bypass.

## P08 retry and shutdown behavior

When Stripe encounters a transient timeout, disconnect, HTTP 408/429 or selected 5xx response, Invio can retry that recipient automatically up to a maximum of three total attempts. Live Logs show the transient failure and retry delay. A recipient is counted only once in Task progress, regardless of automatic attempts.

Pause also pauses retry waiting. Stop cancels future retries/recipients after any currently blocking request returns or reaches the 30-second timeout. If you exit while a Task is active, the existing exit confirmation is used; after confirmation Invio remains open until the active task thread has stopped safely, then closes automatically.


## P08 verification correction in v1.0.0.1.24

The automatic transient retry behavior also covers a provider connection that ends before the complete HTTP response body arrives, including TLS EOF/clean-close disconnect forms. These cases use the same existing maximum-three-attempt policy and do not change Task progress/account assignment/idempotency rules. Certificate verification failures remain permanent and are not automatically retried.


## P09 multi-account scheduling in v1.0.0.1.25

Tasks keep their original round-robin primary account assignment. Invio now paces Stripe Task requests per account and may route a recipient to the next healthy frozen account only if that recipient has not yet entered provider execution and its primary account is temporarily cooling from a recognized Stripe account rate-limit condition. If any provider request has already started for that recipient, Invio will not move it to another account. Provider/network outages wait on a provider-wide cooldown, and an account that returns HTTP 401/403 is not used again in the current runtime until it is successfully re-tested.


## v1.0.0.1.26 verification note

No user workflow changes from `v1.0.0.1.25`. P09 account pacing, cooldown, deterministic pre-attempt fallback and current-session cross-account replay protection behave the same. This release only corrects a GitHub CI documentation-test boundary.

## v1.0.0.1.27 P10 restart-safe delivery history

Each supported Stripe Task execution now creates a durable execution Run ID separate from the Task ID. The Task ID still identifies the logical provider operation and remains the basis for existing Stripe idempotency keys. Invio records each selected recipient, primary/actual account, operation stage, attempt, provider IDs when available, timestamps and sanitized errors. If the application stops between a mutating provider request and its confirmed local outcome, the recipient is shown internally as `Uncertain` rather than guessed. Existing Tasks/Live Logs expose the resulting safe Resume Remaining or Retry Failed action; no new UI page was added.

## v1.0.0.1.28 P10 uncertainty correction

After restart or a retry/resume, Invio keeps a recipient `Uncertain` when an earlier mutating provider operation still lacks exact reconciliation evidence. A later successful operation resolves that ambiguity only when it uses the same stage and the same persisted non-empty idempotency key. An unrelated later failure does not make the prior ambiguity disappear. Use the existing Resume Remaining flow; no new page or action is added.

## Using Refrens Tasks - v1.0.0.1.29 candidate

Refrens Task execution requires a successfully API-tested Refrens account using the exact API Base URL `https://api.refrens.com`, plus Customer List records with explicit Email, Name and two-letter Country. Do not leave Name or Country blank. Indian recipients are currently blocked because Invio's approved customer model does not contain the Refrens-required GST State field. Automatic Tax and Customer Reuse remain unsupported by the current Refrens Task contract. If a Refrens invoice-create/email request has an uncertain network outcome, Invio keeps that recipient uncertain and does not automatically send it again.

This release is an implementation candidate: owner live API Test, real invoice creation and recipient email delivery must still be verified before P11 is marked complete.
