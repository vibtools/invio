# Changelog

## v1.0.0.1.40.2 - Agiled API-Test Contract and Refrens Provider-Error Visibility Candidate

- Freezes owner-approved `v1.0.0.1.40.1` as the parent Official Baseline for this correction.
- Enables built-in Agiled API Test using the owner-supplied current OpenAPI contract: `GET https://api.agiled.ai/public/v1/me` with HTTP Bearer authentication.
- Keeps Agiled Task sending fail-closed because the current OpenAPI publishes invoice CRUD but no invoice email/send operation and no field-level invoice mutation schema; no guessed Agiled invoice request is introduced.
- Preserves the documented Refrens explicit post-create invoice email operation. The live `HTTP 400: Not allowed to send mail` response is classified as a provider-side API mail permission/capability rejection, not bypassed or falsely marked successful.
- Adds a separate provider Live Log status line such as `CODE 400` when Refrens returns machine-readable HTTP status metadata.
- Keeps SQLite schema v5, WorkerManager/Task architecture, Stripe behavior, provider credential shapes, dependencies and UI architecture unchanged.
- P11 remains **LIVE ACCEPTANCE PENDING**; P14 remains **CERTIFICATION PENDING**; production-ready remains **NO**.

## v1.0.0.1.40 - Refrens Live Send, Customer Defaults, Dark Popup/List and App Icon Correction Candidate

- Froze owner-approved `v1.0.0.1.39` as the parent baseline for this correction; v1.40 remains local/pre-release until live source and compiled-artifact acceptance.
- Corrected the confirmed Refrens HTTP 400 boundary by no longer serializing Invio `list[str]` terms into the Refrens create-invoice request; auth/email/ledger/retry architecture is unchanged.
- Added Settings-backed import defaults: configured Default Customer Name, otherwise email local-part; configured Default Customer Country, otherwise explicit imported country or `US` for missing country.
- Added explicit dark styling for `QListWidget`, `QTableWidget` surfaces and `QMenu`, and applies the existing Invio QSS application-wide so top-level context menus inherit the dark contract.
- Wired `assets/icons/app.png` / `assets/icons/app.ico` into QApplication/Windows AppUserModelID and the pinned Nuitka build. Owner supplies the actual binary icon assets before build.
- No SQLite schema, CredentialStore policy, WorkerManager, Task state-machine, provider manifest, dependency or architecture redesign.
- P11 remains LIVE ACCEPTANCE PENDING and P14 remains CERTIFICATION PENDING; production-ready remains NO.

## v1.0.0.1.39 - P14 Compiled Protected-Credential Storage Correction Candidate

- Frozen `v1.0.0.1.38` as the Official released parent baseline; `v1.0.0.1.39` is local/pre-release only and must not be tagged yet.
- Owner live Refrens API Test succeeded, but `Add Account` failed immediately afterward with `Protected credential storage is unavailable.`, proving the observed failure is in the initial compiled `CredentialStore` keyring import/dependency boundary rather than provider authentication.
- Closed the v1.38 certification coverage gap by explicitly freezing the existing keyring runtime dependency graph and keyring distribution metadata into the pinned Nuitka standalone build.
- Added CI-only compiled protected-credential set/get/delete round-trip execution in the OneDir executable and MSI-installed executable.
- Kept `CredentialStore` policy/no-plaintext-fallback behavior, runtime dependency versions, provider send logic, SQLite schema v5, Task/WorkerManager architecture, provider manifests, WiX/Nuitka pins and UI/UX unchanged.
- P11 remains LIVE ACCEPTANCE PENDING; P14 remains CERTIFICATION PENDING pending owner source/live sending and non-tagged compiled-artifact acceptance.

## v1.0.0.1.38 - P14 WiX Debug-Symbol Release Inventory Correction

- Audited GitHub Actions run `31386258538` / Windows job `93447256779`; all gates through MSI install/run/uninstall passed before release checksum inventory validation failed.
- Confirmed WiX 6.0.2 emits a sibling `.wixpdb` by default; this extra debug-symbol file was correctly included by the checksum writer but correctly rejected by the frozen release-payload audit.
- Added the documented `-pdbtype none` option to the existing WiX build command so `dist/release` contains only the approved portable ZIP, MSI and wheel before `SHA256SUMS.txt` is generated.
- Checksum writer, distribution auditor, MSI layout, WiX/Nuitka pins, provider behavior, SQLite schema, Task/WorkerManager architecture, runtime dependencies and UI/UX remain unchanged.
- P11 remains LIVE ACCEPTANCE PENDING; P14 remains CERTIFICATION PENDING until the exact v1.38 workflow and owner-controlled live-provider gates pass.

## v1.0.0.1.37 - P14 WiX Version Verification Correction

- Audited GitHub Actions run `31374749523`, Windows job `93411358955`.
- Confirmed WiX Toolset `6.0.2` installed successfully; the failure was the workflow's raw equality check against `wix --version` output `6.0.2+b3f3403`.
- Updated only the WiX verification guard to compare the canonical core version before the optional SemVer `+build-metadata` suffix.
- Retained pinned WiX `6.0.2`, Nuitka `4.1.3`, OneDir/portable/MSI/wheel/tag-release architecture, runtime dependencies, provider behavior, SQLite schema v5, P13 interface v1, WorkerManager/Task behavior and UI/UX.
- P11 remains LIVE ACCEPTANCE PENDING; P14 remains CERTIFICATION PENDING until the exact v1.37 Windows distribution workflow and owner-controlled provider-live gates pass.

## v1.0.0.1.36 - P14 GitHub Actions CI Verification Correction

- Forensically audited failed GitHub Actions run `31371279808` / Ubuntu job `93400604928` / Windows job `93400604966`.
- Fixed the publication root cause: broad `.gitignore` `build/` matched `scripts/build/`, so the v1.35 distribution helper scripts existed in the source baseline but were omitted by `git add -A`; the approved helper directory is now explicitly re-included while root build output remains ignored.
- Preserved the v1.35 Nuitka OneDir, portable ZIP, WiX MSI, wheel and tag-release workflow unchanged apart from the v1.36 version identity.
- Fixed Windows-only SQLite file-lock failures found by CI: the P14 crash-recovery verification query now explicitly closes its `sqlite3` handle, and `DomainStore._connect()` closes any partially initialized SQLite connection before re-raising setup/corruption errors.
- Added regression coverage for tracked `scripts/build/*` helpers and exceptional SQLite-handle cleanup.
- No provider API/send behavior, schema, provider manifest, WorkerManager, Task/customer/template model, UI/UX, runtime dependency or P13 interface change.
- P11 remains LIVE ACCEPTANCE PENDING; P14 remains CERTIFICATION PENDING until the exact v1.36 GitHub Windows build and remaining live-provider acceptance gates pass.

## v1.0.0.1.35 - P14 Windows Distribution and Release Pipeline Verification Correction

