## Current UI Update — v1.0.0.1.48.5

Accounts now use one compact flat account table with one-row search/provider/status controls, semantic status badges, existing pagination, and per-row `⋯` actions. No account/backend workflow changed.

## Previous UI Update — v1.0.0.1.48.4

The Tasks → New Task dialog now uses the approved compact single-toolbar / scrollable-account-grid / single-bottom-row layout. Workflow and backend behavior are unchanged.

## v1.0.0.1.48.3 CI/CD Stabilization

The current candidate corrects only the GitHub CI/repository-contract boundary discovered in run `31516505105`. Linux Qt/PySide6 runtime tests already pass; the remaining failure came from partially publishing the private `project/` tree, which activated historical private-only checks in clean Actions checkouts. `v1.0.0.1.48.3` restores the established private-project contract and keeps the existing wheel, Nuitka, WiX MSI, checksum, artifact and exact-tag release pipeline unchanged.

## v1.0.0.1.48.02 Popup Lifecycle Hotfix

The current candidate repairs all existing Invio-owned warning/error/info/confirmation message boxes after the custom-window-chrome refactor. Business behavior is unchanged; the repair is limited to Qt widget selection, live-layout ownership, and direct interaction regression testing.

## v1.0.0.1.48.01 Task Close Hotfix

The current candidate fixes only the Tasks-page `Close Task` confirmation path on Windows while preserving the existing backend close/release engine and every unrelated workflow.

## v1.0.0.1.48.0 Current UI Candidate

Parent baseline: `v1.0.0.1.47.0`. The candidate polishes only custom Main/Dialog chrome and app-owned dialog title/separation presentation. See `release-notes/1.0.0.1.48.0.md`.

## Current UI Candidate — v1.0.0.1.47.0

The current UI candidate builds on the owner-frozen `v1.0.0.1.46.0` baseline and standardizes the application shell, navigation, app-owned dialogs and shared visual states without changing business workflows.

## v1.0.0.1.46.0 UI candidate

Custom branded frameless chrome replaces the native white Main Window and application-owned dialog title bars only. See `release-notes/1.0.0.1.46.0.md`.

# Invio Documentation

Current UI baseline/candidate chain: **v1.0.0.1.44.0 is owner-frozen; v1.0.0.1.45.0 is the Providers Page transient-window/card-layout fix candidate.** The candidate prevents provider cards from becoming transient top-level windows before grid re-parenting and relocates/compacts the existing Available/Verified mark; runtime/business behavior is unchanged.

- `release-notes/1.0.0.1.45.0.md` - Providers Page transient-window/card-layout fix candidate.

Current UI baseline/candidate chain: **v1.0.0.1.42.0 is owner-frozen; v1.0.0.1.43.0 is the Global Data Tables + Lists + Fonts candidate.** The candidate adds compact in-memory search/filter/pagination and data-surface presentation only; runtime/provider/storage/task business behavior is unchanged.

- `release-notes/1.0.0.1.43.0.md` - Global Data Tables + Lists + Fonts candidate.


Official Production Baseline: **v1.0.0.1.40.2 — FIRST PRODUCTION RELEASE**. Owner-confirmed Odoo Provider v1.0.0 end-to-end invoice sending is the production-certified live provider path. P14 is complete by explicit owner acceptance; Refrens P11 live email acceptance is deferred/non-blocking.

Current UI baseline/candidate chain: **v1.0.0.1.41 is the owner-frozen Providers Page UI baseline; v1.0.0.1.41.1 is the final Providers Page polish candidate.** v1.41.1 adds search/filter, real provider logos and simplified card presentation only. Runtime/provider/storage/threading behavior remains unchanged.

Invio is a Vib Tools desktop application for provider-managed invoice automation. Current workflow:

**Provider -> Verified Account(s) -> Invoice Template -> Customer List -> Task -> Provider Runtime -> Reports/Live Logs**

