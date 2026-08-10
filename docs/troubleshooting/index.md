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

For Tasks executed with P10 (`v1.0.0.1.27+`), restart continuation is derived from the durable delivery ledger rather than aggregate counters. Resume Remaining / Retry Failed is enabled only when exact latest recipient outcomes and account binding are trustworthy. If the Task predates P10 and already had non-pristine execution state, Invio intentionally does not fabricate historical recipient/provider evidence; continuation may remain disabled and the Task can be closed to release its Accounts.

## A Task shows Stopped with no Resume Remaining action after finishing

In `v1.0.0.1.20`, a late accepted Pause/Stop can intentionally make an arriving `Completed` terminal signal settle as **Stopped** so the approved P07 transition table remains valid. If all recipients were already resolved, the safe continuation set is empty and **Resume Remaining** is disabled because there is nothing left to send. This does not mean recipient identity state was lost.

After P10, restart continuation uses durable ledger evidence. Pre-P10 non-pristine Tasks still fail closed when exact historical continuation cannot be proven.

## Agiled says API Test/runtime is unavailable

This is expected in `v1.0.0.1.21`. Invio has the Agiled package but deliberately has no executable Agiled handler while the current authoritative base URL, authentication format and invoice-send operation remain unresolved. Do not work around this by changing the manifest or entering a guessed API base URL. Supply authoritative current Agiled API documentation or a verified request/response contract for the exact API generation, then release a separately verified adapter update.

## Agiled remains unavailable in v1.0.0.1.22

This is still intentional. The current Agiled product page documents Bearer API-key authentication while the linked public OpenAPI document exposes a different legacy server/query-token/Brand-header contract, and an authoritative invoice-email send API operation has not been established. Invio therefore continues to fail before transport rather than guessing.

## Transient network retries in v1.0.0.1.23

Timeouts, transient disconnects, HTTP 408/429 and selected 5xx responses can be retried automatically for the same recipient up to three total attempts. Permanent validation/authentication/TLS-certificate failures are not automatically retried. If Exit appears to wait after stopping active Tasks, Invio is intentionally keeping the window alive until an in-flight request returns or reaches the explicit 30-second timeout so the task QThread is not destroyed unsafely.


## A response disconnects while Invio is reading the body

`v1.0.0.1.24` corrects the P08 transport boundary for truncated HTTP bodies and TLS EOF/clean-close interruptions. When these are transient disconnects, Invio applies the existing bounded retry policy. Certificate verification failures remain permanent. If repeated transient attempts exhaust all three total attempts, the recipient follows the normal Failed/Retry Failed workflow.


## P09 account/provider cooldown

If Live Logs report an account cooldown, Invio is temporarily pacing that account after a recognized Stripe rate-limit condition. Only not-yet-attempted recipients can use deterministic fallback. If Live Logs report a provider cooldown, Invio waits instead of hopping accounts. If an account is blocked after HTTP 401/403, use the existing account API Re-test/Edit verification workflow; a successful verification clears the runtime-only block.


## GitHub Actions reports missing `project/planning/PHASE_COMPLETION_LOG.md`

This was a `v1.0.0.1.25` repository-contract test defect, not a missing runtime file. `/project/` is intentionally private and Git-ignored. `v1.0.0.1.26` corrects the test so public CI validates tracked public completion records; do not publish the private `project/` tree to work around this failure.

## A restarted P10 Task shows Uncertain recipients

`Uncertain` means Invio had durable write-ahead evidence that a side-effecting provider operation started, but the previous process ended before a definitive local success/failure record was committed. Invio does not relabel that outcome as Failed or Succeeded. Resume Remaining uses the same Task-derived Stripe idempotency identity and exact previously assigned account when durable evidence makes replay safe; otherwise the action fails closed. Do not create a duplicate full Task merely to bypass an Uncertain state without reviewing the existing Task/Live Logs.

## P10 recipient remains Uncertain after a later failure - v1.0.0.1.28+

This is intentional when an earlier side-effecting provider operation still has no matching successful reconciliation record. A later failure at another stage does not prove what happened to that earlier request. Invio keeps the recipient unresolved and exposes Resume Remaining rather than incorrectly classifying it as definitively Failed. If the same stage and non-empty idempotency key later succeeds, that specific ambiguity is reconciled.

## Refrens P11 Task troubleshooting