- Added the explicitly approved Windows distribution build while preserving the v1.34 wheel/resource corrections: pinned Nuitka `4.1.3` OneDir + PySide6 build, versioned portable ZIP, pinned WiX Toolset `6.0.2` per-user MSI, wheel retention and release checksum audit.
- GitHub Actions now produces Windows distribution artifacts on normal pushes/PRs; exact `v<application-version>` tags publish portable ZIP, MSI, wheel and `SHA256SUMS.txt` to GitHub Releases only after Ubuntu and Windows gates succeed.
- Scoped normal CI permissions to `contents: read`; only the tag-gated release job receives `contents: write`.
- Added deterministic public-five-part -> PE/MSI version mapping, portable preparation, WiX source generation, release checksum finalization and distribution auditing helpers/tests.
- Added an exact executable-directory resource fallback for Nuitka OneDir while preserving source/wheel module-relative resource resolution.
- MSI installation is per-user under LocalAppData to preserve the existing writable P13 provider registry without moving provider state or requiring UAC.
- Runtime dependencies, provider APIs/business logic, schema v5, WorkerManager, Task/customer/template models, P13 interface v1, Settings/Reports/Logs and page inventory remain unchanged.
- P11 remains LIVE ACCEPTANCE PENDING and P14 remains CERTIFICATION PENDING; the exact v1.35 Windows workflow and owner-controlled live provider gates are not represented as PASS until executed.

## v1.0.0.1.34 - P14 Certification Candidate

- Repaired the reproduced setuptools wheel packaging gap by including the existing `src.core.settings` package, packaged Stripe/Refrens/Agiled manifests and `assets/icons/checkmark.svg`; no provider manifest content or runtime dependency changed.
- Added `src/core/paths.py` for deterministic source-checkout/installed-wheel resource resolution and fail-closed required-resource validation.
- Retained Ubuntu GitHub Actions coverage and added a Windows/Python-3.12 job for full regression, wheel build/content audit, clean wheel install and native offscreen PySide6/keyring/resource/three-Task-QThread smoke.
- Added deterministic P14 local certification tests for a 10,000-recipient import, 1,000-recipient injected-transport execution soak and subprocess crash-after-write-ahead recovery.
- Local wheel build/content/isolated-install verification passes. Live Stripe/Refrens acceptance and executed native Windows certification are not available in this workspace, so P11 remains LIVE ACCEPTANCE PENDING, P14 remains CERTIFICATION PENDING, completed acceptance phases remain 12/14, and no production-ready claim is made.

## v1.0.0.1.33 - P13 Forensic Verification Correction

- Contained `BaseException` raised while reading/validating the object returned by external `create_adapter()`, so hostile/broken metadata such as `interface_version` cannot terminate Invio startup and is reported as an incompatible adapter instead.
- Made provider uninstall fail-closed/rollback-safe by staging active manifest/adapter registry names with `os.replace`; if the second move fails, the original manifest is restored and the provider remains installed instead of becoming half-uninstalled.
- Added focused P13 regressions for post-entrypoint metadata `SystemExit` containment and uninstall rollback after adapter-move failure.
- Preserved interface version 1, provider capability semantics, P06/P08/P10 integration, packaged Stripe/Refrens behavior, Agiled fail-close, SQLite schema v5, dependencies, page inventory and one-QThread-per-Task ownership.
- P13 remains COMPLETE; completed acceptance phases remain 12/14. P11 remains IMPLEMENTED / LIVE ACCEPTANCE PENDING and P14 remains the final production-certification phase.

## v1.0.0.1.32 - P13 Executable External Provider Adapter Contract

- Added explicit `ExternalProviderAdapterV1` interface version 1 and optional `provider.json` + sibling `adapter.py` executable bundle support through the existing Load Provider workflow.
- Added trusted in-process adapter confirmation, staged immutable-byte validation before atomic registry replacement, reserved packaged-ID protection, exact ID/interface/version/profile/capability validation, import/entrypoint failure containment, and persistent `sys.path` tamper rejection/restoration.
- External API Test now uses the existing threaded verification path and cannot report success until at least one host-managed `SAFE_READ` succeeds.
- External Tasks reuse P05 immutable inputs, P06 preflight, P08 bounded reliability, optional P09 pacing and P10 write-ahead ledger/recovery through host-managed SAFE_READ / IDEMPOTENT_MUTATION / NON_IDEMPOTENT_MUTATION operations. Adapter validation/execution receives isolated template data; recipient success requires successful host-managed mutating evidence with a matching final stage.
- Ambiguous non-idempotent mutations, adapter failures after successful non-idempotent mutation, and restart windows where mutation success exists without recipient finalization remain durable `Uncertain` when safe replay cannot be proven. SQLite remains schema v5 with exactly the existing three P10 tables.
- Manifest-only external providers remain loadable but non-executable; executable external replacement/uninstall is blocked while current Tasks reference the provider.
- Packaged Stripe/Refrens business behavior, Agiled fail-close, WorkerManager, dependencies and page inventory remain unchanged.
- P13 is COMPLETE; completed acceptance phases are 12/14. P11 live Refrens acceptance remains pending; P14 remains the final production-certification phase.

## v1.0.0.1.31 - P12 Forensic Verification Correction

- Corrected centralized secret redaction so quoted JSON-style named secrets such as `accessToken`, `appSecret`, `api_key`, `secret_key`, `authorization` and `token` are masked even when their values are not already known account credentials.
- Corrected recipient support reporting so `Provider Accepted`/`Accepted` requires durable send-stage success evidence; a contradictory recipient `Succeeded` row without send evidence fails closed as `Uncertain`.
- Recipient reporting now preserves unresolved mutating ambiguity even if a later recipient row claims success, and fails closed on conflicting historical primary/assigned account evidence.
- Added focused regression coverage for all three forensic cases.
- SQLite remains schema v5 with exactly three P10 ledger tables; provider send semantics, P09 scheduling, P10 recovery/idempotency, WorkerManager, Task/customer/template models, provider manifests, dependencies and page layout are unchanged.
- P12 remains COMPLETE. P11 remains IMPLEMENTED / LIVE ACCEPTANCE PENDING. Completed acceptance phases remain 11/14.

## v1.0.0.1.30 - P12 Reports, Logs, Privacy and Operational Observability

- Adds recipient-level reconciliation backed exclusively by the existing P10 delivery ledger, including safe status, distinct attempts, account reference, provider invoice reference, last stage/error code, provider-send acceptance and independent email-delivery state.
- Presents successful provider send evidence as **Provider Accepted** and never as independently confirmed email delivery without a separate delivery event.
- Adds structured `INFO/WARNING/ERROR` logs with bounded operational categories and preserves plain TaskExecutionContext log compatibility.
- Generalizes provider-secret redaction and masks recipient email in Live Logs while retaining full email only in explicit Reports/recipient exports.
- Preserves Task CSV export, adds Recipient CSV export, uses atomic writes, handles export failures without crashing Qt event handlers, and neutralizes spreadsheet formula injection in CSV text cells.
- Defines delivery-ledger retention as indefinite by default and adds confirmed clearing of only already-closed Task history; open Task recovery rows remain protected.
- Keeps SQLite schema v5, exactly three P10 ledger tables, provider manifests, dependencies, provider send semantics, P09 scheduling and P10 idempotency/recovery unchanged.
- P12 is COMPLETE. P11 live Refrens acceptance remains pending; completed acceptance phases are 11/14.

