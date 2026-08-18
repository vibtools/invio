## Current Phase-4 implementation candidate — v1.0.0.1.50

Invio v1.0.0.1.50 implements the owner-approved **Deterministic Dynamic Tags V1** scope over the CI-verified v1.0.0.1.49.9 baseline. Supported exact tags are `#NAME#`, `#EMAIL#`, `#R5#`, `#R11#`, `#DATE#`, `#DATE-NAME#`, and `#YAAR#`. Unknown tag-like text remains literal. Date values are frozen from the Task-creation UTC reference; deterministic numeric tags are stable for the same Task+recipient through retry, Resume Remaining, Retry Failed, and restart recovery. Rendering is limited to Settings Default Customer Name provenance plus Invoice Template Memo, Footer, Customer Note, Terms, and Item Description. Recipient email is never changed.

Phase 4 advances operational storage additively from schema v6 to **schema v7** so Settings-default dynamic-name provenance and the immutable Task Dynamic Tags version/UTC reference survive restart. Existing v6 Customer/Task rows migrate with Dynamic Tags disabled, preserving pre-Phase-4 literal behavior for already captured executions. No new UI page, preview workflow, provider-specific hidden tags, provider API capability, WorkerManager architecture, TLS behavior, Phase-2 circuit breaker, or Phase-3 scheduling behavior is introduced. GitHub Windows CI remains a post-push acceptance gate; it is not claimed here.

## Current baseline candidate — v1.0.0.1.49.9

v1.0.0.1.49.9 is a narrow Windows CI correction over the accepted Phase-3 implementation. GitHub Actions run `32097949119` proved the Linux job and all Phase-3 runtime/UI tests green; the Windows job failed only because the new schema-v5→v6 migration test fixture left its own SQLite connections open until temporary-directory cleanup. The fixture now explicitly closes those test connections. Production `DomainStore`, SQLite schema v6, Sending & Retry controls, provider rate ceilings, Phase-1 TLS, Phase-2 fatal-limit semantics, WorkerManager/QThread ownership and all provider/UI workflows remain unchanged.

## Current baseline candidate — v1.0.0.1.49.8

Phase 3 adds bounded Sending Scheduler / Retry / Delay controls without changing provider business payloads, Phase-1 TLS trust, Phase-2 fatal-limit circuit-breaking, WorkerManager/QThread ownership, or Dynamic Tags. New Tasks freeze their sending controls into the immutable execution snapshot and SQLite schema v6 persists those controls across restart. Defaults preserve v1.49.7 behavior: 30-second Task network timeout, three total automatic attempts, zero additional recipient delay, Stripe 20 requests/second/account, Refrens 1 request/second/account, and no invented Odoo numeric scheduling policy. Provider `Retry-After`, internal retry taxonomy/backoff/jitter/cooldowns and non-idempotent no-blind-replay rules remain authoritative.

## Current baseline candidate — v1.0.0.1.49.7

v1.49.7 corrects only the verified GitHub Actions P14 release-audit false negative from the v1.49.6 Windows build. Nuitka successfully compiled and executed the native `truststore` TLS backend in both OneDir and MSI smoke tests, but the final portable audit incorrectly required the original `Invio/truststore/__init__.py` source file. The audit now checks only stable portable resources while executable smoke gates remain the runtime proof. Phase-1 TLS and Phase-2 provider-limit behavior remain unchanged.

## v1.0.0.1.49.6 — Provider Fatal-Limit Circuit Breaker

Phase 2 adds a generic fail-safe external-provider batch circuit breaker. Odoo v1.0.1 uses it only for the proven daily email-limit condition and post-send `UNVERIFIED` evidence. The current non-idempotent recipient is preserved as Uncertain when required, untouched recipients stay Pending, no later recipient starts after the stop condition, and the existing Task card retains an actionable stop message. Phase-1 native Windows TLS remains intact; Phase 3 sending controls and Phase 4 Dynamic Tags remain deferred.

## v1.0.0.1.49.5 — Windows/RDP Native TLS Trust Correction

Phase 1 corrects a verified Windows/RDP TLS trust-chain compatibility defect in the shared HTTPS transport. Windows requests use the native OS trust store through `truststore`; certificate and hostname verification remain fail-closed. Provider business logic and all Phase 2-4 work remain unchanged.

## v1.0.0.1.49.4 — Provider IVX Windows Security & Compatibility Correction

`Invio v1.0.0.1.49.3 Provider IVX Package System V1` is the frozen parent baseline. Native Windows verification exposed two release-blocking defects: raw ZIP backslash paths were normalized by Python before the IVX validator inspected `ZipInfo.filename`, and the Providers page treated the new `ProviderManager.provider_logo_path()` capability as mandatory for legacy manager collaborators. The correction validates raw `ZipInfo.orig_filename`, keeps plugin-logo lookup additive via `getattr`, and adds non-GUI regression coverage so these contracts are checked even when PySide6 runtime tests are unavailable.

