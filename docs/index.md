# Invio Documentation

Current version: **v1.0.0.1.28**.

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
- `release-notes/1.0.0.1.28.md` - current P10 verification-correction release.
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
