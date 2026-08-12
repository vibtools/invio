# Invio v1.0.0.1.49.2 Replace-Ready Delta Patch Manifest

## Official current baseline

The exact frozen parent is the owner-approved **`v1.0.0.1.49.1 Provider Easy Onboarding V1`** replace-ready delta state, reconstructed from `Invio_v1.0.0.1.49.1_Provider_Easy_Onboarding_V1_delta_patch.zip` on top of its frozen `39574bc70aaf8ea8254a830a244a1a5c52252f8a` source candidate.

## Root-cause scope lock

The verified defect family is limited to Add Account compatibility selection: the optional Provider Easy Onboarding V1 host capability was called as if every Browser-OAuth-compatible runtime collaborator implemented `supports_onboarding`. Native Windows regression testing proved that a legacy/Browser-OAuth-only runtime without that method raises `AttributeError` during dialog construction. Forensic continuation of that unchanged native test also showed that, after removing the exception, the legacy Browser OAuth-only path must retain its established `Connect once in your browser...` status copy instead of inheriting Quick Connect copy.

The correction is scope-locked to making the new onboarding capability genuinely additive/optional, synchronizing version identity/tests/documentation, and packaging the exact corrected delta. No unrelated behavior is authorized.

## Exact implementation

- Guard `supports_onboarding` through optional `getattr` + callable detection.
- Guard `onboarding_profile` through optional `getattr` + callable detection.
- Missing onboarding capability returns unsupported instead of raising.
- Keep the existing real `ProviderRuntime` onboarding path unchanged when supported.
- Preserve Browser OAuth-only runtime compatibility, including its established connection/status copy when onboarding is unavailable.
- Preserve the existing Advanced / Manual Setup fallback and existing Accounts.

## Explicitly unchanged

No provider Task/send semantics, provider execution interface, browser OAuth protocol, provider-plugin send implementation, Task/WorkerManager architecture, storage/schema, delivery ledger, retry/resume, customer/template/report business behavior, provider install/uninstall architecture, MSI/WiX implementation, dependency stack, or unrelated UI behavior is changed.

The Easy Onboarding provider pack remains v1.2.0; no companion provider source correction is included in this application delta.

## Version mapping

- Application: `1.0.0.1.49.2`
- Tag: `v1.0.0.1.49.2`
- PE: `1.0.1.4902`
- MSI: `1.1.4902`
- Wheel: `1.0.0.1.49.2`

## Verification

- Owner-supplied native Windows baseline audit: **504 tests / 1 ERROR**, with the sole error at the Add Account optional-onboarding capability boundary.
- Targeted correction cycle 1 exposed no additional product failure; two verification assertions required synchronization with the exact compatibility correction.
- Targeted correction cycle 2: Provider Easy Onboarding **9/9 PASS**, v1.49.2 release contract **1/1 PASS**, Browser OAuth **9/9 PASS**.
- P14 distribution/version suite: **10/10 PASS**.
- UI source/contract suite: **91/91 PASS**.
- Final local repository audit: **506 discovered / 487 PASS / 19 SKIPPED / 0 FAIL / 0 ERROR**.
- The 19 local skips are the existing native PySide6 runtime-interaction tests because PySide6 is unavailable in the delivery container; they are not represented as PASS.
- The exact owner-failing native regression test file remains byte-identical to the frozen baseline so the subsequent GitHub Windows CI run tests the real pre-existing contract rather than a weakened replacement.
- Companion provider v1.2.0 deterministic suites: **42/42 PASS** (Zoho Books 8, Zoho Invoice 8, Xero 7, QuickBooks Online 9, Square 10).
- Syntax audit: PASS.
- Repository privacy contract: PASS.
- Provider visibility contract: PASS.
- Version mapping helper: PASS (`1.0.0.1.49.2` -> PE `1.0.1.4902`, MSI `1.1.4902`).
- Protected-scope comparison: WorkerManager, Task state machine, storage/schema/credential store, provider manager, External Adapter v1, Browser OAuth v1, Reports/Customers/Templates pages and WiX generator are byte-identical to the frozen parent.
- Production runtime scan found no fake/mock/demo provider execution endpoint; only historical documentation wording and non-executable UI placeholder examples were present.
- Removed frozen-baseline files: **0**.

## Delta policy

The replace-ready ZIP is rooted at the project root with no wrapper folder. It contains only files added or changed from the frozen v1.49.1 Easy Onboarding baseline. Runtime/build caches are excluded. `SHA256SUMS.txt` hashes every other delta payload path and excludes itself.

## Final delta inventory

### Added

- `PATCH_MANIFEST_v1.0.0.1.49.2.md`
- `docs/release-notes/1.0.0.1.49.2.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.2.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.2.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.49.2.md`

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
- `src/core/provider_runtime/runtime.py`
- `src/ui/dialogs.py`
- `src/ui/main_window.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_provider_onboarding.py`
- `tests/test_repository_contracts.py`
- `vibproject.ygit`

### Removed

None.

### Counts

- Added: 5
- Modified: 32 (including regenerated `SHA256SUMS.txt`)
- Removed: 0
- Total delta paths: 37
- `SHA256SUMS.txt` payload entries: 36