## v1.0.0.1.29 - P11 Refrens End-to-End Task Implementation Candidate

- Enables the built-in Refrens adapter for Task invoice/send execution using the existing immutable customer email/name/country records; all three values are required and no customer data is guessed.
- Preserves the exact `https://api.refrens.com` trust boundary before App ID/App Secret construction/transmission and blocks Indian recipients before invoice creation because the approved customer model has no Refrens-required GST State field.
- Adds the Refrens batch runner to the existing Task-owned QThread pipeline, frozen round-robin account assignment, exact attempted-account binding, 1 request/second/account burst-1 Invio safety pacing and existing P09 provider-health handling.
- Applies P08 bounded retry only to Refrens authentication; the invoice-create/email mutation is single-shot and ambiguous timeout/disconnect/408/5xx outcomes become durable P10 `Uncertain` evidence instead of being blindly replayed.
- Records `refrens_authentication` and `refrens_invoice_create_email` write-ahead operations in the existing schema-v5 ledger, persists returned invoice `_id` as provider invoice/reference evidence, and never persists JWT/App Secret.
- Keeps Refrens uncertain recipients out of automatic Resume; Pending/Failed durable continuation remains restart-safe under existing action rules.
- No UI page, customer field, schema migration, dependency, WorkerManager change, Stripe change, Agiled enablement or P12+ behavior is included.
- **Release status:** P11 **IMPLEMENTED / LIVE ACCEPTANCE PENDING**. Production progress remains **10/14**; `v1.0.0.1.28` remains the latest completed-phase Official Baseline until owner live API Test, real invoice creation and recipient email-delivery acceptance pass.

## v1.0.0.1.28 - P10 Verification Correction

- Re-audits the exact `v1.0.0.1.27` P10 durable-ledger implementation.
- Corrects stale uncertainty classification after a later successful replay of the same mutating stage with the exact same non-empty idempotency key.
- Preserves unresolved mutating uncertainty across later runs until that exact stage/idempotency identity is successfully reconciled; unrelated deterministic failures can no longer hide it.
- Adds fail-closed historical recipient/provider/primary-account/assigned-account consistency checks to durable summary reconstruction.
- SQLite remains schema v5 with exactly three P10 audit tables; no WorkerManager, Task-state, provider manifest, dependency, UI-page, Stripe business-flow, Refrens, Agiled or P11+ behavior change.
- Production progress remains **10/14**; P11 remains next and separately approval-gated.

## v1.0.0.1.27 - P10 Persistent Delivery Ledger, Idempotency and Recovery

- Advances operational SQLite storage from schema v4 to schema v5 using the existing transactional pre-migration backup path and adds exactly three durable delivery-ledger tables: runs, per-run recipients and provider operations.
- Adds a unique execution `run_id` per First Run / Resume Remaining / Retry Failed invocation while preserving `Task.id` as the canonical Stripe idempotency identity.
- Adds write-ahead `Started` operation persistence before each Stripe Task transport call, durable P08 attempt/stage/idempotency/account evidence, provider customer/invoice IDs, sanitized errors and final recipient outcomes.
- Reconciles interrupted runs on restart, classifies unresolved mutating operations as `Uncertain`, derives Task counters and durable Resume/Retry sets from ledger evidence, and preserves P09 exact attempted-account binding across restart.
- Retains delivery history after Close Task and preserves fail-closed behavior for pre-P10 non-pristine Tasks without fabricating historical records.
- Preserves one Task = one QThread, P05-P09 semantics, Stripe business flow, Refrens P11 gate, Agiled fail-close, dependencies, provider manifests, Settings/UI design and P11+ scope.
- Production progress advances to **10/14**; **P11 - Refrens End-to-End Task Enablement** is next.

## v1.0.0.1.26 - P09 CI / Repository-Contract Verification Correction

- Reproduces GitHub Actions run `31336019074` / job `93301866645`, where `test_p09_completion_records_are_synchronized` failed because a public CI checkout does not contain the intentionally Git-ignored private `project/` tree.
- Corrects the P09 repository-contract test so mandatory CI assertions use tracked public completion records; private `project/` completion records remain additionally verified when the full private baseline is present.
- Adds an explicit current-release metadata contract for `v1.0.0.1.26` while retaining historical compatibility test names under the no-removal baseline rule.
- Keeps the P09 runtime scheduler, rate/health/failover behavior, one-task-one-QThread boundary, SQLite schema v4, dependencies, Stripe send flow/idempotency, Refrens P11 gate, Agiled fail-close behavior, provider/plugin architecture and P10+ scope unchanged.
- Production progress remains **9/14**; **P10 - Persistent Delivery Ledger, Idempotency and Recovery** remains next.

## v1.0.0.1.25 - P09 Multi-Account Scheduling, Limits and Health

- Preserves the frozen `recipient_ordinal_round_robin_v1` primary assignment and P05 account ordering.
- Adds the internal Stripe scheduling policy: 20 API requests/second/account, burst capacity 1, with cooperative rate waits.
- Adds runtime-only account/provider health with bounded 5/10/20/40/60-second cooldown progression and `Retry-After` extension.
- Uses deterministic circular fallback only for not-yet-attempted recipients whose primary account is cooling after a recognized account-scoped Stripe rate-limit condition.
- Adds current-session attempted-recipient account binding so a recipient that has already entered provider execution is never replayed on another account during Resume/Retry.
- Applies provider-wide cooldown without account hopping for timeout/disconnect/HTTP 408/5xx failures.
- Blocks repeated network use after HTTP 401/403 account authentication/permission failures until successful account re-verification clears runtime health.
- Keeps deterministic customer/template/operation errors non-failover and preserves P08 retry/idempotency behavior.
- Preserves one Task = one QThread with intra-Task concurrency fixed at 1; no P10 ledger, schema, dependency, provider-send, Refrens, Agiled, plugin, Settings, page or layout change.
- Production progress advances to **9/14**; **P10 - Persistent Delivery Ledger, Idempotency and Recovery** is next.

## v1.0.0.1.24 - P08 Forensic Verification Correction

- Re-audits the exact shipped `v1.0.0.1.23` P08 Worker and Network Reliability implementation.
- Reproduces and fixes a transient-disconnect classification gap where `http.client.IncompleteRead` escaped the structured retry boundary and became an unexpected non-retry recipient failure.
- Treats TLS EOF/clean-close interruptions as retryable transient disconnects while preserving permanent certificate-verification and non-transient TLS handling.
- Preserves known HTTP status/`Retry-After` classification when an HTTP error body is itself truncated.
- Keeps the approved maximum three total attempts, 0.5s/1.0s exponential backoff, 0-25% jitter, same-recipient/same-account/same-Stripe-idempotency behavior, one-task-one-QThread architecture, safe asynchronous shutdown, schema v4, dependencies, Refrens P11 gate, Agiled fail-close, and all P09+ behavior unchanged.
- Corrects stale private P08 completion/error-handling records so the authoritative phase documents consistently show **8/14 complete**, **6/14 remaining**, and **P09 next**.
- Production progress remains **8/14**; this correction does not implement P09.

