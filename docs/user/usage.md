## v1.0.0.1.49.1 — Connect once, reuse authorization

For browser-auth-enabled providers, use **Accounts > Add Account > Connect <Provider>** to authorize in your normal browser. After connection, run API Test and save. Invio keeps the refresh/bootstrap credential in the existing protected OS credential store and the provider automatically obtains fresh access tokens when needed. You normally authorize once; reconnect only if the provider revokes/expires the grant, permissions change, or protected token persistence cannot continue.

## v1.0.0.1.49 — Compact Headers and Wide Tables

Providers and Settings keep the same actions/controls with tighter frozen header spacing. Invoice Templates retains all seven columns and Edit/Delete actions. Reports retains all Task Summary and Recipient Delivery History columns; wide content can be reached through horizontal scrolling without losing report data.

## v1.0.0.1.48.9 — Customer Lists

Open **Customer Lists** to work in two compact panels. The left Lists panel keeps list search/state filtering, shows each list with a muted customer count and a row `⋯` menu, and scrolls for larger list sets. The Customers panel keeps Search, Country filter, Upload, `# / EMAIL / NAME / COUNTRY`, rows-per-page and pagination. Existing create/select/delete/import behavior is unchanged.

## v1.0.0.1.48.8 — Accounts Status Visibility

Accounts status badges now receive enough natural column width for the active Qt font/DPI environment. Status values, colors, actions, filtering and pagination are otherwise unchanged.

## v1.0.0.1.48.7 — Status Display

Status values throughout the shared UI use consistent semantic badges: success, warning, danger and neutral. Table status cells show the status exactly once; filtering and underlying status behavior are unchanged.

## v1.0.0.1.48.6 — Accounts Compact Table / Row Actions

The Accounts flat table keeps the same data and workflow with improved compact presentation: Account/Provider share available width, Status/Action stay compact, and status badges use the approved Accounts-only Vib Tools colors (success `#22C55E`, warning `#FCD34D`, danger `#F87171`, primary `#2563EB`). Clicking `⋯` opens the existing **Edit**, **Re-test**, and **Delete** menu inside the safe intersection of the Invio window and current screen; near the bottom it may open above the row.

## v1.0.0.1.48.5 — Accounts List

The Accounts page now lists each account as one row with **Account**, **Provider**, **Status**, and **Action**. Use Search plus Provider/Status filters for large account sets, change rows-per-page or page with the existing footer, and open the row `⋯` menu for **Edit**, **Re-test**, or **Delete**. **Add Account** remains the only page-header action.

The underlying account verification, credentials, task-assignment restrictions and confirmation behavior are unchanged.

## v1.0.0.1.48.4 — Creating a Task

Open **Tasks → New Task**. Provider, account availability/status filters and account search now appear on one compact row. Select eligible accounts in the same checkbox table; use the existing pager for larger result sets and scroll inside the fixed account viewport when needed. Choose the Invoice Template and Customer List on the bottom row, then use **Create Task** or **Cancel**. The underlying selection and creation workflow is unchanged.

## CI/CD stabilization — v1.0.0.1.48.3

There is no new user workflow or user-visible feature in this release. Existing dialogs, pages, Task actions, providers, customer/invoice operations and Settings behavior are unchanged. The update is limited to automated test/build/release reliability and release-version identity.

## Popup / Confirmation behavior — v1.0.0.1.48.02

Existing warnings, errors, information messages and confirmations retain their previous wording and actions. The hotfix restores their ability to open and return the selected button after the custom-chrome redesign. No new user workflow is introduced.

## Closing a Task — v1.0.0.1.48.01

For a Ready, Stopped, Failed or Completed Task, **Close Task** uses the existing optional confirmation setting. When confirmed, Invio removes the operational Task, releases its reserved accounts and retains historical recipient-delivery evidence according to the existing ledger policy. Running, Paused or Stopping Tasks must still be stopped first.

## v1.0.0.1.48.0 Dialog Presentation

App-owned dialogs now have clearer subtle separation from the parent window and display their dialog name once in the custom title bar. Dialog fields, buttons, keyboard behavior and workflows are unchanged.

## v1.0.0.1.47.0 UI Notes

- Invio now uses one compact application title bar; the duplicate legacy header is removed.
- Sidebar destinations are grouped as MAIN, OPERATIONS and SETTINGS. Navigation destinations and workflows are unchanged.
- App-owned dialogs use the same dark title bar, compact footer and modal background treatment. `Esc`, Tab navigation, close, drag and required resize behavior remain available.
- Account API Test progress/results use the existing inline status area as the primary feedback surface; provider verification semantics are unchanged.
- Data Grid search/filter/pagination and all existing columns remain unchanged from v1.43.0.

