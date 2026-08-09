# Versioning

Invio release versions are controlled by Vib Tools. Every approved update freezes the latest verified release as the next baseline and produces a replace-ready project-root delta.

- `v1.0.0`: frozen source baseline.
- `v1.0.0.1`: official sidebar/provider-card and production-marker correction.
- `v1.0.0.1.1`: persistent user-friendly Settings UI/backend.
- `v1.0.0.1.2`: provider uninstall plus compact application-owned dialogs.
- `v1.0.0.1.3`: invoice-template expansion/provider binding, built-in provider runtime, compact logs/reports, and Dashboard.
- `v1.0.0.1.4`: dark scroll-surface correction, compact Invoice Template spacing repair, and bounded searchable Currency control.
- `v1.0.0.1.5`: Invoice Template geometry/root-cause repair.
- `v1.0.0.1.6`: P01 real non-blocking Stripe/Refrens API verification and verified-account Task gates.
- `v1.0.0.1.7`: P01 verification corrective release and shipped registry/test-boundary correction.
- `v1.0.0.1.8`: P02 durable SQLite domain state, schema/migration/recovery controls, and OS-protected `keyring` provider credentials with no plaintext fallback.
- `v1.0.0.1.9`: P02 verification corrective release; fixes persistence-failure re-entrancy, exact reservation-state recovery validation, and stale P02 roadmap progress metadata.

- `v1.0.0.1.10`: P03 production release; adds reservation-safe account lifecycle, durable verification health, SQLite schema v2, provider-uninstall preservation and Task provider-install execution gates.
- `v1.0.0.1.11`: P03 verification/corrective release; makes schema-migration backups WAL-aware, persists credential-loss verification downgrades, and hardens cross-store Account Edit recovery to remain fail-closed.

Future version changes require a new explicit scope lock. No unapproved feature or architecture change is included in a release delta.

- `v1.0.0.1.12`: P04 customer data/import release; adds backward-compatible email/name/country customer records, schema v3, structured validation/duplicate handling and customer-aware runtime snapshots without enabling Refrens Task sending.
- `v1.0.0.1.13`: P04 verification/correction release; restores mutable `CustomerList.emails` compatibility, row-numbered existing-list conflicts, ASCII two-letter country validation, malformed-file error containment, and pre-P04 Dashboard label scope fidelity.
- `v1.0.0.1.14`: Windows operational-storage/runtime hotfix; explicitly closes the temporary SQLite migration-backup connection before atomic replacement, preventing the self-inflicted `WinError 32` startup failure while keeping schema v3 and P01-P04 behavior unchanged.

- `v1.0.0.1.15`: P05 immutable Task execution snapshots; schema v4 freezes ordered recipients, copied invoice-template content, provider ID and account-assignment basis at Task creation, uses `Task.id` as the canonical logical run identity, and preserves pre-P05 Tasks as non-executable `LegacyUnavailable` records rather than fabricating historical inputs.
- `v1.0.0.1.16`: P05 forensic verification/correction; rejects post-P05 Tasks without a captured immutable snapshot, validates captured Task progress against its frozen recipient set, and prevents routine Task updates from rewriting the immutable total. Schema remains v4 and production progress remains 5/14.


- `v1.0.0.1.17`: P06 provider capability/preflight release; adds packaged manifest/runtime reconciliation, reserved built-in provider-ID collision protection, no-side-effect New Task/Start/Retry preflight, strict account/template/customer checks, Stripe INVOICE/tax safety gates, canonical Refrens endpoint trust, and runtime-capability visibility. SQLite remains schema v4.

- `v1.0.0.1.18`: P06 forensic verification/correction; hardens executable manifest truth, frozen Account binding, Refrens currency/endpoint validation and installed-provider capability reporting without changing schema v4 or advancing to P07.

## v1.0.0.1.19