## v1.0.0.1.23 - P08 Worker and Network Reliability

- Adds structured provider/network failure classification with retryable/permanent metadata, HTTP status and parsed `Retry-After` where available.
- Adds a maximum of three total recipient attempts using bounded exponential backoff (0.5s, 1.0s before jitter) with 0-25% jitter and an 8-second exponential cap.
- Handles transient timeout/disconnect, HTTP 408/429/500/502/503/504 automatically; deterministic 4xx, invalid responses and TLS certificate verification failures remain permanent.
- Preserves original task/account assignment and existing deterministic Stripe idempotency keys across automatic retries; retry attempts do not increment Task progress.
- Makes retry waits Pause/Stop-aware and prevents a Stop request from starting the next retry or recipient.
- Replaces the unsafe fixed 1500 ms shutdown wait with cooperative asynchronous shutdown; the application does not accept close while a task-owned QThread remains active and never force-terminates workers.
- Isolates unexpected per-recipient exceptions and reconciles each recipient exactly once in aggregate progress.
- Keeps one task-owned QThread per active Task, SQLite schema v4, dependencies, Stripe/Refrens send contracts, Agiled fail-close behavior and P09+ scope unchanged.
- Verification: 254/254 tests PASS plus repository/syntax/privacy/provider audits. Native Qt/keyring launch is not certified in the current audit environment because those runtime packages are unavailable.
- Production progress advances to **8/14**; **P09 - Multi-Account Scheduling, Limits and Health** is next.

## v1.0.0.1.22 - Pre-P08 Provider Adapter Forensic Verification

- Re-audits the exact `v1.0.0.1.21` Provider Adapter Foundation + Agiled release against its approved scope and `v1.0.0.1.20` parent baseline.
- Confirms no functional defect, fake/demo execution path, scope regression, Stripe/Refrens behavior change, P08/P09+ behavior, Refrens P11 enablement, schema migration, dependency change, or WorkerManager change was introduced by `v1.0.0.1.21`.
- Adds missing verification gates for packaged Agiled install/uninstall, registered executable handler resolution, and generic UI manifest/API-test gating.
- Revalidates the current Agiled public contract conflict and preserves the no-network fail-closed Agiled behavior; no API key is transmitted and no Agiled invoice request is attempted.
- Updates release metadata/documentation to `v1.0.0.1.22`; provider/invoice runtime behavior is otherwise unchanged.
- Production progress remains **7/14** and **P08 - Worker and Network Reliability** remains next.

## v1.0.0.1.21 - Pre-P08 Provider Adapter Foundation + Agiled

- Introduces `src/core/provider_runtime/adapters.py` as the internal packaged-provider runtime contract registry.
- Routes executable capability lookup, packaged manifest/runtime reconciliation, API Test dispatch and Task batch dispatch through the registry without changing existing Stripe network behavior.
- Preserves Refrens API Test and its P11 production Task gate.
- Adds the packaged `agiled` provider manifest with a protected `API Key` credential field.
- Registers Agiled as fail-closed with zero executable capabilities because the current authoritative base URL/authentication/invoice-send contract could not be reconciled from the accessible official Agiled materials. No Agiled API key is transmitted and no invoice request is attempted.
- Adds adapter/Agiled contract regression tests; current suite is 237/237 PASS before final packaging.
- Keeps SQLite schema v4, P05 immutable snapshots, P06 preflight, P07 state/resend semantics, WorkerManager, UI workflow and dependencies unchanged.
- Does not implement P08/P09+, enable Refrens P11, or complete the dynamic external-provider architecture planned for P13.

## v1.0.0.1.20 - P07 Forensic Verification and Resend-Safety Correction

- Re-audited the exact shipped `v1.0.0.1.19` P07 implementation against its approved state-machine/resend plan.
- Reconciles a late worker `Completed` terminal signal to `Stopped` when a valid late Pause/Stop UI state has already been accepted, preserving the approved transition table and avoiding a terminal-state race.
- Requires an actually active WorkerManager thread before Pause/Resume/Stop can be enabled or accepted, preventing stale controls after worker completion.
- Distinguishes a proven-safe empty continuation set from an unavailable recipient set so Stopped/Failed correction messages remain truthful.
- Keeps P07 deterministic First Run / Resume Remaining / Retry Failed send-set semantics, P05 immutable snapshots, P06 preflight, account reservations, SQLite schema v4, WorkerManager architecture, provider contracts and dependencies unchanged.
- Production progress remains **7/14**; P08 remains separately approval-gated.

## v1.0.0.1.19 - P07 Task State Machine and Resend Safety

- Completed production phase **P07** on the verified `v1.0.0.1.18` P06 baseline while preserving SQLite schema v4, P05 immutable execution snapshots, P06 preflight, WorkerManager, packaged provider contracts, dependencies, and P08+ scope.
- Added a centralized `Ready/Running/Paused/Stopping/Stopped/Failed/Completed` Task transition/action policy. `Start` is now first-run-only for pristine `Ready` Tasks.
- Replaced unsafe Stopped full restart with **Resume Remaining**, using only the exact current-session failed-plus-never-attempted recipient set in immutable P05 order.
- Restricted **Retry Failed** to the exact current-session failed-recipient set; successful recipients are excluded, and repeated retries shrink to only unresolved failures.
- Blocked `Completed` resend and Failed normal Start at both UI and backend action boundaries.
- Reconciled Stop/final counters from the same runtime failed/pending sets so `success + failed == processed` and `remaining == total - processed`.
- Made application-restart continuation fail closed: aggregate counters remain durable, but exact recipient identities are not guessed; Retry/Resume is disabled until P10 provides a durable delivery ledger.
- Preserved the injected runner registration API for first runs while blocking unsafe injected-runner Retry/Resume fallback.
- Preserved Account reservations until existing **Close Task** release and retained P06 preflight before every permitted new worker attempt.

## v1.0.0.1.18 - P06 Forensic Verification & Contract Correction

- Re-audited the exact v1.0.0.1.17 P06 release against its approved capability/preflight plan.
- Hardened built-in packaged-manifest reconciliation against hard-coded executable credential/mode/capability contracts instead of allowing a modified packaged manifest to validate itself.
- Added frozen Account-input binding validation to Task preflight.
- Made Refrens use the existing safe currency catalogue for static validation and restricted its trusted base URL to canonical `https://api.refrens.com` with no explicit port.
- Corrected Providers capability truthfulness by displaying the actual installed manifest and fail-closing effective runtime capability on packaged/runtime mismatch.
- Corrected the static Stripe currency certification record: Stripe availability is account-country dependent; region-specific three-decimal currencies remain blocked because the current Invio minor-unit sender does not implement that contract.
- SQLite remains schema v4; WorkerManager, P05 snapshots, provider manifests, dependencies, external runner API, Stripe send semantics, Refrens P11 gate and P07+ behavior remain unchanged.