P02 adds restart-durable non-sensitive operational state and OS-protected provider credentials. P04 adds backward-compatible customer records and structured import. v1.0.0.1.14 preserves the Windows-safe migration backup path. P05 makes Task execution inputs durable/immutable and v1.0.0.1.16 hardens those invariants. v1.0.0.1.17 added P06 provider capability/preflight validation; v1.0.0.1.18 verification-corrected its contracts; v1.0.0.1.19 adds P07 deterministic Task state/resend safety; v1.0.0.1.20 verification-corrects its worker-terminal/control integration; v1.0.0.1.21 adds the approved pre-P08 internal packaged-provider adapter registry and a fail-closed Agiled package without advancing the P07/P08 roadmap boundary; v1.0.0.1.22 forensic-verifies that exception without changing runtime behavior.

Use these documents:

- `getting-started/installation.md` - installation and protected-store requirements.
- `user/usage.md` - end-user workflow and restart behavior.
- `guides/invoice-templates.md` - reusable template fields and provider mapping.
- `guides/tasks.md` - task creation/control, reservation, and recovery.
- `guides/providers.md` - provider installation, API verification, and credential protection.
- `configuration/index.md` - Settings and durable storage locations.
- `developer/architecture.md` - modules, persistence, data flow, threading, provider adapters.
- `developer/ACTUAL_IMPLEMENTATION_STATUS.md` - exact working/partial/missing inventory.
- `developer/ERROR_HANDLING.md` - current error-handling inventory and remaining gaps.
- `troubleshooting/index.md` - operational/storage/provider issues.
- `release-notes/1.0.0.1.41.1.md` - Providers Page final UI polish candidate.
- `release-notes/1.0.0.1.41.md` - Providers Page compact UI/UX history.
- `release-notes/1.0.0.1.40.2.md` - first production release, Odoo live acceptance, and provider certification boundaries.
- `api/agiled-runtime.md` - verified Agiled Bearer API Test boundary and Task-send fail-closed rationale.
- `release-notes/1.0.0.1.38.md` - historical P14 WiX release-inventory correction release.
- `release-notes/1.0.0.1.27.md` - original P10 completion release.
- `release-notes/1.0.0.1.26.md` - P09 CI verification correction.
- `release-notes/1.0.0.1.25.md` - P09 production release.
- `release-notes/1.0.0.1.24.md` - P08 verification-correction release.
- `release-notes/1.0.0.1.23.md` - original P08 implementation release.
- `release-notes/1.0.0.1.15.md` - original P05 implementation.
- `release-notes/1.0.0.1.14.md` - Windows storage hotfix.
- `release-notes/1.0.0.1.12.md` - original P04 feature release.
- `release-notes/1.0.0.1.9.md` - P02 corrective release.

Detailed forensic reports, phase roadmap, phase completion ledger and update protocol are private records under `project/`.

## Current production phase

P10 is complete in `v1.0.0.1.27`. Production progress is **10/14** and the next separately approval-gated phase is **P11 - Refrens End-to-End Task Enablement**.

## P07 Task execution safety

P07 makes Start/Resume/Retry recipient selection deterministic. First Run is limited to pristine Ready Tasks; Stopped Tasks may Resume Remaining only when the exact current-session failed/pending set exists; Failed Tasks may Retry Failed only when the exact failed set exists; Completed Tasks cannot resend. Restart does not reconstruct recipient identities from counters, so continuation fails closed until P10.

## v1.0.0.1.20 P07 verification note

P07's send-set rules are unchanged. The correction makes late worker terminal signals deterministic against accepted Pause/Stop state, disables stale Pause/Resume/Stop controls when the Task thread has already ended, and reports a proven empty continuation set as empty rather than unavailable.

## v1.0.0.1.21 Provider Adapter / Agiled Boundary

Packaged provider runtime contracts now resolve through one internal registry. Agiled is installable as a packaged provider but remains non-executable until its current official API contract is revalidated. See the provider guide, API manifest guide and v1.0.0.1.22 historical release notes. Agiled remains fail-closed; P08 later completed in v1.0.0.1.23.

