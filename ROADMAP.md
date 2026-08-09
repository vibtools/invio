# Roadmap

Current frozen implementation baseline: **Invio v1.0.0.1.22**.

Roadmap entries are planning records, not implementation approval. Every production phase requires a separate explicit owner scope lock before code changes.

## Production Progress

- Documentation/governance phase `G0`: **COMPLETE**.
- Production implementation phases: **7 / 14 complete**.
- Completed: **P01**, **P02**, **P03**, **P04**, **P05**, **P06**, **P07**.
- Next planned phase: **P08 - Worker and Network Reliability**.
- Current status: **not production-certified**.

## Ordered Production Phases

1. **P01 - Real Account API Verification [COMPLETE]**: real non-blocking provider API Test and verified-account Task gates.
2. **P02 - Durable Domain Storage and Protected Credentials [COMPLETE in v1.0.0.1.8; verification-corrected in v1.0.0.1.9]**: SQLite operational persistence, versioned schema/transactions/recovery, and owner-approved OS-protected keyring credentials with no plaintext fallback.
3. **P03 - Account Lifecycle, Verification Health and Provider-Install Consistency [COMPLETE in v1.0.0.1.10; verification-corrected in v1.0.0.1.11]**: reservation-safe edit/delete/re-test, durable verification health, provider-uninstall preservation, and provider-installed Task execution gates.
4. **P04 - Customer Data Contract and Import Upgrade [COMPLETE in v1.0.0.1.12; verified/corrected in v1.0.0.1.13]**: backward-compatible customer records, structured/legacy imports, schema-v3 metadata persistence and customer-aware runtime snapshots while preserving Stripe email-only semantics.
5. **P05 - Immutable Task Execution Snapshot and Input Consistency [COMPLETE in v1.0.0.1.15; verification-corrected in v1.0.0.1.16]**: durable creation-time recipients/template/provider/account-basis snapshots, snapshot-derived totals, Start/Retry reuse, and fail-closed legacy Task migration.
6. **P06 - Provider Capability and Preflight Validation [COMPLETE in v1.0.0.1.17; verification-corrected in v1.0.0.1.18]**: reconcile declared/executable capabilities, protect packaged runtime IDs, validate provider/account/template/customer/endpoint contracts before side effects, and show precise correction messages.
7. **P07 - Task State Machine and Resend Safety [COMPLETE in v1.0.0.1.19; verification-corrected in v1.0.0.1.20]**: deterministic First Run/Resume Remaining/Retry Failed semantics, centralized transitions, stop counter reconciliation, and current-session successful-recipient resend protection with fail-closed restart continuation.
8. **P08 - Worker and Network Reliability**: retry/backoff/rate-limit/timeout/cancellation/shutdown hardening.
9. **P09 - Multi-Account Scheduling, Limits and Health**: production-safe account distribution, limits and eligible failover.
10. **P10 - Persistent Delivery Ledger, Idempotency and Recovery**: per-recipient durable attempts/provider IDs/idempotency/restart recovery.
11. **P11 - Refrens End-to-End Task Enablement**: enable normal Refrens bulk Task execution using explicit required customer data.
12. **P12 - Reports, Logs, Privacy and Operational Observability**: recipient-level reconciliation, generalized secret redaction, safe export/retention.
13. **P13 - Executable External Provider Adapter Contract**: make future loaded providers accurately represent executable capability; architecture approval required before implementation.
14. **P14 - Live Integration, Recovery, Packaging and Production Certification**: real provider/environment tests and final production gate.

Detailed dependency graph and acceptance criteria remain in `project/planning/PRODUCTION_ROADMAP.md`.

## Pre-P08 Provider Adapter Exception - v1.0.0.1.21

Owner explicitly approved an exception before P08 to remove duplicated packaged-provider runtime dispatch and add an Agiled package. The release establishes an **internal packaged-provider adapter registry only**. It does not advance the 7/14 production phase count and does not complete P13 dynamic external-provider loading. Agiled remains fail-closed pending authoritative API contract convergence. P08 remains the next production phase.

## Pre-P08 Provider Adapter Verification - v1.0.0.1.22

The exact `v1.0.0.1.21` exception release was re-audited and no provider/API/invoice/UI behavior defect was found. `v1.0.0.1.22` adds verification coverage and synchronized release records only; P13 remains pending and Agiled remains non-executable until an authoritative current API contract is available. Production phase count remains 7/14 and P08 remains next.