## v1.0.0.1.17 - P06 Provider Capability and Preflight Validation

- Completed production phase **P06** on the verified `v1.0.0.1.16` P05 baseline without changing SQLite schema v4, WorkerManager, P05 immutable snapshots, provider manifests, dependencies, external runner API, or P07+ behavior.
- Added a pure/no-side-effect provider preflight contract used before New Task creation and before Start/Retry runner creation. Unsupported combinations are rejected before any provider invoice/customer mutation.
- Reconciled packaged manifest declarations with actual built-in runtime capability. Stripe exposes executable invoice/send/API-test capability; Refrens exposes executable API Test only while normal Task execution remains intentionally blocked until P11.
- Reserved packaged provider IDs prevent an external manifest from replacing the `stripe` or `refrens` manifest/runtime contract. Existing mismatched installed packaged-runtime manifests fail closed and require explicit uninstall/reinstall rather than silent replacement.
- Added account-health preflight for provider identity, `Verified` status, timezone-aware verification timestamp, empty verification-error state, supported account mode, required credentials, and Stripe mode/key consistency.
- Added Stripe preflight safety gates: current Invio Stripe adapter accepts standard `INVOICE` only; Automatic Tax is blocked because the current Customer contract cannot guarantee Stripe Tax location requirements; non-zero template line-tax percentages are blocked because the Stripe runtime does not map them to Stripe TaxRate objects.
- Pinned Refrens credential transport to canonical `https://api.refrens.com` before authentication payload construction, rejecting deceptive hosts/credentials/path/query/fragment variants before App ID/App Secret can be sent.
- Providers UI now distinguishes **Declared capabilities** from current **Runtime capabilities** without adding a new page or changing the provider-manifest schema.
- Revalidated current Stripe/Refrens assumptions against primary provider documentation and recorded the release evidence. Production progress is **6/14**; P07 remains separately approval-gated.

## v1.0.0.1.16 - P05 Forensic Verification & Consistency Correction

- Re-audited the exact shipped `v1.0.0.1.15` P05 baseline against the approved immutable-execution plan.
- Corrected the normal post-P05 persistence path so a new Task with no captured snapshot (or an explicit `LegacyUnavailable` snapshot) is rejected transactionally instead of being silently reclassified as a pre-P05 legacy Task.
- Added snapshot-bound progress validation: captured Tasks reject inconsistent processed/success/failed state at runtime persistence boundaries and on startup load.
- Stopped routine Task status/progress updates from rewriting the immutable `tasks.total` column; captured Task total drift now fails closed against the frozen recipient snapshot.
- Preserved schema v4, Task.id run identity, Customer/Template immutability, P03/P04 behavior, ProviderManager, WorkerManager, provider-send semantics, dependencies and UI/UX.
- Added focused regression coverage and synchronized P05 verification/release documentation. Production progress remains **5/14**; P06 is still approval-gated.

## v1.0.0.1.15 - P05 Immutable Task Execution Snapshot and Input Consistency

- Completed production phase **P05** without changing WorkerManager, ProviderManager, provider manifests, provider-send semantics, dependencies, or unrelated UI.
- Added frozen Task execution-snapshot contracts for ordered customer records, copied invoice-template data/items/terms, provider ID, ordered Account basis, and the existing `recipient_ordinal_round_robin_v1` assignment strategy.
- `AppState.create_task()` now captures the snapshot at Task creation and derives `Task.total` from the frozen recipient set.
- Upgraded durable SQLite storage from schema v3 to **schema v4** with dedicated Task snapshot tables and transactional Task + account reservation + snapshot creation.
- ProviderRuntime Start/Retry now reads the Task's durable immutable snapshot instead of the live Customer List or live Invoice Template. Later list/template edits cannot change an existing Task run or retry.
- Defined **`Task.id` as the canonical logical run identity**. A different recipient/template/provider/account-basis execution requires a new Task and therefore a new Task ID.
- Preserved pre-P05 Tasks during v3-to-v4 migration as `LegacyUnavailable` without fabricating historical recipients/template data from current state. Legacy Tasks remain visible/closable but Start and Retry fail closed.
- Added corruption-safe validation for provider, account order, snapshot state, template presence, invoice items, and Task-total/recipient-count agreement.
- Added P05 state/storage/runtime/UI/repository regression tests while preserving prior tests and release compatibility aliases.
- Production progress advances to **5/14**; P06 remains separately approval-gated.

## v1.0.0.1.14 - Windows Operational Storage Runtime Hotfix

- Reproduced the reported Windows startup failure in the SQLite pre-migration backup path: the temporary backup database remained open when `Path.replace()` attempted `.bak.tmp -> .bak`, producing `WinError 32`.
- Root cause: Python's `sqlite3.Connection` context-manager protocol does not close the connection on `with` exit; it only commits/rolls back.
- Fixed `DomainStore._create_migration_backup()` to explicitly close the SQLite backup destination before the atomic replacement while preserving SQLite live-backup/WAL semantics.
- Added a regression test that fails if the migration backup destination is still open at replacement time.
- Kept SQLite schema v3, migration order, protected credential storage, ProviderManager, WorkerManager, provider send behavior, customer/import behavior, UI/UX and all P01-P04 features unchanged.
- Production phase progress remains **4/14**; P05 is still the next separately approved phase.

## v1.0.0.1.13 - P04 Verification & Correction

- Re-audited the exact shipped `v1.0.0.1.12` P04 baseline against the approved P04 plan and preserved the 4/14 production-phase status.
- Restored the pre-P04 mutable-list behavior of `CustomerList.emails` while retaining `CustomerRecord` as the authoritative customer representation and preserving existing name/country metadata for unchanged emails.
- Preserved source row numbers through structured/legacy imports so conflicts against existing Customer List metadata are row-numbered instead of email-only.
- Tightened explicit country validation to two ASCII alphabetic characters in both the customer contract and the Refrens payload helper; country is still never guessed.
- Converted malformed customer-workbook/parser failures into the existing caught `ValueError` import boundary so invalid files cannot escape as uncaught parser exceptions.
- Reverted the unrelated Dashboard `Customer Emails` label that P04 had changed outside the approved Customer Lists UI scope.
- Added regression coverage for all corrections; no P05+, Refrens Task enablement, dependency, provider manifest, WorkerManager/ProviderManager, Account/Invoice/Task model, or shared UI design-system change is included.

## v1.0.0.1.12 - P04 Customer Data Contract and Import Upgrade

