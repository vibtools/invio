# Roadmap

Current Official source/build baseline: **Invio v1.0.0.1.37 — P14 CERTIFICATION PENDING**.

Owner-frozen parent baseline: **Invio v1.0.0.1.36**. Production certification remains pending.

Last fully accepted pre-certification baseline: **Invio v1.0.0.1.33**.

P12 remains **COMPLETE / verification-corrected in v1.0.0.1.31**. P13 remains **COMPLETE / verification-corrected in v1.0.0.1.33**. P11 remains **IMPLEMENTED / LIVE ACCEPTANCE PENDING**. P14 packaging/certification and Windows distribution/release harness work is verification-corrected through `v1.0.0.1.37`, but P14 is **not COMPLETE** because owner live Stripe/Refrens evidence and an executed clean Windows/native PySide6/keyring certification run are still outstanding.

Roadmap entries are planning records, not implementation approval. Every production phase requires a separate explicit owner scope lock before code changes.

## Production Progress

- Documentation/governance phase `G0`: **COMPLETE**.
- Completed acceptance phases: **12 / 14** (P01-P10, P12 and P13).
- Completed: **P01**, **P02**, **P03**, **P04**, **P05**, **P06**, **P07**, **P08**, **P09**, **P10**, **P12**, **P13**.
- Outstanding acceptance gate: **P11 - Refrens End-to-End Task Enablement — IMPLEMENTED / LIVE ACCEPTANCE PENDING**.
- Owner explicitly froze `v1.0.0.1.29` and unlocked P12 despite the separate P11 live gate; that exception is recorded rather than retroactively marking P11 complete.
- Current status: **not production-certified**.

## Ordered Production Phases

1. **P01 - Real Account API Verification [COMPLETE]**: real non-blocking provider API Test and verified-account Task gates.
2. **P02 - Durable Domain Storage and Protected Credentials [COMPLETE in v1.0.0.1.8; verification-corrected in v1.0.0.1.9]**: SQLite operational persistence, versioned schema/transactions/recovery, and owner-approved OS-protected keyring credentials with no plaintext fallback.
3. **P03 - Account Lifecycle, Verification Health and Provider-Install Consistency [COMPLETE in v1.0.0.1.10; verification-corrected in v1.0.0.1.11]**: reservation-safe edit/delete/re-test, durable verification health, provider-uninstall preservation, and provider-installed Task execution gates.
4. **P04 - Customer Data Contract and Import Upgrade [COMPLETE in v1.0.0.1.12; verified/corrected in v1.0.0.1.13]**: backward-compatible customer records, structured/legacy imports, schema-v3 metadata persistence and customer-aware runtime snapshots while preserving Stripe email-only semantics.
5. **P05 - Immutable Task Execution Snapshot and Input Consistency [COMPLETE in v1.0.0.1.15; verification-corrected in v1.0.0.1.16]**: durable creation-time recipients/template/provider/account-basis snapshots, snapshot-derived totals, Start/Retry reuse, and fail-closed legacy Task migration.
6. **P06 - Provider Capability and Preflight Validation [COMPLETE in v1.0.0.1.17; verification-corrected in v1.0.0.1.18]**: reconcile declared/executable capabilities, protect packaged runtime IDs, validate provider/account/template/customer/endpoint contracts before side effects, and show precise correction messages.
7. **P07 - Task State Machine and Resend Safety [COMPLETE in v1.0.0.1.19; verification-corrected in v1.0.0.1.20]**: deterministic First Run/Resume Remaining/Retry Failed semantics, centralized transitions, stop counter reconciliation, and current-session successful-recipient resend protection with fail-closed restart continuation.
8. **P08 - Worker and Network Reliability [COMPLETE in v1.0.0.1.23; verification-corrected in v1.0.0.1.24]**: structured retry classification, bounded retry/backoff/jitter, Retry-After, explicit timeout policy, cooperative cancellation and safe asynchronous shutdown.
9. **P09 - Multi-Account Scheduling, Limits and Health [COMPLETE in v1.0.0.1.25; CI verification-corrected in v1.0.0.1.26]**: deterministic primary assignment, provider-safe per-account request pacing, runtime-only health/cooldown, and eligible pre-attempt failover without cross-account replay.
10. **P10 - Persistent Delivery Ledger, Idempotency and Recovery [COMPLETE in v1.0.0.1.27; verification-corrected in v1.0.0.1.28]**: per-recipient durable attempts/provider IDs/idempotency/restart recovery.
11. **P11 - Refrens End-to-End Task Enablement [IMPLEMENTED in v1.0.0.1.29; LIVE ACCEPTANCE PENDING]**: built-in Refrens Task execution using explicit required customer data; phase completion remains gated on owner-supplied live API Test, real invoice creation and recipient email delivery.
12. **P12 - Reports, Logs, Privacy and Operational Observability [COMPLETE in v1.0.0.1.30]**: recipient-level ledger reconciliation, structured/generalized redaction, safe export and closed-history retention controls.
13. **P13 - Executable External Provider Adapter Contract [COMPLETE in v1.0.0.1.32; verification-corrected in v1.0.0.1.33]**: versioned trusted external adapter bundles, truthful executable capability, fail-closed loading/lifecycle handling and P06/P08/P10 host integration.
14. **P14 - Live Integration, Recovery, Packaging and Production Certification**: real provider/environment tests and final production gate.