## v1.0.0.1.22 historical verification baseline

`v1.0.0.1.22` was the verification-corrected pre-P08 provider-adapter baseline. Agiled remained fail-closed and P08 was still pending at that release.

## v1.0.0.1.23 original P08 baseline

P08 Worker and Network Reliability is complete. Invio now classifies transient/permanent provider failures, retries bounded transient recipient failures with cooperative backoff and Retry-After handling, uses an explicit 30-second urllib timeout policy, isolates unexpected recipient failures, and closes only after active task QThreads finish. Production progress is 8/14; P09 is next.


## v1.0.0.1.24 historical P08 verification baseline

P08 remains complete. The forensic correction extends the transient-disconnect classifier to truncated HTTP response bodies and TLS EOF/clean-close interruptions, while retaining known HTTP status and Retry-After semantics when an error body is incomplete. Retry count/backoff, provider operations, shutdown architecture and all P09+ behavior remain unchanged. Production progress remains 8/14; P09 is next.


## v1.0.0.1.25 current baseline

P09 adds conservative multi-account scheduling without changing the frozen round-robin primary mapping. Stripe Task traffic is paced per account, temporary account/provider health is runtime-only, eligible failover is restricted to unattempted recipients, and attempted recipients are protected from cross-account replay. P10 persistence/recovery remains unimplemented.


## v1.0.0.1.26 current baseline

The P09 runtime remains unchanged. This verification correction fixes the public CI repository-contract boundary so tracked documentation is mandatory in GitHub Actions while intentionally private Git-ignored `project/` records are only checked when available in a full private baseline. Production progress remains 9/14 and P10 remains next.

## v1.0.0.1.27 current baseline

P10 advances SQLite to schema v5 and adds durable execution runs, per-run recipient outcomes, and provider-operation evidence. Supported Stripe Task operations are write-ahead recorded before transport, interrupted mutating operations recover as `Uncertain`, and restart-safe Resume Remaining / Retry Failed now use the durable ledger. P09 account binding, P08 retry/idempotency, the existing page inventory, Refrens P11 gate and Agiled fail-close remain unchanged.

## v1.0.0.1.28 current baseline

P10 remains complete and schema remains v5. This verification correction ensures unresolved mutating ambiguity survives across attempts/runs until exact same-stage/same-idempotency successful evidence reconciles it. Production progress remains **10/14**; P11 remains the next separately approval-gated phase.

## v1.0.0.1.29 P11 implementation candidate

Refrens Task execution is implemented behind explicit customer-data, canonical-host, scheduling, retry/no-replay and durable-ledger safety rules. Live owner acceptance has not yet been executed, so P11 remains live-acceptance pending and production progress remains 10/14.

## v1.0.0.1.30 P12 observability

P12 adds durable recipient reconciliation, provider-acceptance vs independent-email-delivery distinction, structured privacy-redacted logs, atomic spreadsheet-safe report exports and closed-history retention controls. P11 live Refrens acceptance remains separately pending.


## v1.0.0.1.31 P12 verification correction

P12 reporting/privacy was re-audited. Quoted JSON-style named secrets are now redacted centrally, and recipient support status can only claim provider acceptance when durable send-stage success proves it. Unresolved ambiguity and conflicting historical account evidence remain fail-closed/observable. Schema stays v5 and P11 live acceptance remains pending.

## v1.0.0.1.32 P13 executable external providers

P13 extends the existing Load Provider workflow with an optional executable `adapter.py` contract. Manifest-only providers remain visible but non-executable. Executable adapters require explicit trusted-code confirmation and exact interface/version/capability validation, and run through existing account verification, Task worker, preflight, retry and durable-ledger boundaries. See `guides/providers.md` and `api/provider-manifest.md`.

## v1.0.0.1.33 P13 verification correction