- Added backward-compatible `CustomerRecord` data with mandatory normalized email plus optional explicit name/country; no name/country inference.
- Added structured CSV/TSV/XLSX/XLSM imports using `email`, `name`, `country` headers while preserving TXT and legacy email-extraction behavior.
- Added row-numbered validation, deterministic duplicate/conflict handling, and safe enrichment of previously blank customer metadata.
- Upgraded durable domain schema from v2 to v3 by adding customer `name`/`country` columns to the existing ordered `customer_emails` table with WAL-aware migration backup.
- Added transactional customer-record persistence and kept `CustomerList.emails`, `AppState.add_emails()` and `import_emails()` backward compatible.
- Upgraded task runtime snapshots to carry customer records while preserving the email-only view and unchanged Stripe customer/send behavior.
- Kept Refrens production Task execution disabled until P11 even when explicit name/country is available.
- Updated Customer Lists UI to display Email, Name and Country and provide bounded import-result diagnostics.
- No new page, dependency, Account/Invoice/Task model redesign, WorkerManager/ProviderManager architecture change, provider manifest change, or P05+ implementation is included.

## v1.0.0.1.11 - P03 Verification & Correction

- Re-audited the exact shipped `v1.0.0.1.10` P03 baseline without introducing P04 functionality.
- Fixed schema-v1 migration backup fidelity: backups now use SQLite live-backup semantics so committed data still present in WAL is included instead of copying only the main database file.
- Fixed credential-loss recovery durability: missing/unreadable protected credentials now persist the Account `Not Verified` state and safe error summary before startup completes, so a later-restored secret cannot silently resurrect a stale durable `Verified` state.
- Hardened Account Edit across SQLite and protected credential storage by staging a durable `Not Verified` safety state before replacing credentials. Successful edits finish as `Verified`; fully successful rollback restores the prior Account; failed compensation remains explicitly non-executable in memory and durable storage.
- Added regression coverage for committed-WAL migration backups, durable credential-loss downgrade, final Account Edit database rollback, and fail-closed compensation failure.
- Updated runtime/release metadata to `v1.0.0.1.11` and synchronized README, roadmap, error-handling, implementation-status, architecture, phase ledger, release notes and private forensic records.
- P03 remains the completed production phase; progress remains **3/14** and P04 is not implemented.
- No provider manifest, provider runtime behavior (except release User-Agent), WorkerManager, ProviderManager, Customer/Invoice/Task model, UI page/design, dependency, credential-storage technology, or SQLite schema-version change is included.

## v1.0.0.1.10 - P03 Account Lifecycle, Verification Health and Provider-Install Consistency

- Added reservation-safe Account **Edit**, **Re-test**, and **Delete** workflows without adding a new page.
- Account Edit keeps provider identity immutable and requires a new successful real API Test before saving metadata/credential changes. Failed candidate verification does not overwrite the saved account.
- Added durable `last_verification_at` and secret-scrubbed `verification_error_summary` metadata with SQLite schema v2 and transactional v1-to-v2 migration backup.
- Added protected-credential compensation for Account update/delete failure paths; no plaintext fallback is introduced.
- Provider uninstall now blocks while a provider Task has an active worker, preserves existing accounts/tasks/reservations/credentials when inactive, and keeps those accounts visible as **Not Installed**.
- Task Start/Retry now fail closed when the Task provider is not currently installed.
- Re-test failure persists `Not Verified`, so existing P01 creation/Start/Retry gates prevent execution with known-invalid credentials.
- If a failed Re-test cannot be persisted, the current process still fails the Account closed to `Not Verified`; a successful Re-test never elevates an Account unless its durable verification-health write commits.
- Corrected the Accounts credential label from the stale `Stored in memory` text to the actual protected-storage state.
- No verification-age expiry, background health polling, WorkerManager change, provider manifest change, invoice/customer/task model redesign, or P04+ feature is included.


## v1.0.0.1.9 - P02 verification corrective release

- Re-audited the exact `Invio_v1.0.0.1.8.zip` P02 baseline against the approved P02 implementation plan.
- Fixed a re-entrant persistence-failure path in `MainWindow._task_persistence_failure()` by recording the task fault before requesting WorkerManager Stop, preventing recursive Stop/status persistence handling while storage remains unavailable.
- Hardened startup domain validation so persisted Task account selections and `account_reservations` must match exactly; missing or conflicting reservation state now fails closed instead of restoring a task/account exclusivity mismatch.
- Added regression coverage for both corrections while retaining every pre-existing test method under the no-removal baseline contract.
- Corrected stale production-roadmap summary metadata that still reported P01-only progress after P02 completion.
- Corrected `vibproject.ygit` P02 dependency/release metadata so the approved `keyring>=25.7,<26` dependency and current release version are represented consistently with `requirements.txt` and `pyproject.toml`.
- No P03-or-later feature, UI redesign, provider behavior, WorkerManager architecture, domain model field, provider manifest, or credential-storage technology change is included.

## 1.0.0.1.8 - 2026-08-08

### P02 - Durable Domain Storage and Protected Credentials
- Added SQLite-backed durable operational storage for Accounts metadata, Customer Lists/emails, Invoice Templates/items/terms, Tasks, task-account ordering, task counters/messages, and account reservations.
- Added schema version 1 with foreign-key enforcement, WAL journal mode, synchronous FULL durability, transactional writes, ordered migration handling, pre-migration backup, future-schema rejection, and corruption-safe startup that does not overwrite an unsafe database.
- Added protected provider credential storage through the owner-approved `keyring` mechanism. Operational SQLite/settings data stores only an opaque credential reference; there is no plaintext-file fallback.
- Added compensation handling so an Account is not committed to memory/database if protected credential persistence or Account metadata persistence fails. If automatic protected-secret cleanup also fails, the failure is surfaced rather than silently ignored.
- Added startup recovery. Persisted Accounts/Lists/Templates/Tasks/Reservations are reconstructed before pages are built; missing/unreadable protected credentials restore the Account as `Not Verified`, and previously active Tasks recover as existing status `Stopped` without automatic sending.
- Integrated transactional persistence into approved AppState mutations and task status/progress updates. An active Task receives a stop request if its operational-state persistence fails.
- Kept P01 verification gates, provider runtimes, provider manifests, one-QThread-per-active-Task WorkerManager architecture, existing pages, and invoice/customer/task domain behavior unchanged outside the P02 persistence boundary.

### Security / dependencies
- Added approved dependency `keyring>=25.7,<26`. Production credential access fails closed unless an approved OS-protected keyring backend is active; injected test backends are used only by deterministic unit tests.
- Provider secret values are not persisted in `domain.sqlite3`, `settings.json`, project files, or P02 logs.

### Verification boundary
- Added P02 storage/migration/rollback/recovery/secret-boundary tests.
- Full native PySide6 launch and native OS-keyring integration are not claimed in the audit container where those runtime packages/backends are unavailable; final live/native certification remains P14.
- P02 does not implement the P10 recipient-level delivery ledger or provider-side crash reconciliation.

## Production Readiness Documentation - 2026-08-08 (runtime remained v1.0.0.1.5)