The same IVX-only forensic pass also closes verified package-boundary gaps: non-canonical path aliases and Windows-unsafe path components are rejected, unsupported ZIP compression is converted to a normal fail-closed IVX validation error, optional PNG logos receive structural/CRC/dimension checks before materialization, and the deterministic IVX builder validates its temporary archive before publishing the final `.ivx`. Task execution, WorkerManager, storage/schema, OAuth/Easy Onboarding, provider API/send logic, MSI/WiX and unrelated UI remain unchanged. Version mapping: application/tag `1.0.0.1.49.4` / `v1.0.0.1.49.4`, PE `1.0.1.4904`, MSI `1.1.4904`, wheel `1.0.0.1.49.4`.

## v1.0.0.1.49.3 — Provider IVX Package System V1

`Invio v1.0.0.1.49.2` is the frozen parent baseline. Provider distribution can now use a single `.ivx` file: a standard ZIP container with Invio's custom extension, root-level `provider.json`, conditional `adapter.py`, optional `logo.png`, and optional documentation/checksum files. `Load Provider` prefers `.ivx` while the existing direct `provider.json` path remains available for backward compatibility.

IVX import is non-executing and security-gated: archive paths, encryption, symlinks, duplicates/case collisions, CRCs, size/file-count limits and optional `SHA256SUMS.txt` are validated before safe staging. Packages are atomically materialized at `providers/packages/<provider_id>/`; executable adapter trust and P13 adapter validation remain at the separate Install step. Imported provider logos are used when valid, existing built-in provider icons remain unchanged, and missing/invalid plugin logos resolve to `assets/icons/providers/fallback.png`.

No Task, WorkerManager, storage/schema, Browser OAuth, Easy Onboarding, provider send/API semantics, MSI/WiX or unrelated UI behavior is changed. Version mapping: application/tag `1.0.0.1.49.3` / `v1.0.0.1.49.3`, PE `1.0.1.4903`, MSI `1.1.4903`, wheel `1.0.0.1.49.3`.

## v1.0.0.1.49.2 — Provider Easy Onboarding compatibility correction

`Invio v1.0.0.1.49.1 Provider Easy Onboarding V1` is the frozen parent baseline. This correction keeps Easy Onboarding optional at the Add/Edit Account UI boundary: an existing Browser-OAuth-only runtime collaborator that predates `supports_onboarding()` is treated as not supporting onboarding instead of raising `AttributeError` while the dialog is constructed. Full `ProviderRuntime` Quick Connect behavior is unchanged.

No provider Task/send semantics, External Provider Adapter v1 contract, Browser OAuth v1 flow, WorkerManager, Task state machine, delivery ledger, database schema, customer/template/report behavior, MSI/WiX behavior, provider bundles, dependency stack, or unrelated UI is changed. Version mapping: application/tag `1.0.0.1.49.2` / `v1.0.0.1.49.2`, PE `1.0.1.4902`, MSI `1.1.4902`, Python wheel `1.0.0.1.49.2`.

## v1.0.0.1.49.1 — Persistent Browser OAuth + Provider Easy Onboarding + MSI Launch Integration

`Invio v1.0.0.1.49` is the frozen parent baseline. This hotfix adds an optional, backward-compatible browser OAuth authorization contract for trusted P13 external providers and corrects the Windows MSI end-user launch entry without changing existing provider sending, Task, WorkerManager, storage schema or business logic.

Browser-auth-capable providers can open the system browser, validate `state`, use PKCE where declared, receive a loopback callback or validate a manually pasted HTTPS callback, exchange the authorization code, discover the authorized organisation/tenant/company/location, and place only refresh/bootstrap credentials into the existing Add Account form. After the account is saved, credentials remain protected by Invio's existing OS keyring boundary; provider adapters silently refresh access tokens and, where the provider rotates refresh tokens, persist the latest refresh token in protected storage. Existing manually configured provider credentials remain supported.

The MSI remains an unsigned per-user LocalAppData package by approved Signing Option C, so Windows may still display `Unknown Publisher`. The functional correction adds `Start Menu > Vib Tools > Invio`, verifies its target in CI, preserves the current install location/UpgradeCode, and removes the shortcut on uninstall.

Version mapping: application/tag `1.0.0.1.49.1` / `v1.0.0.1.49.1`, PE `1.0.1.4901`, MSI `1.1.4901`, Python wheel `1.0.0.1.49.1`.

### Provider Easy Onboarding V1

`v1.0.0.1.49.1` now includes an optional provider-driven **Easy Onboarding V1** contract. Providers that opt in classify credential values as user-required, user-choice, generated, discovered, or Invio-managed. Add/Edit Account shows only unavoidable user inputs in Quick Connect mode; generated refresh tokens, provider organisation/tenant/company/location identifiers and managed resource IDs stay hidden while remaining available to the protected credential workflow. **Advanced / Manual Setup** preserves the existing raw-field path for backward compatibility.