- **Task blocked for missing data:** ensure every Refrens recipient has explicit Email, Name and Country in the Customer List.
- **India/GST State warning:** the current approved customer model has no GST State field, so Indian Refrens recipients are intentionally blocked before invoice creation.
- **Untrusted endpoint:** set API Base URL exactly to `https://api.refrens.com` and re-test the account; credentials are not sent to other hosts.
- **Uncertain delivery:** do not manually assume failure and re-run the same recipient. An ambiguous invoice-create/email outcome is retained as `Uncertain` to avoid duplicate delivery; automatic Refrens replay is disabled for that recipient.
- **Live acceptance:** P11 remains live-acceptance pending until an owner-controlled Refrens environment confirms API Test, invoice creation and recipient email delivery.

## Report or log export fails

Invio reports export write/permission/encoding failures in a dialog and keeps the application running. Choose a writable destination and retry. Exports use a temporary sibling file and only replace the final target after a complete write.

If recipient history appears `Provider Accepted`, remember that this means provider acceptance, not independently confirmed mailbox delivery. `Uncertain` means the durable ledger cannot safely prove the provider-side result and must not be interpreted as success or definitive failure.


## Recipient Delivery History reports an error or Uncertain status

P12 reporting fails closed when durable history contains conflicting account-assignment evidence or unresolved side-effecting provider operations. Do not infer delivery from aggregate Task counters alone. Review the durable recipient status/provider reference and reconcile the provider-side invoice state before retrying an uncertain operation. `Provider Accepted` means Invio has durable send-stage success evidence; it is still not independent mailbox-delivery confirmation.

## External provider adapter is not executable

Check the Providers card runtime-adapter state. `Manifest only` means no executable adapter was declared. `Missing` means an executable declaration exists but the installed adapter file is absent. `Incompatible` means import, interface version, provider ID, adapter version, profile, capability or scheduling validation failed. Re-load a complete trusted `provider.json` + sibling `adapter.py` bundle. Invio does not install missing Python dependencies automatically. If existing Tasks reference an executable external provider, close those Tasks before replacing or uninstalling its adapter.


## External provider adapter is Incompatible

Confirm the bundle contains the selected `provider.json` plus sibling `adapter.py`, uses interface version 1, matching provider/adapter versions and matching declared/executable capabilities. Invio does not auto-install missing Python dependencies. Import/entrypoint failures or persistent `sys.path` mutation are contained and the provider remains non-executable; correct the trusted adapter bundle and load it again.

## External provider reports Incompatible or uninstall fails - v1.0.0.1.33

If an external provider is shown as **Incompatible**, replace it with an adapter whose interface/provider/version/profile/capability metadata can be read safely and matches its manifest. If uninstall reports a filesystem error, the active provider registry is rolled back when possible; close software that may be locking files and retry. Do not manually delete only the manifest or only the adapter file.


## Wheel installation is missing providers/settings/assets

Use `v1.0.0.1.34` or later candidate packaging and run `python scripts/test/p14_wheel_audit.py <wheel>` before installation. The audit requires the existing settings package, three packaged provider manifests and checkmark asset. If Invio reports `Invio Runtime Resources`, reinstall from a wheel that passes this audit rather than manually fabricating provider files.

## Is v1.0.0.1.34 production-ready?

No. Local deterministic P14 gates and packaging correction are implemented, but the owner live Stripe/Refrens gates and an executed clean Windows/native PySide6/keyring certification run remain outstanding. P11 and P14 must not be marked complete until that evidence exists.


## Portable EXE starts but reports missing runtime resources

Re-extract the complete versioned portable ZIP. `Invio.exe` must remain beside the packaged `assets/` and `providers/` trees and all Nuitka OneDir support files. Copying `Invio.exe` alone is unsupported.

## MSI install succeeds but Provider Load/Install cannot write

The v1.0.0.1.37 MSI is designed as a per-user LocalAppData installation specifically so the provider registry is writable. If the files were manually moved into a protected system directory, reinstall using the official MSI instead of changing provider-storage permissions.

## GitHub release was not created for a tag

Confirm the tag exactly matches the five-part application version (`v1.0.0.1.37`) and that both the Ubuntu and Windows build jobs passed. The release job intentionally does not run if the tag/version differs or if the Nuitka/MSI distribution gate fails.
