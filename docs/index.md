# Invio Documentation

Current version: **v1.0.0.1.17**.

Invio is a Vib Tools desktop application for provider-managed invoice automation. Current workflow:

**Provider -> Verified Account(s) -> Invoice Template -> Customer List -> Task -> Provider Runtime -> Reports/Live Logs**

P02 adds restart-durable non-sensitive operational state and OS-protected provider credentials. P04 adds backward-compatible customer records and structured import. v1.0.0.1.14 preserves the Windows-safe migration backup path. P05 makes Task execution inputs durable/immutable and v1.0.0.1.16 hardens those invariants. v1.0.0.1.17 adds P06 provider capability/preflight validation before Task persistence or provider runner execution.

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
- `release-notes/1.0.0.1.17.md` - current release.
- `release-notes/1.0.0.1.15.md` - original P05 implementation.
- `release-notes/1.0.0.1.14.md` - Windows storage hotfix.
- `release-notes/1.0.0.1.12.md` - original P04 feature release.
- `release-notes/1.0.0.1.9.md` - P02 corrective release.

Detailed forensic reports, phase roadmap, phase completion ledger and update protocol are private records under `project/`.

## Current production phase

`v1.0.0.1.17` completes **P06 - Provider Capability and Preflight Validation**. Production progress is **6/14**. The next separately approval-gated phase is **P07 - Task State Machine and Resend Safety**.