Quick Connect composes the existing Browser OAuth flow with provider-controlled discovery/preparation and then runs the existing real API Test automatically. Provider-specific account choices use friendly labels while Invio stores the provider IDs. External Provider Adapter interface v1 and all Task execution/send semantics remain unchanged. The contract is generic: any future trusted external provider can declare `onboarding.interface_version = 1` and implement `prepare_account()` without changing the Accounts UI.

The companion v1.2.0 OAuth provider bundles use the same host contract: Zoho Books, Zoho Invoice, Xero, QuickBooks Online and Square. Zoho Books/Invoice reuse or create one deterministic `Invio Service` item; Xero safely discovers a usable sales account without changing the chart of accounts; QuickBooks reuses/creates `Invio Service` only when an Income account is unambiguous; Square derives location/currency configuration. Existing saved accounts are not forced to reconnect solely because of this host update.

## v1.0.0.1.49 — Provider/Settings Compact Headers + Template/Reports Table Layout Correction

UI-only correction on the frozen `v1.0.0.1.48.9` baseline. Providers and Settings retain their existing page/section hierarchy with compact search controls and reduced header spacing. Invoice Templates preserves all seven existing columns/row values/actions while widening the Actions cell safely and enabling explicit horizontal overflow handling. Reports preserves every Task Summary and Recipient Delivery History column/value and switches wide report tables to content-driven column widths with horizontal scrolling rather than hiding data. Backend/provider/storage/task behavior is unchanged.

## v1.0.0.1.48.9 — Customer Lists + Compact Header Standardization

Customer Lists now uses a compact scrollable list-navigation panel with inline count badges and row-scoped list actions. The Customers panel keeps `# / EMAIL / NAME / COUNTRY` and places Search, Country and Upload on one section row. The already-frozen compact Page Header / Section Toolbar hierarchy is also applied to remaining applicable UI pages. Backend/provider/storage/task behavior is unchanged.

# v1.0.0.1.48.8 Canonical Status Column Natural-Width Runtime Correction

`Invio v1.0.0.1.48.7` is the frozen parent state. The only confirmed failing Windows runtime contract was the Accounts `STATUS` column: it was fixed at 132px while the canonical shared badge reported a 180px natural width in the real PySide6 environment. `v1.0.0.1.48.8` removes that unsafe fixed-width assumption and lets the existing canonical table-status item size hint drive the Status column through `QHeaderView.ResizeToContents`.

The shared v1.48.7 status renderer, one-visible-badge rule, colors, table data, filters, pagination, row actions, backend/provider/storage/task behavior and every unrelated page remain unchanged.

Version mapping: application/tag `1.0.0.1.48.8` / `v1.0.0.1.48.8`, PE `1.0.1.4808`, MSI `1.1.4808`, Python wheel `1.0.0.1.48.8`.

# v1.0.0.1.48.7 Global Status Badge Rendering & Table Cell Alignment Fix

`Invio v1.0.0.1.48.6` is the frozen parent baseline. `v1.0.0.1.48.7` fixes status presentation through the existing shared UI layer: `widgets.py` now owns canonical status tone mapping, status display text, badge refresh, and `set_data_status_cell()` for table cells. Status table cells keep the raw value only in `Qt.UserRole`/tooltip metadata while the visible cell text is rendered exactly once by the badge widget.

Accounts, New Task account selection, Reports task status, and Reports delivery status consumers now use the shared table-status renderer. Task and Provider status badges share the same semantic mapping path. Existing account/provider/task/storage/API/business behavior, action menus, pagination, filtering and layouts remain unchanged.

Canonical semantic presentation remains inside the approved Vib Tools palette: success uses the existing `#22C55E` token, warning uses `#FCD34D`, danger uses `#F87171`, neutral uses the existing neutral border/text tokens, and primary interaction remains `#2563EB`.

Version mapping: application/tag `1.0.0.1.48.7` / `v1.0.0.1.48.7`, PE `1.0.1.4807`, MSI `1.1.4807`, Python wheel `1.0.0.1.48.7`.

# v1.0.0.1.48.6 Accounts Page — Compact Table / Action Menu Correction

`Invio v1.0.0.1.48.5` is the frozen parent baseline. `v1.0.0.1.48.6` changes only the **Accounts** page presentation and directly required verification/release records. The flat table is rebalanced for compact scanning, the `ACTION` header/control is fully contained, and the existing row `QMenu` is anchored inward and bounded to both the Invio window and current screen available geometry.

Accounts-only status presentation now uses the owner-approved Vib Tools semantic values: success remains the existing success token (`#22C55E`), warning is `#FCD34D`, danger is `#F87171`, and primary interaction remains `#2563EB`. These are scoped to `AccountsDataTable`; global token values and other pages are unchanged. Search, Provider/Status filters, pagination, rows-per-page, Edit/Re-test/Delete callbacks, account/provider data contracts, API verification, protected credentials, task reservations, storage, provider runtime and WorkerManager behavior remain unchanged.

