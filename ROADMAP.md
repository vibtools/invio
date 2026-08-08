# Roadmap

Current frozen implementation baseline: **Invio v1.0.0.1.5**.

Roadmap entries are planning records, not implementation approval. Every production phase requires a separate explicit owner scope lock before code changes.

## Production Progress

- Documentation/governance phase `G0`: **COMPLETE**.
- Production implementation phases: **0 / 14 complete**.
- Next planned phase: **P01 - Real Account API Verification**.
- Current status: **not production-certified**.

## Ordered Production Phases

1. **P01 - Real Account API Verification**: wire the existing provider test logic to a non-blocking real API Test and gate Task use to verified accounts.
2. **P02 - Durable Domain Storage and Protected Credentials**: persist operational state and use an owner-approved protected secret-storage mechanism.
3. **P03 - Account Lifecycle, Verification Health and Provider-Install Consistency**: edit/delete/retest/health and deterministic uninstall behavior.
4. **P04 - Customer Data Contract and Import Upgrade**: preserve email-only Stripe use while adding explicit provider-required customer data such as Refrens country.
5. **P05 - Immutable Task Execution Snapshot and Input Consistency**: freeze recipients/template/account basis and eliminate list/template drift.
6. **P06 - Provider Capability and Preflight Validation**: reject unsupported provider/account/template/customer combinations before side effects.
7. **P07 - Task State Machine and Resend Safety**: deterministic Start/Retry semantics and protection against accidental successful-recipient resend.
8. **P08 - Worker and Network Reliability**: retry/backoff/rate-limit/timeout/cancellation/shutdown hardening.
9. **P09 - Multi-Account Scheduling, Limits and Health**: production-safe account distribution, limits and eligible failover.
10. **P10 - Persistent Delivery Ledger, Idempotency and Recovery**: per-recipient durable attempts/provider IDs/idempotency/restart recovery.
11. **P11 - Refrens End-to-End Task Enablement**: enable normal Refrens bulk Task execution using explicit required customer data.
12. **P12 - Reports, Logs, Privacy and Operational Observability**: recipient-level reconciliation, generalized secret redaction, safe export/retention.
13. **P13 - Executable External Provider Adapter Contract**: make future loaded providers accurately represent executable capability; architecture approval required before implementation.
14. **P14 - Live Integration, Recovery, Packaging and Production Certification**: real provider/environment tests and final production gate.

The detailed dependency graph, acceptance criteria and owner-decision gates are maintained in private project documentation:

- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.5.md`

Public developer inventories:

- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
