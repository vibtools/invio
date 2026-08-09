# Roadmap

Current frozen implementation baseline: **Invio v1.0.0.1.10**.

Roadmap entries are planning records, not implementation approval. Every production phase requires a separate explicit owner scope lock before code changes.

## Production Progress

- Documentation/governance phase `G0`: **COMPLETE**.
- Production implementation phases: **3 / 14 complete**.
- Completed: **P01**, **P02**, **P03**.
- Next planned phase: **P04 - Customer Data Contract and Import Upgrade**.
- Current status: **not production-certified**.

## Ordered Production Phases

1. **P01 - Real Account API Verification [COMPLETE]**: real non-blocking provider API Test and verified-account Task gates.
2. **P02 - Durable Domain Storage and Protected Credentials [COMPLETE in v1.0.0.1.8; verification-corrected in v1.0.0.1.9]**: SQLite operational persistence, versioned schema/transactions/recovery, and owner-approved OS-protected keyring credentials with no plaintext fallback.
3. **P03 - Account Lifecycle, Verification Health and Provider-Install Consistency [COMPLETE in v1.0.0.1.10]**: reservation-safe edit/delete/re-test, durable verification health, provider-uninstall preservation, and provider-installed Task execution gates.
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

Detailed dependency graph and acceptance criteria remain in `project/planning/PRODUCTION_ROADMAP.md`.