Version mapping: application/tag `1.0.0.1.48.6` / `v1.0.0.1.48.6`, PE `1.0.1.4806`, MSI `1.1.4806`, Python wheel `1.0.0.1.48.6`.

# v1.0.0.1.48.5 Accounts Page — Compact Flat Account Table & Semantic Status UI

`Invio v1.0.0.1.48.4` is the frozen parent baseline. `v1.0.0.1.48.5` changes only the **Accounts** page presentation: the expandable Provider → Account hierarchy is replaced by one flat Account table; the page header keeps only **Add Account**; **Added Accounts List + Search + Provider filter + Status filter** share one compact toolbar row; existing pagination/rows-per-page remain; and **Edit / Re-test / Delete** move to each account row under a compact `⋯` menu.

Account/provider relationships, verification data, API-test behavior, protected credentials, task reservations, callbacks, filtering semantics, persistence, provider runtime, WorkerManager and all non-Accounts UI remain unchanged. Status badges reuse the existing palette with green success/ready states, amber verification attention, red provider/error states, gray unavailable states and existing blue primary/selection styling.

Version mapping: application/tag `1.0.0.1.48.5` / `v1.0.0.1.48.5`, PE `1.0.1.4805`, MSI `1.1.4805`, Python wheel `1.0.0.1.48.5`.

# v1.0.0.1.48.4 Compact Add Task Modal UI Redesign

`Invio v1.0.0.1.48.3` is the frozen parent baseline. `v1.0.0.1.48.4` changes only the **Tasks → New Task** modal composition: Provider + account availability/status filters + account search share one compact toolbar row; the existing account table uses a stable 250px scrollable viewport with its existing pagination; Invoice Template + Customer List + Cancel + Create Task share one compact bottom row. Existing colors, typography, borders, custom title bar, dialog shadow, account eligibility, selection, validation, payload, Task creation workflow, provider/runtime/storage/WorkerManager behavior and every other page remain unchanged.

Version mapping: application/tag `1.0.0.1.48.4` / `v1.0.0.1.48.4`, PE `1.0.1.4804`, MSI `1.1.4804`, Python wheel `1.0.0.1.48.4`.

# v1.0.0.1.48.3 End-to-End CI/CD & Release Pipeline Stabilization Candidate

`Invio_v1.0.0.1.48.02_CL_FIx_Baseline.zip` is the owner-frozen Official Baseline. `v1.0.0.1.48.3` is limited to GitHub CI/test/build/release stabilization. GitHub Actions run `31516505105` confirmed that the Linux Qt runtime correction is effective and that the real PySide6 popup interaction suite passes on both Linux and Windows. The remaining regression was repository-contract only: the v1.48.02 CI correction partially unignored the private `project/` tree so four root-cause records could be checked in a public checkout. That made `project/` exist in GitHub Actions and unintentionally activated every historical private-project assertion, producing 21 repository-contract failures before the Windows build stages could start.

`v1.0.0.1.48.3` restores the established public/private verification boundary: `/project/` remains fully Git-ignored, tracked public records are mandatory in CI, and private project records are checked only when the full private baseline is present. The four v1.47/v1.48 private verification checks now use the same conditional pattern already established by the earlier repository contracts. Linux Qt offscreen dependencies, real `QApplication` / `QMessageBox.exec()` / `QTimer` lifecycle coverage, wheel, Nuitka OneDir, WiX MSI, checksum audit, artifact upload and exact-tag GitHub Release workflow remain otherwise unchanged.

No Task, provider, storage, customer/invoice, settings, WorkerManager, UI layout/color/popup behavior, schema, dependency or business-logic behavior is changed. Version mapping: application/tag `1.0.0.1.48.3` / `v1.0.0.1.48.3`, PE `1.0.1.4803`, MSI `1.1.4803`, Python wheel `1.0.0.1.48.3`.

# v1.0.0.1.48.02 Global QMessageBox / Popup Lifecycle Hotfix Candidate

`Invio v1.0.0.1.48.01` is the owner-frozen Official Baseline. `v1.0.0.1.48.02` fixes the global app-owned `QMessageBox` custom-chrome lifecycle regression: every Invio message box is forced onto Qt's widget-backed path, and custom chrome reacquires the live Qt-owned layout only after frameless/translucent window mutation. Existing warning/error/info/confirmation business flows, Task state, providers, storage, customer/invoice logic and unrelated UI remain unchanged. Real PySide6 interaction tests are included and execute whenever the runtime dependency is available (including the normal dependency-installed CI jobs).

GitHub CI correction: the Linux `ubuntu-24.04` test job now installs the Qt runtime libraries required by the real PySide6 popup interaction suite and runs it with the offscreen QPA platform. The repository contract also narrowly tracks the four historical root-cause verification records that the tests read from `project/research/`; the remainder of `project/` stays ignored. This is CI/test-artifact only and does not change application runtime behavior.