P13 remains complete. The correction contains adapter metadata failures that previously could escape startup and makes executable external-provider uninstall rollback-safe if its second registry move fails. External adapter interface v1, schema v5, provider behavior, dependencies and page inventory remain unchanged.


## v1.0.0.1.34 P14 certification candidate

P14 candidate documentation covers corrected setuptools wheel contents, source/install resource resolution, Windows CI/native-smoke tooling and deterministic local load/recovery gates. Live Stripe/Refrens and executed native-Windows evidence remain pending, so the release is not production-certified.


## v1.0.0.1.35 Windows distribution baseline

P14 distribution documentation now covers the approved Nuitka OneDir Windows executable folder, versioned portable ZIP, WiX per-user MSI, retained wheel, checksum manifest and tag-gated GitHub Release publication. The build/release implementation is not itself production certification: P11 live Refrens acceptance and P14 live/native gates remain pending.


## v1.0.0.1.36 GitHub Actions verification correction

The v1.35 distribution design is retained. v1.36 corrects the Git publication omission of `scripts/build/*` and Windows SQLite-handle cleanup failures found by GitHub Actions run `31371279808`. P14 remains certification-pending until the exact v1.36 Windows pipeline succeeds and remaining live-provider gates pass.


## v1.0.0.1.37 WiX version verification correction

The current source/build baseline fixes the GitHub Windows pipeline's false WiX stale-version failure. WiX stays pinned at `6.0.2`; the guard accepts the same canonical version when `wix --version` appends informational build metadata such as `+b3f3403`. P14 remains certification pending until the exact v1.37 Windows workflow completes and the separate owner-controlled live-provider gates are satisfied.


## v1.0.0.1.38 WiX release inventory correction

v1.38 preserves the existing Windows distribution design and suppresses WiX's default `.wixpdb` debug sidecar so the checksum manifest and distribution audit operate on the same approved portable/MSI/wheel payload set. P14 remains certification pending.
## Current v1.0.0.1.39 correction candidate

`v1.0.0.1.38` remains the Official released parent baseline. `v1.0.0.1.39` is a pre-release correction for the owner-observed compiled protected-credential storage failure after a successful Refrens API Test. It preserves the existing keyring/security/provider/storage architecture and adds explicit compiled keyring packaging plus OneDir/MSI CredentialStore round-trip verification. Do not tag/release the candidate until owner source/live and compiled-artifact validation pass.

## Current v1.0.0.1.40 live-correction candidate

Owner-frozen parent baseline is v1.0.0.1.39. v1.40 is limited to the live Refrens `terms` payload correction, email-only customer defaults, the reported dark list/menu/table surfaces, and owner app icon wiring. Do not tag/release until local source Refrens invoice/email acceptance and subsequent non-tagged compiled-artifact acceptance both pass.

## Current v1.0.0.1.40.1 error-fix candidate

The owner-frozen v1.40 baseline now proves real Refrens invoice creation but exposed a separate email-trigger gap. v1.40.1 uses Refrens' explicit post-create invoice-email endpoint, restores Settings to the shared frozen Vib Tools form/card spacing and typography, and removes the obsolete custom Nuitka keyring package config from CI. Agiled stays fail-closed; P11/P14 and production certification remain pending.

## v1.0.0.1.40.2 provider note

Agiled Account API Test is now executable against the exact current `GET https://api.agiled.ai/public/v1/me` Bearer endpoint. Agiled Task sending is still unavailable because the supplied OpenAPI does not define an invoice email/send operation or field-level invoice mutation schema. Refrens live API mail remains blocked by the provider response `HTTP 400: Not allowed to send mail`; Invio logs the provider HTTP status explicitly and does not convert the rejection into success.


## Current production baseline

**Invio v1.0.0.1.40.2** is the first owner-accepted production release. Odoo Provider v1.0.0 is the live end-to-end accepted invoice-send path. P14 is complete by explicit owner production acceptance; Refrens P11 live mail acceptance remains deferred/non-blocking and is not claimed as certified delivery.