### Documentation
- Frozen `v1.0.0.1.5` as the production-hardening planning baseline without changing runtime code or the application version.
- Added a forensic production-readiness report covering Provider, Accounts/API Test, Customer Lists, Invoice Templates, Tasks, worker threading, Stripe/Refrens execution, retry, persistence, reports/logs, shutdown safety, and test-certification gaps.
- Added an ordered `G0 + P01-P14` production roadmap, phase completion ledger, and strict production update protocol.
- Added developer-facing Actual Implementation Status and Error Handling inventories so working/partial/missing behavior is updated after every future phase.
- Added the missing `BASELINE_FREEZE_v1.0.0.1.5.md` private baseline record.

### Scope protection
- Documentation-only delta: no file under `src/`, `providers/`, `tests/`, `assets/`, `requirements.txt`, `pyproject.toml`, or runtime metadata is changed.
- No production phase is authorized by these planning documents; each phase still requires a separate explicit owner scope lock.

## 1.0.0.1.7 - 2026-08-08

### P01 verification correction
- Re-audited the exact uploaded `v1.0.0.1.6` full artifact against the approved P01 plan.
- Confirmed the P01 runtime implementation itself is present: real Stripe/Refrens API Test adapters, Stripe Test/Live mode check, dedicated Add Account verification `QThread`, current-session `Verified` state, and New Task/create/start/retry gates.
- Fixed stale shipped Refrens installed-registry metadata that still exposed `1.0.3-ui` and deferred-backend wording even though the bundled provider manifest was already production-clean.
- Corrected the runtime-surface production-marker test to exclude mutable Git-ignored provider registry state while retaining source and bundled-provider checks.
- Corrected the stale release-metadata test name and synchronized release metadata/documentation to `v1.0.0.1.7`.
- Added truthful post-release errata to the `v1.0.0.1.6` verification records: the exact uploaded full artifact initially ran 61/62 tests because of the stale registry state.

### Scope protection
- No P01 provider API behavior, credential field, provider ID/mode, task-worker architecture, invoice-send workflow, Customer List/Invoice Template model, persistence mechanism, page design, or dependency was expanded or replaced.
- Production phase count remains 1/14; P02 remains the next separately approved phase.

## 1.0.0.1.6 - 2026-08-08

### Added / Changed
- Completed production phase **P01 - Real Account API Verification**.
- Wired the existing `ProviderRuntime.test_account()` adapter into Add Account instead of treating required-field presence as a successful API test.
- Added executable API-test capability detection for built-in Stripe/Refrens adapters; providers without a real test adapter now show API Test as unavailable.
- Added a dedicated dialog-owned `QThread` for account API verification so network calls do not execute on the GUI thread.
- Made Stripe API verification mode-aware: Test mode accepts test keys and Live mode accepts live keys before provider requests are attempted.
- Successful API verification now creates the account with current-session status `Verified`; changing provider/mode/credential input invalidates the prior verification.
- Added verified-account gates to New Task selection, backend Task creation, and Start/Retry preparation.
- Added secret-safe API-test success/failure logging and user-facing provider/network failure messages.

### Tests / Verification
- Added provider-runtime tests for executable API-test support, Stripe real permission-request flow, Stripe mode mismatch fail-closed behavior, Refrens auth/access verification, and unsupported adapter rejection.
- Added state regression coverage proving unverified accounts cannot create Tasks.
- Added UI source contracts for threaded Add Account verification and selection/start gating.
- Existing provider sending, Invoice Template, Settings, provider registry, account reservation, and per-task worker contracts remain covered.

### Scope protection
- No provider credential fields, provider IDs, account modes, provider manifests, Customer List schema, Invoice Template behavior, persistence mechanism, task worker architecture, or third-party dependency was changed.
- P02 and later production phases remain pending and require separate owner approval.

## 1.0.0.1.5 - 2026-08-08

### Fixed
- Repaired the Invoice Template editor's broken vertical geometry introduced by the previous anti-stretch sizing override.
- Removed Invoice Template card-level `QSizePolicy.Maximum` overrides that allowed compact scroll-area layouts to shrink cards below the height required by their controls and wrapped helper text.
- Added an Invoice-Template-local minimum-height/height-for-width text contract so wrapped descriptions and captions retain the space required for their rendered text without changing shared application widget behavior.
- Moved Currency and Invoice Type helper text onto dedicated full-width grid rows so narrow form columns cannot make those notes collide with the following label/control.
- Wrapped the two-column upper form region in a bounded minimum-height host and top-aligned the Invoice Template cards so surplus scroll viewport space is absorbed only by the terminal stretch instead of creating broken gaps between sections.
- Applied a minimum-size constraint to the Invoice Template scroll content layout so the resizable scroll area scrolls when content needs more height instead of compressing the form below its minimum geometry.
- Fixed the compact note/footer text editors to a stable 52 px height so their controls cannot collapse under layout pressure.

### Verification
- Replaced the prior source contract that required the faulty `QSizePolicy.Maximum` behavior with regression checks for minimum-content sizing, dedicated caption rows, top-aligned bounded cards, and stable multiline editor heights.
- Re-ran the complete project test suite and repository audit after applying the update to the frozen `v1.0.0.1.4` baseline.
- Updated release metadata, README, versioning, Invoice Template documentation, release notes, patch manifest, and private forensic/update records.

### Scope protection
- This release changes only Invoice Template UI geometry plus mandatory release metadata/documentation/tests.
- Invoice-template fields, validation, currency catalog/search behavior, provider mapping, task binding, account/customer models, provider runtimes, worker-thread behavior, other pages, dependencies, and public APIs are unchanged.

## 1.0.0.1.4 - 2026-08-07

### Fixed
- Removed Windows light/white scroll-content surfaces from Settings and the Invoice Template editor by explicitly applying the frozen Vib Tools page background to application scroll viewports/content hosts.
- Corrected Invoice Template card/stretch behavior so compact sections keep their intended height and spacing instead of expanding into broken empty gaps.
- Rebalanced the Currency and Days until due controls so the Currency field is intentionally narrower and aligned with the compact template form.

### Changed
- Currency selection is now editable type-to-search with case-insensitive contains matching and a maximum of eight visible results instead of an oversized full currency popup.
- Currency input is still validated against the existing approved uppercase currency catalog before the template can be saved; provider/task invoice creation and send bindings are unchanged.

### Verification
- Added UI regression contracts for dark scroll backdrops, searchable currency completion, valid-currency enforcement, and compact Invoice Template card sizing.
- Updated README, release notes, version metadata, baseline/update records, and forensic verification documentation.

### Scope protection
- No page, provider, task, account, customer-list, invoice-template field, provider runtime operation, worker-thread behavior, provider manifest, or dependency was removed, renamed, replaced, or expanded.

## 1.0.0.1.3 - 2026-08-07