## v1.0.0.1.46.0 window controls

The Main Window now uses Invio-branded controls for minimize, maximize/restore and close. Application-owned dialogs use a compact branded title bar with Close. Drag title bars to move windows; resize remains available from window edges.

# User Guide

## v1.0.0.1.45.0 Providers Page usage

Providers Page navigation/search/install/uninstall usage is unchanged. Provider cards no longer appear as transient top-level windows during app startup/page refresh; Available/Verified is now shown compactly below the Provider Name.

## v1.0.0.1.44.0 UI usage

Static page introductions and card/section subtitles are intentionally omitted for a cleaner desktop surface. Titles, controls, provider package descriptions, dynamic status/validation text, data-grid search/filter/pagination and all workflows behave as in v1.0.0.1.43.0.

## v1.0.0.1.43.0 Data Grid usage

Accounts, Customer Lists/Records, Invoice Templates and Reports now provide compact UI-session search/filter/pagination controls. Pagination defaults to 10 rows with 25/50 alternatives and does not change stored data. Long table values retain full-value tooltips. Accounts keep provider grouping with compact displayed API-test time; New Task Accounts is a bounded four-column selector that preserves the existing Verified/available eligibility rules. Invoice Items pagination hides non-page rows only in the view; every item remains part of the saved template payload.


## v1.0.0.1.42.0 Forms and Settings usage

Application-owned forms use a denser 32px control system with consistent primary actions and reduced explanatory copy. Settings adds `Search settings... (Ctrl+F)`: type any setting/card/option term to filter visible cards; `Ctrl+F` focuses the field. `Reset Settings` loads existing defaults but does not persist them until `Save Changes` is selected. All existing setting meanings and defaults are unchanged.


## 1. Dashboard

Dashboard shows installed providers, accounts, templates, customer count, task activity, account usage, and next setup/action. P02-restored state appears automatically after startup.

## 2. Providers

Install Stripe/Refrens or load an approved external manifest. Provider install/uninstall behavior is unchanged by P02.

In `v1.0.0.1.41.1`, the Providers page adds a live search field above the cards and uses packaged Stripe, Refrens, Agiled and Odoo logos instead of v1.41 initials. Installed provider packages show the owner-approved **Verified** badge directly below the logo; the version appears as small text at the footer bottom-right. Capability chips and runtime/credential metadata are no longer displayed. Cards remain 220px high with 280px minimum width, responsive 2–4-column reflow, maximum three-line descriptions and bottom-anchored actions. Install/Load/Uninstall behavior is unchanged.

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

## Reports, Logs and Privacy - v1.0.0.1.30

**Reports** keeps the Task summary and adds **Recipient Delivery History**. A `Provider Accepted` result means the provider accepted the send/create request; it does not prove mailbox delivery unless an independent delivery-confirmation event exists. Use **Export Recipient CSV** for the same privacy-bounded fields. CSV exports are written safely for spreadsheet opening.

**Live Logs** show severity/category metadata and mask recipient email addresses plus provider secrets. **Clear Logs** clears only the current view. **Clear Delivery History** is separate and deletes only history for Tasks already closed; open Task recovery history is protected.


## P12 support-report correction - v1.0.0.1.31

Recipient Delivery History remains the support surface for full recipient email, account reference and provider invoice reference. A row shows **Provider Accepted** only when the durable ledger contains successful provider send-stage evidence. If the stored history is contradictory or a side-effecting outcome remains unresolved, Invio reports `Uncertain` or fails the report read safely rather than guessing. Live Logs continue to mask recipient email and provider secrets, including quoted JSON-style token/secret fields.

## External executable providers - P13

To load an executable external provider, select its `provider.json` through the existing **Load Provider** action. The manifest must declare `runtime_adapter` interface version 1 and a compatible fixed sibling `adapter.py` must be present. Invio shows a warning before loading executable code because the adapter runs in-process with Invio permissions and is not sandboxed. Load only code you trust. A provider shown as `Manifest only`, `Missing`, or `Incompatible` cannot API Test or execute Tasks. Valid executable providers use the same verified-account and Task controls as built-in providers.


## Trusted external provider adapters (P13)

`Load Provider` still starts from `provider.json`. A provider may be manifest-only, or it may declare an executable runtime and include a fixed sibling `adapter.py`. Before executable Python is installed, Invio asks for explicit confirmation because the adapter runs in-process with Invio permissions and is not sandboxed. Load only provider code you trust. A provider card reports Executable, Manifest only, Missing or Incompatible separately from the manifest's declared capabilities. Invalid or unavailable executable adapters cannot API Test or run Tasks.