Detailed dependency graph and acceptance criteria remain in `project/planning/PRODUCTION_ROADMAP.md`.

## Pre-P08 Provider Adapter Exception - v1.0.0.1.21

Owner explicitly approved an exception before P08 to remove duplicated packaged-provider runtime dispatch and add an Agiled package. The release establishes an **internal packaged-provider adapter registry only**. It does not advance the 7/14 production phase count and does not complete P13 dynamic external-provider loading. Agiled remains fail-closed pending authoritative API contract convergence. P08 remains the next production phase.

## Pre-P08 Provider Adapter Verification - v1.0.0.1.22

The exact `v1.0.0.1.21` exception release was re-audited and no provider/API/invoice/UI behavior defect was found. `v1.0.0.1.22` adds verification coverage and synchronized release records only; P13 remains pending and Agiled remains non-executable until an authoritative current API contract is available. Production phase count remains 7/14 and P08 remains next.

## P08 Completion - v1.0.0.1.23

P08 is complete. The one-task-one-QThread boundary is preserved. Retry is bounded to three total recipient attempts, reactive `429/Retry-After` handling is implemented without introducing P09 rate scheduling, Stop is cooperative around in-flight requests, and application close waits for actual task-thread completion without blocking the GUI thread or calling `QThread.terminate()`. P09 is now the next production phase.


## P08 Verification Correction - v1.0.0.1.24

The exact `v1.0.0.1.23` P08 release was re-audited. `v1.0.0.1.24` closes truncated-response and TLS EOF/clean-close transient-disconnect classification gaps while preserving the approved retry/backoff/Retry-After, timeout, Stop/shutdown, progress and one-task-one-QThread contracts. It also synchronizes stale private phase/error-handling records. P08 remains complete; production progress remains 8/14 and P09 remains next.


## P09 Completion - v1.0.0.1.25

P09 is complete. The frozen round-robin primary assignment remains authoritative. Stripe Task requests are paced at the approved 20 requests/second/account with burst 1; temporary account/provider health is runtime-only; recognized account-scoped rate limiting can route only a not-yet-attempted recipient to the next healthy frozen account. Already-attempted recipients never cross accounts. Provider/network failures use provider-wide cooldown without account hopping, and deterministic customer/template/operation failures never fail over. Intra-Task concurrency remains 1. Production progress is 9/14; P10 is next.


## P09 CI Verification Correction - v1.0.0.1.26

The exact `v1.0.0.1.25` P09 runtime release was re-audited after GitHub Actions run `31336019074` exposed a CI-only repository-contract failure. Public CI checkout intentionally excludes the private `project/` tree, but one P09 synchronization test required files from that ignored tree. `v1.0.0.1.26` corrects the test boundary so tracked public completion records are always required and private completion records are additionally checked only when present. P09 remains complete, production progress remains 9/14, and P10 remains the next separately approval-gated phase.

## P10 Completion - v1.0.0.1.27

P10 is complete. SQLite schema v5 adds exactly three durable delivery-ledger tables for runs, per-run recipients and provider operations. `run_id` is an audit/execution invocation identity while `Task.id` remains the canonical logical Stripe idempotency identity. Stripe Task requests are write-ahead recorded before transport; durable outcomes, exact attempted-account binding, attempts, idempotency evidence and provider IDs support restart reconciliation. Interrupted mutating operations are classified `Uncertain`, and Resume Remaining / Retry Failed now derive from durable records. Historical ledger rows survive Close Task. Production progress is 10/14; P11 is now the next separately approval-gated phase.

## P10 Verification Correction - v1.0.0.1.28

The exact `v1.0.0.1.27` P10 release was re-audited. `v1.0.0.1.28` fixes durable ambiguity reconciliation only: an earlier mutating `Started`/`Uncertain` operation remains unresolved until a later successful operation proves the same stage with the exact same non-empty idempotency key; unrelated later failures cannot overwrite that uncertainty. Historical frozen primary-account and assigned-account consistency is also validated fail-closed. Schema remains v5 with exactly three P10 tables, P10 remains complete, production progress remains 10/14, and P11 remains the next separately approval-gated phase.

## P11 Implementation Candidate - v1.0.0.1.29

P11 code and automated contracts are implemented, but the phase is **not COMPLETE** because the owner-supplied live Refrens acceptance environment was not available for this implementation run. Refrens Task execution now requires explicit email/name/country, validates the exact trusted API host before credential transmission, blocks Indian recipients because the approved customer model has no GST State field, executes through the existing Task worker, uses 1 request/second/account Invio safety pacing, retries authentication only, and never blindly replays ambiguous invoice-create/email mutations. Refrens operations are write-ahead recorded in the existing schema-v5 P10 ledger and returned invoice `_id` evidence is persisted.

