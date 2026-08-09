# Invio Documentation

Current version: **v1.0.0.1.20**.

Invio is a Vib Tools desktop application for provider-managed invoice automation. Current workflow:

**Provider -> Verified Account(s) -> Invoice Template -> Customer List -> Task -> Provider Runtime -> Reports/Live Logs**

P02 adds restart-durable non-sensitive operational state and OS-protected provider credentials. P04 adds backward-compatible customer records and structured import. v1.0.0.1.14 preserves the Windows-safe migration backup path. P05 makes Task execution inputs durable/immutable and v1.0.0.1.16 hardens those invariants. v1.0.0.1.17 added P06 provider capability/preflight validation; v1.0.0.1.18 verification-corrected its contracts; v1.0.0.1.19 adds P07 deterministic Task state/resend safety; v1.0.0.1.20 verification-corrects its worker-terminal/control integration without changing the P07 model.

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
- `release-notes/1.0.0.1.20.md` - current release.
- `release-notes/1.0.0.1.15.md` - original P05 implementation.
- `release-notes/1.0.0.1.14.md` - Windows storage hotfix.
- `release-notes/1.0.0.1.12.md` - original P04 feature release.
- `release-notes/1.0.0.1.9.md` - P02 corrective release.

Detailed forensic reports, phase roadmap, phase completion ledger and update protocol are private records under `project/`.

## Current production phase

`v1.0.0.1.20` is the verification-corrected **P07 - Task State Machine and Resend Safety** baseline. Production progress remains **7/14**. The next separately approval-gated phase is **P08 - Worker and Network Reliability**.

## P07 Task execution safety

P07 makes Start/Resume/Retry recipient selection deterministic. First Run is limited to pristine Ready Tasks; Stopped Tasks may Resume Remaining only when the exact current-session failed/pending set exists; Failed Tasks may Retry Failed only when the exact failed set exists; Completed Tasks cannot resend. Restart does not reconstruct recipient identities from counters, so continuation fails closed until P10.

## v1.0.0.1.20 P07 verification note

P07's send-set rules are unchanged. The correction makes late worker terminal signals deterministic against accepted Pause/Stop state, disables stale Pause/Resume/Stop controls when the Task thread has already ended, and reports a proven empty continuation set as empty rather than unavailable.