### Added
- Added the Dashboard page using only live Invio state: provider/account/template/customer counts, task activity, account reservation summary, and context-sensitive next step.
- Added reusable invoice-template fields for invoice title, optional subtitle, invoice type, invoice note, customer note, terms, and per-line tax rate without adding customer, billing, shipping, or payment details to templates.
- Added an uppercase provider-compatible invoice currency catalog and provider-bound currency normalization.
- Added required invoice-template selection to task creation and persisted the template ID/name on each task.
- Added `src/core/provider_runtime/` with built-in Stripe and Refrens REST contracts using the Python standard library.
- Added deterministic Stripe idempotency keys and failed-recipient state used by Retry Failed.

### Changed
- Reworked the Invoice Template dialog into compact, scroll-safe sections with corrected table/header presentation and provider-oriented template fields.
- Compacted Settings text sizing/spacing and added an explicit visual checkmark asset for checked checkboxes.
- Restyled Live Logs and Reports to the approved compact Vib Tools reference layout while preserving their existing Invio actions.
- Reports now identify the invoice template assigned to each task.
- Settings startup-page choices now include Dashboard; the default remains Accounts.

### Provider execution
- Stripe tasks now run real draft-invoice -> line-item -> finalize -> send-invoice operations inside the task-owned worker thread.
- Refrens authentication, payload, create, and documented create-time email delivery are implemented; task execution is intentionally blocked before any create/send call when `billedTo.country` is unavailable from the approved email-only Customer List model. No country is guessed.
- External/custom providers continue to use the existing registered task-runner extension point.

### Verification
- Added provider-runtime execution tests, invoice-template/task binding tests, Dashboard/UI contracts, and Refrens required-data protection tests.
- Updated README, public user/developer/configuration/troubleshooting documentation, release metadata, patch manifest, and private forensic records.

### Scope protection
- No existing feature/page was removed or renamed.
- Existing Step-40J core color and sizing tokens remain frozen.
- No provider manifest/credential schema was changed.
- No customer-list schema, billing/shipping/payment data model, account reservation rule, or per-task QThread model was replaced.
- No new third-party dependency was added.

## 1.0.0.1.2 - 2026-08-07

### Added / Fixed
- Added working provider Uninstall actions while keeping bundled provider packages available for reinstall.
- Made Add Account credentials compact and two-column when a provider declares more than two credential fields.
- Applied compact responsive sizing to application-owned modal and message dialogs.
- Preserved all provider IDs, credential fields, account reservation behavior, page inventory, and worker-thread architecture.

### Verification
- Added provider uninstall and compact-dialog regression contracts and recorded the replace-ready `v1.0.0.1.2` delta.

## 1.0.0.1.1 - 2026-08-07

### Added
- Replaced the informational Settings page with persistent, user-facing application preferences backed by a dedicated non-sensitive settings manager.
- Added startup selection for a fixed page or the last page used.
- Added optional window size/position memory.
- Added individual confirmation controls for exiting with active tasks, closing tasks, deleting invoice templates, deleting customer lists, and clearing Live Logs.
- Added Live Logs preferences for timestamps, automatic scrolling, and an optional maximum retained line count (`0` = unlimited).
- Added file-location preferences for a default file folder and optional last-used-folder memory. These settings are used by provider manifest loading, customer email import, report export, and log export dialogs.
- Added Restore Defaults and Save Changes controls with validation and user-facing save feedback.

### Backend
- Added `src/core/settings/` with validated JSON settings storage, cross-platform per-user configuration paths, atomic writes, corruption-safe fallback to baseline defaults, runtime last-page/folder/window state, and no credential persistence.
- Settings defaults preserve the behavior of the frozen `v1.0.0.1` baseline until the user explicitly changes a preference.
- Settings are applied to the existing application actions without changing provider, account, invoice, customer-list, task, report, or worker architecture.

### Fixed
- Added a guarded viewport-size chip update so restoring a saved window size cannot access the header chip before it exists.
- Added off-screen protection for restored window position by applying saved coordinates only when they are on a currently available screen.

### Verification
- Added settings backend and wiring tests covering defaults, persistence, invalid settings recovery, folder/window opt-in behavior, credential exclusion, UI controls, and runtime action hooks.
- Updated README, configuration, user, architecture, installation, troubleshooting, versioning, release notes, patch manifest, and private forensic/update records for `v1.0.0.1.1`.

### Scope protection
- No existing page was added, removed, renamed, or reordered.
- No provider manifest, provider credential field, provider ID, capability, account mode, install/load contract, or provider execution contract was changed.
- No account, invoice-template, customer-list, task, report, or worker model was removed, renamed, or replaced.
- No provider network adapter, invoice-sending backend, credential persistence, domain-data persistence, or unrelated feature was added.

## 1.0.0.1 - 2026-08-07

### Fixed
- Fixed the Windows sidebar navigation surface so the scroll area, viewport, and navigation host use the official Vib Tools `#090D14` sidebar background instead of the platform default light surface.
- Corrected the repository audit so an existing validated installed-provider registry state is audited rather than incorrectly treated as a failure.

### Updated
- Restyled the Providers page cards to the official Vib Tools Plugin Page visual contract while preserving the existing provider install/load workflow and provider behavior.
- Removed development-stage and UI-only wording from current runtime labels, provider descriptions, dialogs, Reports, Settings, and current source documentation without enabling or simulating unavailable provider operations.
- Removed the `-ui` suffix from the bundled Stripe and Refrens provider package version labels; credential fields, modes, capabilities, and provider IDs are unchanged.
- Marked the desktop shell as the Invio production build `v1.0.0.1`.
- Synchronized public documentation and release metadata with the production UI baseline.

### Scope protection
- No page was added, removed, or renamed.
- No provider credential field, capability, account mode, provider ID, or install/load behavior was changed.
- No task, account, customer-list, invoice-template, report, log, or settings feature was removed or replaced.
- No provider network adapter or invoice-sending backend was added.

## 1.0.0 - 2026-08-07

### Baseline freeze
- Frozen the user-supplied `Invio_v1.0.0.zip` as the immutable source baseline for subsequent delta updates.
- Baseline SHA-256: `50188d56d416ccd359e748e69996fb3a5566dbeefb469d3d7cf7f7f41336636b`.
- The frozen baseline already includes the `ProviderManifestError` export fix, bundled Stripe and Refrens provider manifests, provider visibility rules, account reservation, and per-task worker-thread architecture.

## 0.1.0 - 2026-08-07

### Added
- New Invio desktop project created from the Vib Tools project template.
- Vib Tools Step-40J compliant dark desktop shell and all requested pages.
- Provider manifest install/load flow with installed-provider-only visibility.
- Provider-grouped account UI and dynamic credential fields.
- Invoice-only template editor without customer/billing/shipping fields.
- Named customer lists with bulk email import.
- Multi-account task creation with strict account reservation exclusivity.
- Dedicated `QThread` worker slot architecture per active task.
- Reports, live logs, and settings UI.
- Public user/developer documentation and private `project/` forensic records.

### Deferred
- Provider API networking and real invoice sending.
- Durable account/credential persistence.
- Provider-specific backend adapters and retry/idempotency implementation.
