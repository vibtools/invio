# PATCH MANIFEST — Invio v1.0.0.1.49.6

## Official frozen parent

- Parent: `Invio v1.0.0.1.49.5`
- Parent Git commit: `8942477949cf61e169156032e3574377bf6d6fc7`
- Scope: `Phase 2 — Provider Fatal Error / Account Limit Circuit Breaker & Task UX` only
- Target: `Invio v1.0.0.1.49.6`
- Phase-1 live RDP acceptance is owner-deferred until the final combined release.

## Verified root causes

1. The generic external-provider recipient loop caught each recipient exception, updated the durable state, then continued to the next recipient with no machine-readable fatal-batch boundary.
2. Odoo's proven daily-email-limit evidence was a normal non-retryable `provider-mail` exception and could not tell the host that all later recipients were predictably blocked.
3. Odoo `UNVERIFIED` post-send evidence still returned `ExternalRecipientResult`, overstating certainty after a non-idempotent send mutation.
4. External progress used loop-attempt count rather than the authoritative durable summary, and MainWindow could replace the exact stop reason during worker terminal reconciliation.

## Functional changes

1. Add optional `halt_batch`, `halt_code`, `user_message` metadata to `ProviderRuntimeError`; defaults preserve existing adapters.
2. Reconcile the current external recipient before honoring a fatal batch halt.
3. Abort before the next recipient once `halt_batch=True` is observed.
4. Preserve non-idempotent current-recipient outcomes as `Uncertain`; untouched recipients remain `Pending`.
5. Report durable external progress counts instead of raw attempted-loop counts.
6. Preserve actionable `Stopped:` provider messages on the existing Task card.
7. Advance bundled Odoo provider to v1.0.1.
8. Classify the proven Odoo daily email limit as a terminal provider-quota condition.
9. Treat Odoo post-send `UNVERIFIED` evidence as terminal uncertainty rather than confirmed success.
10. Keep `SENT` / `QUEUED` success semantics and ordinary non-quota recipient failure continuation unchanged.
11. Add direct P13/Odoo/UI/repository regression coverage and synchronize version/documentation records.


## Delta inventory

- Added files: 6
- Modified files: 28 (including regenerated root `SHA256SUMS.txt`)
- Removed files: 0
- Total delta files: 34
- Layout: direct project-root overlay; no wrapper directory
- Companion external-provider artifact: `Invio_Odoo_Provider_v1.0.1.ivx`

## Frozen boundaries

No new Task status/page/schema is added. Phase-1 TLS, WorkerManager/QThread, Task state-machine architecture, delivery ledger schema, SQLite/storage/CredentialStore, Browser OAuth/Easy Onboarding, IVX Format/provider loading, **Phase 3** retry/backoff/timeout/delay/rate Settings and Odoo scheduling policy, **Phase 4** Dynamic Tags, unrelated UI and MSI/WiX architecture remain outside Phase 2.

## Security / delivery invariants

- Uncertain non-idempotent external mutations are never automatically replayed.
- No automatic cross-account Odoo quota failover is introduced.
- No provider limit value is guessed; only the proven provider evidence pattern is classified as daily-limit terminal.
- Ordinary external recipient errors remain backward compatible.
- Phase-1 certificate and hostname verification remain fail-closed.

## Verification gates

The candidate must pass targeted Odoo/P13/UI/repository tests, the complete repository audit, wheel/distribution structural checks, frozen-boundary comparison, Odoo bundle checksum validation, Odoo v1.0.1 IVX validation, and exact parent+delta overlay verification before delivery. Native final combined release/RDP acceptance remains deferred by owner.