Python wheel packaging note: the public application/tag identity remains `1.0.0.1.48.02` / `v1.0.0.1.48.02`; Python packaging canonically emits wheel metadata/filename version `1.0.0.1.48.2`, which P14 validates explicitly. Portable/MSI naming and PE/MSI identities remain on the public mapping.

# v1.0.0.1.48.01 Task Close Confirmation Hotfix Candidate

`Invio v1.0.0.1.48.0` is the owner-frozen Official Baseline. `v1.0.0.1.48.01` changes only the Tasks subsystem Close Task confirmation boundary: the confirmation is forced onto Qt's widget-backed `QMessageBox` path before custom chrome/properties are applied, restoring reliable Windows confirmation and allowing the existing verified backend close/release pipeline to execute. Task state rules, WorkerManager, storage, provider runtime, delivery ledger, account reservations, all other confirmation workflows and unrelated UI remain unchanged.

# v1.0.0.1.48.0 Dialog Chrome Polish Candidate

`Invio v1.0.0.1.47.0` is the owner-frozen Official Baseline. `v1.0.0.1.48.0` changes only custom Main/Dialog chrome presentation: compact right inset after Close, subtle bordered/shadowed app-owned dialog separation, and removal of duplicated body-level dialog titles. All fields, actions, page/data-grid UI, runtime/provider/storage/task/customer/invoice/settings behavior remain unchanged.

# v1.0.0.1.47.0 Vib Tools Desktop Design System Candidate

`Invio v1.0.0.1.46.0` is the owner-frozen Official Baseline. `v1.0.0.1.47.0` refines only the approved desktop UI/UX system: one global frameless application header, grouped SVG-based sidebar navigation, standardized app-owned dialog chrome/body/footer/overlay, centralized compact component states, and aligned Accounts / Customer Lists / Invoice Templates presentation. Existing provider/runtime/storage/task/customer/invoice/settings behavior remains unchanged.

# v1.0.0.1.46.0 Custom Window Chrome Candidate

`Invio v1.0.0.1.45.0` is the owner-frozen baseline. `v1.0.0.1.46.0` changes only the main-window and application-owned dialog title bars: native Windows chrome is replaced by compact branded frameless title bars while existing window controls, modal workflows, content, provider/runtime behavior and all page UI remain unchanged.

# Invio

**Invio** is a Vib Tools desktop application for provider-based invoice automation. **`v1.0.0.1.44.0` is the owner-frozen Official Baseline.** **`v1.0.0.1.45.0` is the scope-locked Providers Page transient-window/card-layout fix candidate.** It prevents newly constructed provider cards from being shown as parentless top-level windows before grid re-parenting, moves the compact Available/Verified badge below the provider name, and reduces only the Provider card height implied by that header compaction. Provider/runtime/storage/business behavior and every non-Providers UI surface remain unchanged.

## v1.0.0.1.45.0 Providers Page Transient-Window Fix Candidate

- Fixes the brief white `Invio` window seen during application construction and on each Providers Page refresh by ensuring provider cards become visible only after `QGridLayout` has re-parented them into the Providers Page host.
- Moves `Available` / `Verified` from below the logo to directly below the Provider Name.
- Uses a compact 18px provider-status mark and reduces Provider card height from 220px to 194px; logo size, minimum card width, search, responsive grid, description ellipsis, version footer and Install/Uninstall workflows are preserved.
- Adds no provider API/runtime, storage, Task, plugin, dependency, schema, page-navigation or non-Providers UI change.

## v1.0.0.1.44.0 Intro/Subtitle Cleanup Candidate

- Removes the static `description` visual row from shared page headers while retaining the frozen helper signature.
- Removes static card/section subtitle rows from shared Cards while retaining the frozen helper signature.
- Removes the one static Task-card subtitle identified in the owner screenshots.
- Preserves provider package descriptions and dynamic operational/status/validation text.
- No layout redesign, data-grid change, provider/runtime/storage/business change, dependency or schema change is included.

## v1.0.0.1.41.1 Providers Page Final UI Polish Candidate

- Adds a live Search providers field directly above the card grid.
- Replaces neutral initials with packaged Stripe, Refrens, Agiled and Odoo logo assets rendered at 40px.
- Moves status below the logo and uses the owner-approved `Verified` text for installed provider packages; Available remains the non-installed state.
- Moves the small provider version text to the card footer bottom-right.
- Removes visible capability chips and visible runtime/credential metadata from cards.
- Keeps actions bottom-anchored; Providers-page Uninstall now uses primary-theme blue styling rather than the global danger/red treatment.
- Retains v1.41 card height `220px`, minimum width `280px`, `16px` spacing, 2–4 responsive columns, three-line description ellipsis and `#1A212E` hover surface.
- No provider/runtime/storage/threading/business/API behavior changes are included.