- Completes P07 Task State Machine and Resend Safety.
- Adds formal Task transition/action validation and deterministic First Run / Resume Remaining / Retry Failed semantics.
- Prevents Completed full resend and Failed normal Start; successful recipients are excluded from current-session continuation/retry sets.
- Reconciles stopped/failed counters from the exact runtime failed/pending sets.
- Keeps exact continuation identities process-local and fails closed after restart; durable recipient recovery remains P10.
- Preserves SQLite schema v4, P05 snapshots, P06 preflight, WorkerManager, provider manifests/send semantics, dependencies, and P08+ scope.

## v1.0.0.1.20

- P07 forensic verification/correction release.
- Closes the late worker-terminal/late Pause-Stop transition race without expanding the approved P07 transition table.
- Requires an active existing Task worker for Pause/Resume/Stop controls and backend actions.
- Makes safe-empty Stopped/Failed continuation messaging distinct from restart/uncertain continuation unavailability.
- Keeps SQLite schema v4, P05 immutable snapshots, P06 preflight, WorkerManager architecture, provider manifests/send semantics, dependencies and P08+ scope unchanged.

## v1.0.0.1.21

Pre-P08 provider-adapter foundation and packaged Agiled provider. This owner-approved exception centralizes packaged runtime bindings without advancing the production phase count. Agiled is intentionally fail-closed pending authoritative API contract revalidation; P08 remains next.

## v1.0.0.1.22

Pre-P08 provider-adapter forensic verification release. It preserves the `v1.0.0.1.21` runtime behavior, adds targeted Agiled/adapter integration regression gates, revalidates the Agiled fail-closed contract boundary, synchronizes release records, and keeps P08 as the next separately approved production phase.

## v1.0.0.1.23

Completes P08 Worker and Network Reliability. Adds structured transient/permanent failure metadata, bounded three-attempt recipient retry with exponential backoff/jitter and Retry-After support, explicit 30-second shared urllib connect/read socket timeout policy, cooperative Pause/Stop-aware waits, safe asynchronous application shutdown, and per-recipient unexpected-exception isolation. Preserves one task-owned QThread, Stripe idempotency/account assignment, schema v4, dependencies, Refrens P11 gate, Agiled fail-close and all P09+ behavior.


## v1.0.0.1.24

P08 forensic verification correction. Reclassifies truncated HTTP response bodies and TLS EOF/clean-close interruptions as transient retryable disconnects where appropriate, preserves HTTP status/Retry-After when an error body is truncated, and synchronizes stale P08 completion/error-handling records. No retry-count/backoff, provider-send, WorkerManager, UI, schema, dependency, Refrens, Agiled, plugin, or P09+ behavior is changed.


## v1.0.0.1.25

P09 production release. Adds deterministic multi-account scheduling safety, Stripe per-account request pacing, runtime-only account/provider health and bounded cooldown, eligible pre-attempt deterministic failover, permanent account-auth suppression, and current-session attempted-recipient cross-account protection. No schema/dependency/UI architecture/P10 behavior change.


## v1.0.0.1.26

P09 CI/repository-contract verification correction. Runtime behavior is unchanged from `v1.0.0.1.25` except release/User-Agent markers. The correction removes a public-CI dependency on the intentionally private Git-ignored `project/` tree while retaining optional full-baseline verification of those private records. Production progress remains 9/14 and P10 remains next.

## v1.0.0.1.27 P10

Completes P10 Persistent Delivery Ledger, Idempotency and Recovery. SQLite advances from schema v4 to v5 with exactly three durable ledger tables. Every execution invocation gets a distinct `run_id`, but existing provider idempotency remains based on `Task.id`. Durable write-ahead operation records, attempts, account binding, provider references and sanitized error evidence make supported Stripe continuation restart-safe and observable. P05-P09 behavior, one-task-one-QThread, dependencies, provider manifests, Refrens P11 gate, Agiled fail-close and UI architecture remain unchanged.

## v1.0.0.1.28 P10 Verification Correction

Verification-only P10 correctness release. Schema stays v5 and the three-table delivery-ledger contract is unchanged. Durable uncertainty now remains until the exact mutating stage + non-empty idempotency identity is later proven successful; successful reconciliation removes only that matched ambiguity. Production phase count remains 10/14.