## External provider lifecycle safety - v1.0.0.1.33

A broken executable adapter that fails while exposing its declared runtime metadata is now shown as **Incompatible** instead of being able to terminate application startup. Uninstalling an executable external provider remains blocked while Tasks reference it; if a filesystem error occurs while detaching the provider's adapter file, Invio restores the provider manifest and reports the uninstall failure rather than leaving a partial uninstall.


## P14 certification-candidate notice

`v1.0.0.1.34` is not yet production-certified. Stripe and Refrens executable paths remain available under their existing safety gates, but production certification requires owner-controlled live-provider evidence and native Windows acceptance. Do not interpret this candidate label as confirmation that a provider accepted or delivered any specific invoice/email.


## Using the v1.0.0.1.38 Windows builds

For the portable build, extract the complete `Invio` folder and keep all DLLs, `assets/`, and `providers/` beside `Invio.exe`; do not copy only the EXE. For the MSI build, install normally and launch the installed Invio executable. The MSI is intentionally per-user so the existing Providers Load/Install/Uninstall workflow can continue writing its registry files without administrator elevation.

Portable/MSI availability does not mean P14 production certification passed. Check the release notes for live-provider and Windows-runner certification status before treating a build as production-certified.

### Portable ZIP state behavior

The portable ZIP is *installer-free distribution*, not a portable-data mode. Invio continues to use the existing per-user Settings/SQLite locations and OS-protected keyring. Moving the OneDir folder does not move or duplicate those per-user records. The provider registry remains beside the application because that is the frozen P13 behavior.


### v1.0.0.1.38 release inventory note

End-user distribution remains unchanged: use either the complete portable ZIP or the per-user MSI. The `.wixpdb` file is a WiX build-debug artifact and is not part of the supported Invio release.
## Current live-acceptance sequence for v1.0.0.1.39 candidate

For owner validation, use the existing Account workflow unchanged: run the real provider **API Test**, then **Add Account**. A successful candidate must commit the Account to protected credential storage, show it as Verified, and restore it after restart. Only then proceed with the already-existing Customer List, Invoice Template and one-recipient controlled Task flow. v1.39 is not approved for public release until this source/live sequence and the later compiled Windows artifact validation pass.

## Email-only customer import defaults — v1.0.0.1.40

Before importing, optionally open **Settings → Customer Defaults**. Set a Default customer name if all imported rows should use the same name. Leave it blank to use an explicit imported name when present and otherwise the email username/local-part. Set a two-letter Default customer country if desired; leave it blank to preserve an explicit imported country and use `US` when country is missing. This makes an email-only list provider-ready before Task snapshot creation.

For Refrens live acceptance, use one controlled recipient first. A successful automated Task result is still not the final P11 gate; confirm the invoice exists in Refrens and that the controlled mailbox received the invoice email.

## v1.0.0.1.40.1 Refrens send acceptance

A Refrens Task now treats invoice creation and invoice-email triggering as separate steps. The Task is provider-successful for a recipient only after the explicit invoice email endpoint accepts the request. If invoice creation succeeded but email triggering definitively failed, **Retry Failed** reuses the existing invoice ID and retries only the email trigger. For production acceptance, still verify that the controlled recipient mailbox actually receives the invoice.

## v1.0.0.1.40.2 Agiled/Refrens usage note

- **Agiled:** Add Account/Re-test can now verify an Agiled API key with the current Bearer-authenticated `/public/v1/me` safe-read. A verified Agiled account still cannot create/run an Invio Task because the supplied current OpenAPI does not publish the invoice field mapping or invoice email/send operation required for safe execution.
- **Refrens:** if Live Logs show `Not allowed to send mail` followed by `CODE 400`, the invoice was created but Refrens rejected the API email operation. Do not repeatedly Retry Failed or create replacement Tasks to work around that rejection. Resolve API mail permission/capability with Refrens first, then retry only the preserved failed recipient using Invio's existing duplicate-invoice-safe flow.


## Odoo production provider — v1.0.0.1.40.2

The first production release ships Odoo Provider v1.0.0 under `providers/plugins/odoo/`. Load it explicitly from **Providers → Load Provider**, review the trusted-code warning, add an Odoo account and run API Test. Start live use with one controlled recipient. The owner has accepted a real Odoo end-to-end invoice send as the production provider path for this release.