## v1.0.0.1.43.0 Global Data Tables + Lists + Fonts Candidate

- Uses the existing Segoe UI Variable/Segoe UI family; data-page titles/cards move to the approved 500-weight hierarchy while table headers remain 11px/600.
- Adds reusable 28px Data Grid search/filter/footer controls and 10/25/50 in-memory pagination without backend pagination or sorting.
- Standardizes 28px table headers, 30px rows, subtle zebra striping/hover, no vertical grid lines, semantic status pills and full-value cell tooltips.
- Adds presentation filters/search/pagination to Accounts, Customer Lists/Records, Invoice Templates, both Reports tables, Invoice Items and New Task Accounts.
- Keeps Accounts as a QTreeWidget with stronger provider-group hierarchy, 16px provider logos and compact displayed API-test timestamps.
- Converts only New Task Accounts from QListWidget to a four-column QTableWidget and caps the record surface at 250px while retaining verified/reserved account gates.
- Fixes the Invoice Templates Actions clipping at the approved compact 80px width.
- No provider/runtime/storage/settings/business behavior changes are included.

## v1.0.0.1.41 Providers Page UI/UX Candidate

- Providers Page root background (`#090D14`) and 14px page padding are unchanged.
- Provider cards are compact fixed `220px` height with `280px` minimum width, `16px` internal padding, and `16px` grid gaps.
- The provider grid reflows from 2 to 4 columns according to available content width without introducing a new UI/layout framework.
- Card headers use a neutral `32x32px` provider-initial placeholder, title/version identity block, and right-aligned Installed/Available status.
- Provider descriptions are limited to three visible lines with right ellipsis while the complete description remains in the tooltip.
- Runtime/effective capabilities are rendered as compact chips; runtime-adapter state plus credential count is collapsed to one compact metadata line.
- Install/Uninstall remains the same real action and is bottom-anchored with stretch inside every equal-height card.
- Hover changes only the card surface from `#111722` to `#1A212E`; border semantics remain unchanged.
- `Load Provider` remains the same trusted-provider workflow and receives only a compact provider-page-specific visual emphasis.
- No provider/business/runtime/storage/threading/API/configuration behavior changes are included.

## v1.0.0.1.40.2 First Production Release

- **Production-certified provider path:** Odoo Provider v1.0.0 through the frozen P13 trusted external-adapter interface.
- **Owner live result:** real Odoo invoice creation/posting and email sending completed successfully from Invio.
- **Distribution evidence:** the pre-plugin v1.40.2 Windows CI/distribution path passed. The first final plugin-inclusion CI run exposed only a cross-platform Odoo bundle checksum checkout issue; `.gitattributes` now freezes `providers/plugins/odoo/**` to LF bytes. The corrected final commit must receive green non-tag CI before tagging.
- **Bundled plugin source:** `providers/plugins/odoo/` ships the exact validated Odoo bundle with source, manifest, checksums and live-test documentation. It remains an external trusted-code plugin and is **not auto-installed**; users must explicitly Load Provider and approve it.
- **Refrens:** API Test and invoice creation work; API mail is provider-rejected with `HTTP 400: Not allowed to send mail`, so Refrens email delivery remains unaccepted and non-blocking by owner decision.
- **Agiled:** verified Bearer API Test only; Task sending stays fail-closed.
- **P14:** COMPLETE by owner production acceptance. **P11:** IMPLEMENTED / live Refrens acceptance deferred. The release is production-ready specifically with the supported live Odoo path and the documented provider limitations above.

## Current Application Scope

- **Dashboard**: live summary for installed providers, accounts, templates, customer count, task activity, account reservations, and next setup/action.
- **Accounts**: provider-grouped accounts with Add/Edit/Re-test/Delete lifecycle controls, real non-blocking API verification, durable verification health, protected credentials, and task reservation safety.
- **Invoice Templates**: reusable invoice-only content. Templates never store customer, billing, shipping, or payment details.
- **Customer Lists**: independent named bulk-customer lists. Email is mandatory. During import, Settings can supply a default customer name/country; otherwise missing names use the email local-part and missing countries use `US`. CSV/TSV/XLSX/XLSM structured imports and legacy email-only imports remain supported.
- **Tasks**: installed provider -> one or more available verified accounts -> invoice template -> customer list, with P05 immutable execution inputs and P07 deterministic First Run / Resume Remaining / Retry Failed state semantics. One account cannot belong to two open tasks.
- **Providers**: manifest-based install/load/uninstall workflow with P06 declared-vs-executable capability visibility, packaged-runtime reconciliation, and P13 optional executable external adapters. A trusted external bundle is `provider.json` plus fixed sibling `adapter.py`; manifest-only providers remain non-executable, executable code requires explicit user confirmation, and invalid/missing adapters fail closed. Stripe/Refrens remain on the static packaged adapter registry; Agiled has API Test only. The validated Odoo Provider v1.0.0 ships under `providers/plugins/odoo/` as an explicitly trusted external P13 bundle and is not auto-installed. A provider is selectable in Accounts and Tasks only while installed.
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
- truststore 0.10.4+ (<0.11)