Production progress remains **10/14**. The latest completed-phase Official Baseline remains **v1.0.0.1.28**. P11 can move to COMPLETE/11 of 14 only after live Refrens API Test, real invoice creation and recipient email-delivery acceptance pass.

## P12 Completion - v1.0.0.1.30

P12 is complete. Reports now reconcile recipients from the existing P10 ledger; provider acceptance is distinguished from independently confirmed email delivery; logs have structured severity/category metadata with centralized secret/PII redaction; Task/recipient/log exports are atomic, formula-injection-safe and user-error-safe; and closed delivery history can be explicitly cleared without deleting open Task recovery data. Schema remains v5 and provider-send behavior is unchanged. Completed acceptance phases are 11/14 (P01-P10 plus P12). P11 remains implemented with live acceptance pending.


## P12 Verification Correction - v1.0.0.1.31

The exact uploaded v1.0.0.1.30 P12 baseline was re-audited. v1.0.0.1.31 closes only P12 observability/privacy correctness gaps: quoted JSON-style provider/token fields are centrally redacted, provider-send acceptance is derived from durable send-stage evidence rather than a recipient result flag alone, unresolved mutating ambiguity stays observable, and conflicting historical account evidence fails closed in recipient reporting. P12 remains complete, production acceptance progress remains 11/14, P11 live acceptance remains pending, and P13/P14 remain separately approval-gated.

## P13 Completion - v1.0.0.1.32

P13 is complete. External `Load Provider` now supports an optional explicit interface-v1 executable adapter bundle while preserving manifest-only compatibility. Executable code requires owner confirmation and is treated as trusted in-process Python, not sandboxed code. Provider ID/interface/version/profile/capability mismatches, missing adapter files and import failures remain visible but non-executable. External API Test and Task operations execute through existing verification, immutable snapshot, preflight, reliability, scheduling and durable-ledger boundaries. Packaged Stripe/Refrens remain on the built-in registry and Agiled remains fail-closed. Completed acceptance phases are 12/14; P11 live acceptance and P14 production certification remain outstanding.

## P13 Verification Correction - v1.0.0.1.33

The exact v1.0.0.1.32 P13 baseline was re-audited. v1.0.0.1.33 closes two P13 lifecycle/containment gaps only: exceptions raised while reading adapter metadata after `create_adapter()` are converted to `Incompatible` instead of being able to escape startup, and external-provider uninstall now stages active registry names and restores the manifest if moving the adapter fails. No interface/capability/schema/dependency/provider-send/WorkerManager/UI-page behavior is expanded. P13 remains complete, completed acceptance phases remain 12/14, P11 live acceptance remains pending, and P14 remains the final certification phase.


## P14 Certification Candidate - v1.0.0.1.34

P14 candidate implementation repairs the setuptools wheel package/resource omissions, adds deterministic source/install resource resolution, adds Windows CI/native-smoke certification tooling, and adds local deterministic 10,000-import, 1,000-recipient injected execution and subprocess crash-recovery gates. Local automated and packaging gates can be executed without provider secrets. The final acceptance gate remains open: Stripe Test/Live controlled integration, Refrens API/invoice/mailbox delivery, and clean Windows/native PySide6/keyring evidence must be recorded before P11/P14 can be marked complete or Invio can be described as production-ready.


## P14 Windows Distribution / Release Pipeline - v1.0.0.1.35

The owner explicitly approved Nuitka OneDir and WiX MSI distribution as a P14 verification/build correction. v1.35 adds pinned Windows standalone compilation, a versioned portable ZIP, a generated per-user MSI, release checksums, per-push Windows artifact upload and exact-tag GitHub Release publication while retaining the v1.34 wheel and native-smoke gates. This does not change the P14 acceptance rule: the exact pushed Windows workflow and owner-controlled Stripe/Refrens live gates must pass before P11/P14 can be completed or Invio can be described as production-ready.


## P14 GitHub Actions CI verification correction - v1.0.0.1.36

The first pushed v1.35 distribution workflow correctly failed before packaging. GitHub run `31371279808` proved that `scripts/build/*` had not been committed because the existing broad `build/` ignore rule also matched `scripts/build/`. Windows additionally exposed two SQLite handle-lifetime defects during test cleanup. v1.36 fixes only those confirmed CI/runtime-verification defects, preserves the v1.35 distribution architecture, and remains P14 CERTIFICATION PENDING until the exact v1.36 Windows build executes successfully and outstanding live-provider acceptance gates pass.


## P14 WiX version verification correction - v1.0.0.1.37

GitHub run `31374749523` proved the v1.36 Windows pipeline reaches the pinned WiX installation stage after all preceding regression/wheel/native/Nuitka/portable gates pass. WiX `6.0.2` installs correctly but reports `6.0.2+b3f3403`; the v1.36 raw exact-string guard therefore fails falsely. v1.37 normalizes only the optional `+build-metadata` portion for the pinned-version comparison. P14 phase count does not advance: P11 live Refrens acceptance and a successful exact v1.37 Windows MSI/distribution run remain required.
