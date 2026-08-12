# Invio v1.0.0.1.49.1 Replace-Ready Delta Patch Manifest

## Official parent baseline

`Invio v1.0.0.1.49` is the frozen parent. The implementation must be applied to the exact v1.49 project root, not to an older delta state.

## Approved scope lock

Only these two implementation scopes are included:

1. **Windows MSI functional/distribution correction** — preserve the existing per-user LocalAppData installation architecture and UpgradeCode, add a discoverable uninstall-safe Start Menu launch entry, and extend the existing Windows CI lifecycle checks to verify that shortcut target and removal.
2. **Host-managed Browser OAuth authorization system** — additive browser authorization/bootstrap for external provider plugins, persistent refresh/bootstrap credentials through Invio's existing OS-protected credential store, automatic future access-token renewal, provider-account discovery, and safe reconnect behavior without replacing External Provider Adapter interface v1.

No Task state-machine, WorkerManager, delivery-ledger, retry/resume, invoice generation/send semantics, database/schema, customer/template/report behavior, provider installation workflow, dependency stack, or unrelated UI redesign is included.

## MSI correction

- Existing `%LOCALAPPDATA%\Vib Tools\Invio` per-user install target remains authoritative.
- Existing WiX `UpgradeCode` remains unchanged.
- Adds Start Menu `Vib Tools -> Invio` shortcut targeting installed `Invio.exe` with `INSTALLFOLDER` working directory.
- Shortcut has uninstall-safe component/key-path handling and is removed during uninstall.
- Windows CI now verifies shortcut existence, exact target and post-uninstall removal in addition to the existing installed-executable/keyring/startup lifecycle smoke.
- **Signing Option C is frozen:** no Authenticode signing service/certificate is introduced. Therefore the Windows `Unknown Publisher` warning remains expected for this unsigned release candidate; this is not represented as fixed.

## Browser OAuth correction

- Adds optional `browser_auth` manifest declaration v1; existing manifests remain compatible.
- Existing External Provider Adapter interface v1 (`test_account`, `validate_task`, `execute_recipient`) remains unchanged.
- Adds a separate Browser OAuth v1 contract for authorization URL construction and callback/token/account-discovery completion.
- Uses the system browser; no embedded browser/WebView dependency is introduced.
- Uses cryptographic OAuth `state`; PKCE S256 is supported/required by provider profile where appropriate.
- Loopback receiver is single-session, timeout/cancel capable, path-bound and fail-closed.
- Non-loopback redirects require HTTPS; registered redirect fragments and fixed query strings are rejected.
- Access tokens are not intentionally persisted as account credentials.
- Refresh/bootstrap credentials and provider account identifiers are persisted through the existing OS-protected `CredentialStore`; no plaintext/SQLite token storage is added.
- Existing manual refresh-token configuration remains supported.
- Provider revocation, provider-defined refresh-token expiry/inactivity, OAuth-app deletion/change, consent/security changes, or removed user authorization can require reconnecting; "connect once" means no repeated login/token copy-paste while the provider grant remains refreshable.

## Provider plugin compatibility

The companion v1.1.0 provider bundles retain their existing production invoice/send adapter semantics and add only Browser OAuth bootstrap support:

- Zoho Books
- Zoho Invoice
- Xero
- QuickBooks Online
- Square

Final deterministic provider tests: **37 / 37 PASS**. Final packaged-bundle validation against Invio v1.49.1 host contracts: **5 / 5 PASS**.

## Version mapping

- Application: `1.0.0.1.49.1`
- Tag identity: `v1.0.0.1.49.1` (no tag is created by this delta)
- PE: `1.0.1.4901`
- MSI: `1.1.4901`
- Wheel: `1.0.0.1.49.1`

## Verification

- Final application audit: **496 discovered / 477 PASS / 19 SKIPPED / 0 FAIL / 0 ERROR**.
- All 19 local skips are real PySide6 runtime tests gated only because PySide6 is not installed in the delivery container.
- Syntax audit: PASS.
- Repository privacy contract: PASS.
- Provider visibility contract: PASS.
- Wheel content audit: PASS — **57 source modules / 11 exact runtime resources**.
- Companion provider deterministic tests: **37 / 37 PASS**.
- Final provider ZIP host validation: **5 / 5 PASS**.
- Native Windows MSI shortcut/install/uninstall and native PySide6 interaction execution remain the required non-tag GitHub Windows CI certification gate; they are not fabricated as locally executed results.

## Same-version CI correction after first push

- Frozen GitHub baseline for this correction: commit `2bbd7635f77ed4bc2a0f7f4d36bc84c9b3b05b88` on `main`.
- GitHub Actions run `31602199589` failed in both `test` and `windows-build` at the same repository-contract test before build/package stages.
- Confirmed root cause: `V1491PersistentBrowserOAuthMsiReleaseContractTests` unconditionally opened two `/project/` forensic files even though `/project/` is deliberately Git-ignored/private. Local owner audit passed only because those private files existed locally; clean CI checkout correctly omitted them.
- Correction is limited to the repository truthfulness contract: tracked v1.49.1 release note/manifest evidence is authoritative in public checkout, while private `/project/` evidence is validated only when that private workspace exists.
- Version identity remains `1.0.0.1.49.1`; no app/runtime/OAuth/MSI/provider/UI/storage/business implementation is changed.

