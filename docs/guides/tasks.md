# Task Guide

A Task is an isolated provider execution unit. Each open Task owns its selected accounts until the Task is closed.

## Create a Task

Select:

1. installed Provider;
2. one or more available **Verified** Accounts for that provider;
3. Invoice Template;
4. Customer List with at least one customer record (email is mandatory).

P01 verification gates remain unchanged. P02 persists the created Task, ordered selected accounts, counters/status/message, and account reservations transactionally. P05 extends the same Task-creation transaction with an immutable execution snapshot.

## Restart Recovery

Tasks survive application restart. A Task stored as `Ready`, `Stopped`, `Failed`, or `Completed` is restored with its saved metadata. A Task found as `Running`, `Paused`, or `Stopping` is restored as **Stopped** with a recovery message. Invio does not automatically resume provider requests after restart.

Account reservations are restored with the Task, so an account reserved by an open recovered Task does not become silently selectable by another Task.

## Controls

Existing controls remain: **Start**, **Pause**, **Resume**, **Stop**, **Retry Failed**, and **Close Task**. P07 makes their meaning state-specific: Start is first-run-only, the Start control becomes **Resume Remaining** for a safe Stopped continuation, Retry Failed is exact-failure-only, and Completed has no resend action. P03/P06 provider and account gates still run before a permitted new worker attempt.

Re-testing a reserved Account is permitted only when its Task worker is inactive. If that Re-test fails, the Account becomes **Not Verified** and the existing P01 execution gate blocks the Task.

## P02 Boundary

P02 persists Task-level execution metadata, not the future P10 recipient delivery ledger. P05 defines `Task.id` as the canonical logical run identity. P07 keeps exact failed/pending continuation identities only in current-process ProviderRuntime memory and fails closed after restart; provider customer/invoice IDs, per-attempt delivery records, durable idempotency evidence, and exact crash-to-provider reconciliation remain P10 scope.


## P04 Customer execution data

Task runtime snapshots now carry provider-neutral customer records (`email`, optional `name`, optional `country`) while preserving the historical email view used by the Stripe sender. Stripe execution remains email-based. Refrens Task execution is still disabled until P11 even when explicit name/country data exists. P04 does not solve the live-mutable Task-input issue; that remains P05.

## v1.0.0.1.13 P04 verification correction

The customer-aware Task snapshot and Stripe email-only execution semantics are unchanged. The historical mutable `CustomerList.emails` behavior is restored for compatibility, but P05 remains responsible for freezing Task inputs against later Customer List changes.

## P05 Immutable execution snapshot

For every **new Task**, Invio captures the approved inputs at Task creation time and persists them atomically with the Task and its Account reservations. The frozen snapshot contains:

- ordered customer records (email, optional name, optional country);
- a complete copy of the selected Invoice Template, all items, Decimal values, and terms;
- provider ID;
- ordered selected Account IDs;
- assignment strategy `recipient_ordinal_round_robin_v1`.

`Task.total` is derived from the frozen recipient count. Start and Retry use this same snapshot; they do not re-read current Customer List or Invoice Template content. Therefore, later customer imports/enrichment or template edits affect only future Tasks, not an existing Task.

`Task.id` is the canonical logical run identity. Pause/Resume/Stop/Retry remain actions on that same run. To execute a different recipient/template/provider/account basis, close the old Task as required by the existing reservation rules and create a new Task, which receives a new ID and a new snapshot.

### Pre-P05 Tasks after upgrade

Schema-v3 Tasks are preserved during the v3-to-v4 migration, including status/counters/references/reservations, but their original creation-time recipient/template data never existed on disk. Invio therefore marks them `LegacyUnavailable` rather than copying current list/template data and pretending it is historical. Legacy Tasks remain visible and closable, but **Start** and **Retry Failed** are disabled and backend-gated. Create a new Task to execute current inputs.

P05 does not change the existing Task state-machine semantics, automatic retries, rate limiting, provider failover, or delivery-ledger/restart reconciliation.
## v1.0.0.1.16 P05 verification correction

Normal post-P05 Task creation may persist only a real `Captured` execution snapshot. `LegacyUnavailable` is reserved for migrated pre-P05 Tasks and is never assigned as a fallback to a newly persisted Task. Captured Task progress must remain consistent with its frozen recipient count, and routine status/progress persistence cannot rewrite the immutable Task total. P07 now layers deterministic action/send-set semantics over that immutable snapshot without changing its schema.

## P06 no-side-effect preflight

New Task creation now validates the selected provider, current Account health, template/customer requirements, and executable provider capability **before** `AppState.create_task()` persists the Task or reserves Accounts. If preflight fails, no Task/reservation is created and no provider request is made.

Start and Retry run the same capability/health validation against the existing P05 immutable snapshot before any runner is returned to WorkerManager. The snapshot is not refreshed from current Customer Lists or Invoice Templates. A failed preflight leaves provider-side invoice/customer state untouched and reports the first deterministic correction message.

Current packaged runtime rules include: Stripe standard `INVOICE` only; Stripe Automatic Tax and non-zero template percentage line tax are blocked under the current data/runtime contract; Refrens production Task execution remains blocked until P11. P07 now owns and implements Task state-machine/resend policy; these provider capability rules remain P06 behavior.

## v1.0.0.1.18 P06 verification correction

Start/Retry preflight now verifies that the Account objects supplied to validation match the exact ordered Account IDs frozen in the P05 immutable Task snapshot. A mismatched Account input sequence is blocked before a runner is created. Refrens currency is also validated against Invio's existing approved invoice-currency catalogue even though the Refrens production Task runner remains disabled until P11.

## P07 state machine and resend contract

Allowed execution semantics are intentionally narrow:

- `Ready -> Running`: First Run only, using all frozen P05 recipients, and only when progress is pristine.
- `Running -> Paused -> Running`: the same worker resumes; no new recipient selection occurs.
- `Running/Paused -> Stopping -> Stopped`: Stop preserves an exact current-session separation of known failed recipients and never-attempted recipients.
- `Stopped -> Running`: **Resume Remaining** only; send set is failed plus pending in immutable P05 order, excluding every known success.
- `Failed -> Running`: **Retry Failed** only; send set is the exact current-session failed subset. Repeated retries reduce to unresolved failures.
- `Completed`: terminal for that Task's execution. Another full execution requires a new Task/new `Task.id`.

For a safe built-in Stripe continuation, persisted/UI counters are reconciled from the same runtime sets: `processed = total - pending`, `failed = len(failed)`, `success = processed - failed`, and `remaining = len(pending)`. No P08 automatic retry/backoff is added.

The continuation set is intentionally process-local. After application restart, Invio retains aggregate Task counters/status but does not invent email identities from them. Resume Remaining/Retry Failed is disabled when the exact set is unavailable. P10 remains responsible for durable recipient-level delivery/recovery.

Injected/external runners retain the existing registration API and first-run behavior. Because that API does not provide a trustworthy recipient subset, P07 blocks injected-runner Retry Failed / Resume Remaining rather than falling back to a full resend.