P02 adds `keyring>=25.7,<26`. The current keyring release line supports Python 3.12 and provides the approved system-keyring APIs used by Invio. Provider HTTP calls continue to use Python `urllib`; v1.49.5 adds `truststore>=0.10.4,<0.11` only as the Windows-native certificate verification backend for that shared transport.

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
- Current correction-candidate release notes: `docs/release-notes/1.0.0.1.40.md`

## Private Project Material

`project/` contains private development, architecture, scope-lock, forensic, phase, and baseline records. It remains Git-ignored and is not public documentation.

## Production Readiness Program

`v1.0.0.1.40.2` is the owner-frozen **first production release**. The owner accepted the exact Odoo external-provider live path after successful account verification, invoice creation/posting and email sending, and accepted the green Windows distribution pipeline as the native packaging evidence for P14. P14 is therefore **COMPLETE by explicit owner production acceptance**. P11 remains a separate Refrens-specific live acceptance item and is **DEFERRED/non-blocking** for this release because the provider returns `HTTP 400: Not allowed to send mail`; this release does not claim Refrens email delivery. The production-certified live send path for this release is Odoo Provider v1.0.0.

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


## v1.0.0.1.31 P12 Verification Correction

The v1.0.0.1.30 P12 release was re-audited against its approved privacy and support-reconciliation contract. v1.0.0.1.31 fixes JSON-style named secret redaction (for example quoted `accessToken`, `appSecret`, `api_key`, `secret_key` and `token` fields) and makes recipient report acceptance fail closed unless durable provider send-stage evidence actually proves acceptance. Unresolved mutating operation history remains `Uncertain`, and conflicting historical account assignment evidence causes recipient reporting to fail closed instead of selecting a misleading latest value. P12 remains complete; P11 live Refrens acceptance remains pending.

## v1.0.0.1.32 P13 Executable External Provider Adapter Contract

P13 makes `Load Provider` truthful for future executable integrations. An external manifest may optionally declare a `runtime_adapter` interface-v1 contract and ship a fixed sibling `adapter.py`. Invio requires explicit trusted-code confirmation before installation, validates staged adapter bytes before atomic registry replacement, rejects validation-time byte mutation, validates provider/interface/adapter/profile/capability identity, contains import/entrypoint failures, rejects/restores persistent `sys.path` mutation, and reports `Executable`, `Manifest only`, `Missing`, or `Incompatible` runtime state. External API Test and Task execution stay inside the existing P01/P05/P06/P08/P10/WorkerManager contracts: API Test must complete a host-managed `SAFE_READ`; adapter task inputs are isolated from mutable application template state; and recipient success requires a successful host-managed mutation with a matching final stage. Host-managed `SAFE_READ`, `IDEMPOTENT_MUTATION`, and `NON_IDEMPOTENT_MUTATION` requests enforce retry/idempotency/uncertainty behavior, including durable `Uncertain` recovery after successful non-idempotent provider mutation when final recipient state was not safely committed. No dependency is auto-installed and this in-process model is explicitly **not a sandbox**. SQLite remains schema v5 with exactly the existing three P10 ledger tables. P11 live Refrens acceptance remains pending.

## v1.0.0.1.33 P13 Verification Correction

The uploaded v1.0.0.1.32 baseline was re-audited against the approved P13 executable external-provider contract. Two edge defects were reproduced and corrected without expanding P13: adapter metadata access after `create_adapter()` could raise a `BaseException` such as `SystemExit` outside the existing import/entrypoint containment boundary, and external-provider uninstall could remove the manifest before a later adapter-file failure, leaving a half-uninstalled registry. v1.0.0.1.33 converts post-entrypoint metadata failures into fail-closed `Incompatible` adapter state and uses active-name staging plus rollback for uninstall. P13 remains COMPLETE; P11 live Refrens acceptance remains pending.


## v1.0.0.1.34 P14 Certification Candidate

P14 repairs the current setuptools wheel contract without introducing a new installer framework: the existing `src.core.settings` package, the three packaged provider manifests and `assets/icons/checkmark.svg` are now included in the wheel, while `src/core/paths.py` resolves the same top-level resource layout in source checkouts and installed wheels. CI retains Ubuntu regression testing and adds a Windows/Python-3.12 job that builds and clean-installs the wheel and runs a native offscreen PySide6/keyring/resource/three-QThread smoke. Local deterministic certification adds a 10,000-customer import, 1,000-recipient injected Stripe execution soak and real subprocess crash-after-write-ahead recovery test.