## Delta policy

The final ZIP has no wrapper folder and contains only changed/new project-root files. Runtime/build caches are excluded. `SHA256SUMS.txt` hashes every other delta payload path and excludes itself.

## Final delta inventory

### Added
- `PATCH_MANIFEST_v1.0.0.1.49.1.md`
- `docs/release-notes/1.0.0.1.49.1.md`
- `examples/browser_oauth_provider.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.1.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.1.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.49.1.md`
- `src/core/provider_runtime/oauth.py`
- `tests/test_browser_oauth.py`

### Modified
- `.github/workflows/ci.yml`
- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `SHA256SUMS.txt`
- `VERSIONING.md`
- `docs/api/provider-manifest.md`
- `docs/configuration/index.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/getting-started/installation.md`
- `docs/guides/accounts.md`
- `docs/guides/providers.md`
- `docs/index.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `pyproject.toml`
- `scripts/build/generate_wix_source.py`
- `src/core/provider_manager/__init__.py`
- `src/core/provider_manager/manager.py`
- `src/core/provider_runtime/__init__.py`
- `src/core/provider_runtime/external.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/dialogs.py`
- `src/ui/main_window.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `tests/test_ui_runtime_interactions.py`
- `vibproject.ygit`

### Removed

None.

### Counts

- Added: 8
- Modified: 38 (including regenerated `SHA256SUMS.txt`)
- Removed: 0
- Total delta paths: 46
- `SHA256SUMS.txt` payload entries: 45

## CI correction delta inventory

This same-version correction is applied on top of the frozen `2bbd7635f77ed4bc2a0f7f4d36bc84c9b3b05b88` v1.49.1 candidate. It does not repeat the original v1.49.1 feature payload.

### Public tracked correction files
- `tests/test_repository_contracts.py`
- `CHANGELOG.md`
- `docs/release-notes/1.0.0.1.49.1.md`
- `PATCH_MANIFEST_v1.0.0.1.49.1.md`
- `SHA256SUMS.txt`

### Private forensic records carried in the replace-ready delta but intentionally remaining Git-ignored
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.49.1.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.1.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.1.md`

No runtime/source implementation file, workflow file, version marker, dependency file or provider bundle is modified by this CI correction.

## Provider Easy Onboarding V1 continuation on frozen candidate `39574bc`

This continuation is applied on top of commit `39574bc70aaf8ea8254a830a244a1a5c52252f8a` and keeps application version `1.0.0.1.49.1`. Scope is limited to generic provider account onboarding plus required documentation/tests. MSI/WiX/CI installer behavior is not changed.

Host changes: provider credential ownership/friendly choices, optional `onboarding` declaration v1, constrained onboarding request/result contract, Quick Connect hidden-managed-field UI, Advanced / Manual Setup fallback, Browser OAuth → preparation → automatic API Test chaining, existing account compatibility and future-provider generic extensibility. Companion v1.2.0 bundles for Zoho Books, Zoho Invoice, Xero, QuickBooks Online and Square implement the same contract without changing their Task send interfaces.

## Provider Easy Onboarding V1 exact continuation delta inventory

Frozen input: `39574bc70aaf8ea8254a830a244a1a5c52252f8a` (`v1.0.0.1.49.1` candidate). This inventory is only the Easy Onboarding continuation; it does not repeat earlier v1.49.1 payloads.

### Added

- `examples/easy_onboarding_provider.md`
- `project/research/PROVIDER_EASY_ONBOARDING_V1_IMPLEMENTATION_v1.0.0.1.49.1.md`
- `project/specifications/PROVIDER_EASY_ONBOARDING_V1_SCOPE_LOCK_v1.0.0.1.49.1.md`
- `tests/test_provider_onboarding.py`

### Modified

- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PATCH_MANIFEST_v1.0.0.1.49.1.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `VERSIONING.md`
- `docs/api/provider-manifest.md`
- `docs/configuration/index.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/getting-started/installation.md`
- `docs/guides/accounts.md`
- `docs/guides/providers.md`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.49.1.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.1.md`
- `src/core/provider_manager/__init__.py`
- `src/core/provider_manager/manager.py`
- `src/core/provider_runtime/__init__.py`
- `src/core/provider_runtime/external.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/dialogs.py`

### Removed

None.

### Counts

- Added: 4
- Modified before regenerated checksum inventory: 27
- Removed: 0
- Regenerated `SHA256SUMS.txt`: 1 additional modified path
- Final delta paths: 32
- `SHA256SUMS.txt` payload entries: 31
