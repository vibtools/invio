# Troubleshooting

## Provider does not appear in Accounts or Tasks

Install it from **Providers**. Bundled packages can be Available without being installed.

## Account cannot be saved after a successful API Test

P02 requires an approved OS-protected credential backend. If protected storage is unavailable/locked/unsupported, Invio fails closed and does not save provider secrets to a plaintext file. Restore the OS credential service and retry Add Account.

## A restored account shows Not Verified

Its non-sensitive metadata was loaded from SQLite but the protected credential entry could not be read or was missing. No plaintext fallback is used. The account remains blocked by the existing P01 Task gates.

## Invio reports an operational-storage startup error

Invio does not silently replace a corrupt, unsupported, or newer `domain.sqlite3`. Keep the database file for forensic/recovery work. Correct the underlying file/storage/version issue before reopening. An existing v0 database is backed up before the supported v0->v1 migration.

## Windows startup reports `WinError 32` for `pre_migration_*.bak.tmp`

This was a self-lock in the migration-backup implementation through `v1.0.0.1.13`: the temporary SQLite backup connection was still open when Windows was asked to rename `.bak.tmp` to `.bak`. `v1.0.0.1.14` explicitly closes that connection before the atomic replacement. Apply the `v1.0.0.1.14` patch and restart Invio.

If the same file-lock error still appears on `v1.0.0.1.14`, another process or security/indexing tool may actually be holding the backup path. Close other Invio instances and any tool directly accessing the Invio operational-storage files before retrying. Do not delete or overwrite `domain.sqlite3` as a first response.

## A Task was Running before restart but is now Stopped

Expected P02 behavior. Worker threads do not survive process restart, so `Running`, `Paused`, and `Stopping` tasks are recovered as **Stopped** and are not automatically resumed.

## Account remains reserved after restart

Expected while the owning Task remains open. P02 restores reservations. Close the Task through the normal workflow to release its selected accounts.

## API Test fails or is unavailable

Stripe/Refrens API Test performs real provider connection/permission requests. Correct credentials/mode and retry. Providers without an executable API-test adapter cannot become Task-ready.

## Refrens Task is blocked even though name/country are imported

Expected in P04. Customer Lists can now store explicit Refrens-required name/country data, but the production Refrens Task runner is still intentionally disabled until P11. Invio never guesses country.

## Invoice Template dialog does not fit the display

The editor remains compact and internally scrollable; P02 does not change its UI geometry.

## Customer import says the workbook cannot be read

The selected XLSX/XLSM file is malformed, damaged, mislabeled, or not a valid workbook. Invio reports this as a Customer Import error and does not modify the existing Customer List. Re-export the file as a valid supported workbook and retry.


## A restored Task says it predates immutable execution snapshots

Expected for a Task created before P05/schema v4. Invio cannot reconstruct the exact historical recipient set or Invoice Template copy from mutable current source records without guessing. The Task is therefore preserved for visibility/reporting and reservation safety, but **Start** and **Retry Failed** are disabled. Close the legacy Task to release its Accounts, then create a new Task to capture a trustworthy immutable snapshot.

## Invio reports an invalid or incomplete Task execution snapshot

Invio fails closed when a captured Task snapshot is missing, partial, has a provider/account-order mismatch, or disagrees with the persisted Task total. Do not edit the SQLite tables manually or replace the snapshot with current Customer List/Template data. Preserve `domain.sqlite3` and use the normal backup/recovery path or forensic support.
## Task snapshot or progress consistency error

On v1.0.0.1.16, a captured Task whose stored total/progress no longer agrees with its immutable recipient snapshot is rejected rather than silently repaired from the current Customer List or Invoice Template. Preserve the operational database for diagnosis; do not delete it as a first response. Newly persisted Tasks also cannot be created as `LegacyUnavailable`; that state is reserved for migrated pre-P05 Tasks.

## P06 Preflight Failed

If **Preflight Failed** appears, no provider invoice/customer mutation has started from that blocked action. Follow the displayed correction. Common cases are: provider not installed; packaged manifest/runtime contract mismatch; Account not verified or verification-health metadata incomplete; Stripe `BOS`; Stripe Automatic Tax; non-zero Stripe line tax; unsupported currency; or an untrusted Refrens API Base URL.

For a packaged manifest mismatch, uninstall the provider from **Providers** and install its bundled package again. For Account health failures, use **Accounts -> Re-test**. For Refrens, use exactly `https://api.refrens.com` as the API Base URL. Refrens normal Task sending remains unavailable until P11.


## v1.0.0.1.18 P06 verification corrections

For packaged-manifest/runtime mismatch, uninstall and reinstall the packaged provider. For Refrens endpoint failures, use exactly `https://api.refrens.com` without an explicit port. Region-specific three-decimal Stripe currencies remain unsupported by the current sender and are blocked before invoice creation.

## Resume Remaining or Retry Failed is disabled after restarting Invio

This is expected in v1.0.0.1.19. P07 keeps exact failed/pending recipient identities in the current ProviderRuntime process so successful recipients are never guessed or resent. SQLite still stores aggregate Task counters only; P10 is the planned durable recipient ledger/recovery phase.

If Invio was restarted, the Task remains visible and its Account reservation is preserved, but **Resume Remaining** / **Retry Failed** is disabled when the exact recipient set cannot be proven. Close the Task to release its Accounts, then create a new Task for a deliberate new full execution. Do not interpret a disabled continuation button as data loss from the immutable P05 snapshot; it is a resend-safety gate.

## A Task shows Stopped with no Resume Remaining action after finishing

In `v1.0.0.1.20`, a late accepted Pause/Stop can intentionally make an arriving `Completed` terminal signal settle as **Stopped** so the approved P07 transition table remains valid. If all recipients were already resolved, the safe continuation set is empty and **Resume Remaining** is disabled because there is nothing left to send. This does not mean recipient identity state was lost.

If the application was restarted, the separate existing rule still applies: exact continuation identities are not persisted until P10, so Resume/Retry fails closed rather than guessing.

## Agiled says API Test/runtime is unavailable

This is expected in `v1.0.0.1.21`. Invio has the Agiled package but deliberately has no executable Agiled handler while the current authoritative base URL, authentication format and invoice-send operation remain unresolved. Do not work around this by changing the manifest or entering a guessed API base URL. Supply authoritative current Agiled API documentation or a verified request/response contract for the exact API generation, then release a separately verified adapter update.

## Agiled remains unavailable in v1.0.0.1.22

This is still intentional. The current Agiled product page documents Bearer API-key authentication while the linked public OpenAPI document exposes a different legacy server/query-token/Brand-header contract, and an authoritative invoice-email send API operation has not been established. Invio therefore continues to fail before transport rather than guessing.

## Transient network retries in v1.0.0.1.23

Timeouts, transient disconnects, HTTP 408/429 and selected 5xx responses can be retried automatically for the same recipient up to three total attempts. Permanent validation/authentication/TLS-certificate failures are not automatically retried. If Exit appears to wait after stopping active Tasks, Invio is intentionally keeping the window alive until an in-flight request returns or reaches the explicit 30-second timeout so the task QThread is not destroyed unsafely.