The Windows job has **not been executed for this unpushed candidate**, and no owner live Stripe/Refrens credentials or controlled recipient mailbox were supplied. Therefore P11 live acceptance remains pending, P14 is **not complete**, and `v1.0.0.1.34` must not be described as production-ready.


## v1.0.0.1.35 P14 Windows Distribution and Release Pipeline

The owner-approved v1.35 distribution update keeps the existing wheel/native certification path and adds a Windows x64 **Nuitka 4.1.3 OneDir** build, versioned portable ZIP, **WiX Toolset 6.0.2** per-user MSI, and `SHA256SUMS.txt`. Normal pushes/PRs run the build and upload the Windows distribution artifact. An exact matching version tag such as `v1.0.0.1.35` waits for the Ubuntu and Windows gates and then publishes the portable ZIP, MSI, wheel and checksums to the GitHub Release. Build/test jobs use read-only repository permissions; release-write permission exists only on the tag-gated release job.

The MSI installs under `%LOCALAPPDATA%\Vib Tools\Invio` so the frozen P13 provider registry remains writable without elevation. The portable OneDir keeps the same application-root provider workflow. Nuitka and WiX are CI build tools only and are not added to `requirements.txt`.

This build/release pipeline does **not** close P11 or P14. Until the exact Windows workflow passes after push and owner-controlled Stripe/Refrens live acceptance evidence is recorded, production-ready remains **NO**.


## v1.0.0.1.36 P14 GitHub Actions CI Verification Correction

The v1.35 GitHub Actions run `31371279808` failed before wheel/Nuitka/WiX packaging because the broad `.gitignore` rule `build/` also ignored the approved source directory `scripts/build/`; the helper files existed in the v1.35 source baseline but were absent from commit `12ef4800a75a993da3899399882f0e44daccd4df`. v1.36 explicitly re-includes that source directory while keeping generated `build/` and `dist/` ignored, and re-publishes the five v1.35 helper-source entries byte-identically for GitHub reconciliation.

Windows also exposed file-handle ownership defects during regression cleanup. The P14 crash-recovery verification now explicitly closes its direct SQLite query handle, and `DomainStore._connect()` closes a partially initialized connection if setup fails before return. SQLite schema v5, provider send/business logic, WorkerManager/Task architecture, P13 interface v1, runtime dependencies and UI/UX remain unchanged. Local v1.36 regression is **381/381 PASS** and the repository audit passes; P14 remains **CERTIFICATION PENDING** until the exact v1.36 GitHub Windows workflow executes successfully.


## v1.0.0.1.37 P14 WiX Version Verification Correction

GitHub Actions run `31374749523` / Windows job `93411358955` reached the WiX setup stage after the full 381-test audit, wheel build/install, native PySide6/keyring/resource smoke, Nuitka OneDir build, portable preparation and compiled startup smoke all passed. `dotnet tool install --global wix --version 6.0.2` succeeded, but `wix --version` returned `6.0.2+b3f3403`. The v1.36 workflow compared that informational string directly with `6.0.2` and incorrectly raised a stale-version error.

v1.37 keeps WiX pinned at `6.0.2` and strips only the optional `+build-metadata` suffix for the verification comparison; a different canonical core version still fails closed. No installer architecture, provider behavior, runtime dependency, schema, Task/WorkerManager contract, UI/UX or release topology changes are introduced. P11 remains live-acceptance pending and P14 remains certification pending until the exact v1.37 Windows workflow completes successfully.


## v1.0.0.1.38 P14 WiX Debug-Symbol Release Inventory Correction

GitHub Actions run `31386258538` / Windows job `93447256779` passed the full 383-test audit, wheel/native smoke, Nuitka OneDir build/startup, WiX installation, MSI build and MSI install/run/uninstall smoke. The next release-assembly step failed because WiX emitted its default sibling `.wixpdb` debug-symbol file beside the MSI. The existing checksum writer correctly checksummed every file in `dist/release`, while the release auditor correctly allows only the approved portable ZIP, MSI and wheel payloads plus `SHA256SUMS.txt`.

v1.38 preserves both fail-closed contracts and adds WiX's documented `-pdbtype none` switch to the existing MSI build command. The approved release topology remains portable ZIP + MSI + wheel + checksums; no debug-symbol artifact is published. P11 and P14 acceptance status remains unchanged until the exact v1.38 external workflow and owner-controlled live-provider gates pass.


## Historical acceptance wording retained for audit compatibility

Historical phase records before the explicit v1.0.0.1.40.2 production acceptance used the statements **P11 is IMPLEMENTED / LIVE ACCEPTANCE PENDING** and **P11 remains IMPLEMENTED / LIVE ACCEPTANCE PENDING**. In the original Markdown contract those appeared as: `P11 is **IMPLEMENTED / LIVE ACCEPTANCE PENDING**` and `P11 remains **IMPLEMENTED / LIVE ACCEPTANCE PENDING**`. They remain historical evidence only; the current release status is P11 **DEFERRED/non-blocking**, not completed.
