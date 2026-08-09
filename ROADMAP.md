# Roadmap

Current frozen implementation baseline: **Invio v1.0.0.1.27**.

Roadmap entries are planning records, not implementation approval. Every production phase requires a separate explicit owner scope lock before code changes.

## Production Progress

- Documentation/governance phase `G0`: **COMPLETE**.
- Production implementation phases: **10 / 14 complete**.
- Completed: **P01**, **P02**, **P03**, **P04**, **P05**, **P06**, **P07**, **P08**, **P09**, **P10**.
- Next planned phase: **P11 - Refrens End-to-End Task Enablement**.
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
10. **P10 - Persistent Delivery Ledger, Idempotency and Recovery [COMPLETE in v1.0.0.1.27]**: per-recipient durable attempts/provider IDs/idempotency/restart recovery.
11. **P11 - Refrens End-to-End Task Enablement**: enable normal Refrens bulk Task execution using explicit required customer data.
12. **P12 - Reports, Logs, Privacy and Operational Observability**: recipient-level reconciliation, generalized secret redaction, safe export/retention.
13. **P13 - Executable External Provider Adapter Contract**: make future loaded providers accurately represent executable capability; architecture approval required before implementation.
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
