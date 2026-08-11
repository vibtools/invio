## GitHub Actions reports many missing `project/...` records after a narrow allowlist

If `tests/test_repository_contracts.py` suddenly reports multiple missing planning/specification/research files while application tests and PySide6 runtime tests pass, verify `.gitignore` first. `project/` is intentionally private. A partial unignore makes `project_root.is_dir()` true and activates private-baseline-only assertions without supplying the complete private tree. `v1.0.0.1.48.3` restores the correct boundary: keep `/project/` fully ignored and make private-record verification conditional on a complete private baseline. Do not publish the private project tree as a CI workaround.

## v1.0.0.1.47.0 Window / Dialog UI

If custom window controls or sidebar icons are missing in a packaged build, verify the distribution contains `assets/icons/nav/`, `assets/icons/window/`, and the themed chevron SVG files. These resources are part of the required Windows/wheel inventory in v1.47.0.

## v1.0.0.1.46.0 title-bar note

Invio no longer relies on the white native Windows title bar for its Main Window or application-owned dialogs. If window chrome appears native, confirm the exact v1.46.0 source/build and runtime resources are being used. Native OS file dialogs are intentionally unchanged.

# Troubleshooting

## v1.0.0.1.45.0 Providers Page transient-window correction

A brief blank/white `Invio` window during startup or Providers Page entry was traced to newly-created provider cards being made visible while still parentless. v1.45.0 keeps cards hidden until `QGridLayout` has re-parented them into the Providers Page host.

## v1.0.0.1.44.0 Intro/Subtitle troubleshooting

Page header introductions and shared card/section subtitles are intentionally absent. Provider package descriptions and dynamic operational/validation messages should still display; if those are missing, treat it as a source/package mismatch rather than expected v1.44 behavior.

## v1.0.0.1.43.0 Data Grid troubleshooting

Search/filter/pagination are UI-session state only. Clear the search and return filters to `All` if a known record is not visible. Pagination resets to page 1 after a search/filter change. Full text for elided table values is available by hover tooltip. The New Task account selector still disables unverified or reserved accounts; search/pagination do not override those existing eligibility gates.


## v1.0.0.1.42.0 UI troubleshooting

If Settings appears empty, clear the Search settings field or press `Ctrl+F` and remove the filter text. Search hides nonmatching cards only; it never deletes or changes settings. If a dialog action looks generic rather than blue, treat it as a packaging/source mismatch because Save/Create/Add primary actions are explicitly styled in v1.42.0.


## Provider cards, logos, or search do not display correctly

On `v1.0.0.1.41.1`, Provider cards remain fixed at 220px and descriptions remain limited to three visible lines; hover the description for the full tooltip. The grid calculates 2–4 columns from available page width using a 280px minimum card width. The Search providers field filters the currently visible Provider cards by provider identity/description/status. Stripe, Refrens, Agiled and Odoo card logos are packaged under `assets/icons/providers/`; if a released wheel/portable build omits them, treat that build as invalid rather than substituting initials. Provider install/load/uninstall behavior is unrelated to this visual layout.

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

The v1.0.0.1.38 MSI is designed as a per-user LocalAppData installation specifically so the provider registry is writable. If the files were manually moved into a protected system directory, reinstall using the official MSI instead of changing provider-storage permissions.

## GitHub release was not created for a tag

Confirm the tag exactly matches the five-part application version (`v1.0.0.1.38`) and that both the Ubuntu and Windows build jobs passed. The release job intentionally does not run if the tag/version differs or if the Nuitka/MSI distribution gate fails.


### Release checksum audit reports unexpected `.wixpdb`

The approved Invio release payload set does not include WiX debug-symbol sidecars. v1.0.0.1.38 builds the MSI with `-pdbtype none`; if a `.wixpdb` appears in `dist/release`, treat the build as outside the frozen release contract rather than adding it to `SHA256SUMS.txt` or the published release.
## `Protected credential storage is unavailable.` after a successful API Test

If a provider API Test succeeds but Add Account immediately reports this exact message in released v1.0.0.1.38, the provider API test itself has already succeeded. The message is emitted by the initial `CredentialStore` keyring import/dependency boundary before credential persistence. v1.0.0.1.39 is the scope-locked pre-release compiled-packaging correction candidate. Do not work around the error by storing provider secrets in plaintext. Validate the candidate from source first, then require the compiled Windows credential smoke/artifact gate.

## Refrens `terms: Cast to embedded failed` — v1.0.0.1.39 live failure

If v1.39 live logs show a verified Refrens account followed by `invoices validation failed: terms: Cast to embedded failed ... at path "terms"`, the failure is in the create-invoice payload, not API authentication. v1.40 omits Invio's unsupported `terms: list[str]` request representation. Do not retry the same failed batch repeatedly before applying/testing the correction.

## New Task / Customer Lists / right-click menu appears light

v1.40 explicitly styles `QListWidget`, table surfaces and `QMenu`, and applies the existing Invio QSS at application scope. If a custom OS accessibility/theme layer still overrides those colors, record the exact widget/screenshot rather than changing unrelated palette behavior.

## Refrens invoice exists but recipient email is not triggered — v1.0.0.1.40

This is the owner-observed v1.40 live gap. Invoice creation and provider email triggering are separate evidence boundaries. v1.0.0.1.40.1 performs the explicit post-create `/businesses/:urlKey/invoices/:invoiceID/email` request and does not mark provider send acceptance until it succeeds. Test a controlled recipient mailbox before any release tag.

## GitHub/Nuitka duplicate `keyring` config — v1.0.0.1.40

GitHub run `31411715607`, job `93531112926`, reached the Nuitka OneDir step after the regression/native wheel checks passed and then failed because `.github/nuitka-keyring.nuitka-package.config.yml` duplicated Nuitka 4.1.3's built-in `keyring` standard package configuration. v1.0.0.1.40.1 keeps the keyring packages and compiled credential smoke but no longer passes the custom user package config to Nuitka.

## Agiled API Test works but Task sending is unavailable — v1.0.0.1.40.2

This is intentional. The owner-supplied current Agiled OpenAPI verifies Bearer authentication, `GET /public/v1/me`, and invoice CRUD, so Account API Test can now succeed. The same OpenAPI does not publish an invoice email/send endpoint and does not define the invoice-specific fields inside its generic mutation body. Invio therefore keeps Agiled Task sending fail-closed rather than guessing.

## Refrens `HTTP 400: Not allowed to send mail` — v1.0.0.1.40.2

The explicit Refrens invoice email endpoint is documented and the current Invio request shape matches that contract. If the provider returns `Not allowed to send mail`, v1.40.2 logs the message plus a separate `CODE 400` provider line. This is a Refrens-side API mail permission/capability rejection. Manual sending from the Refrens web dashboard does not prove that API mail permission is enabled. Resolve the provider-side permission before another live acceptance attempt; Invio does not bypass the rejection or falsely mark it successful.


## Odoo provider does not appear in Accounts

The production Odoo integration is shipped as an external trusted plugin, not an auto-installed packaged provider. Open **Providers → Load Provider**, select `providers/plugins/odoo/provider.json`, approve the trusted executable adapter, then add the Odoo Account. If API Test fails, verify Base URL, database technical name, username/email, API key, and that the Odoo user can access Accounting/invoice models.

If an Odoo Task becomes **Uncertain**, do not blindly create a new full Task for the same recipient. Inspect Odoo for an already-created/posted invoice or already-triggered email first; the P13/P10 non-idempotent safety boundary intentionally blocks assumptions after ambiguous external writes.
