# Invio v1.0.0.1.49.4 Replace-Ready Delta Patch Manifest

## Official frozen parent

`Invio v1.0.0.1.49.3 Provider IVX Package System V1` replace-ready state. Parent delta SHA-256: `416a03130f89dfff27204dbc22b32aaabdb05be24fef0fb53b3196ba163d26e7`.

## Scope lock

Provider IVX Package System V1 verification/correction only:

- native Windows raw ZIP-name validation;
- canonical/portable IVX archive-path security;
- Provider-page optional plugin-logo resolver compatibility;
- unsupported compression exception containment;
- structural/dimension-safe optional PNG validation;
- deterministic IVX builder publish-after-validation atomicity;
- directly required regression tests, v1.49.4 identity, release/docs/forensic records.

## Explicitly frozen

Task state machine, WorkerManager, immutable Task snapshots, retry/resume, delivery ledger, SQLite/storage/credentials, External Provider Adapter V1, Browser OAuth V1, Provider Easy Onboarding V1, provider send/API semantics, customer/template/report/settings behavior, MSI/WiX, signing and unrelated UI.

## Verified root causes

- `ZipInfo.filename` / test-fixture normalization hid an intended raw-backslash rejection boundary on native Windows; v1.49.4 validates `orig_filename` and writes exact raw test names.
- ProvidersPage made the new package-logo resolver mandatory; v1.49.4 treats it as an optional additive manager capability.
- Raw path aliases and Windows-special path components were insufficiently rejected before canonicalization.
- Unsupported compression could escape as raw `NotImplementedError`.
- Optional PNG safety validation was signature-only.
- IVX builder final publication occurred before final archive validation.

## Verification

- Owner native Windows v1.49.3 evidence: `529` tests, `1 FAIL`, `1 ERROR`; both are the initiating defects for this correction.
- Targeted corrected IVX suite: `23/23 PASS`.
- Final repository audit: `532 discovered / 513 PASS / 19 SKIPPED / 0 FAIL / 0 ERROR`.
- Syntax / repository privacy / provider visibility: `PASS`.
- External provider companion suites: `42/42 PASS`.
- Rebuilt current provider IVX artifacts: `5/5` byte-identical to v1.49.3 v1.2.0 artifacts.
- Wheel build: `PASS`; P14 wheel audit: `58 source modules / 12 exact runtime resources`.
- Frozen critical architecture byte-identity: `PASS`; runtime/main-window changes are version-identity-only.
- Production fake/demo/TODO marker scan in the corrected IVX/provider-adapter scope: `PASS`.

`19` PySide6 runtime tests are skipped only because PySide6 is unavailable in the Linux delivery container; they are not claimed as PASS. Native Windows v1.49.4 and non-tag GitHub CI remain release gates.

## Target identity

- Application: `1.0.0.1.49.4`
- Tag: `v1.0.0.1.49.4`
- PE: `1.0.1.4904`
- MSI: `1.1.4904`
- Wheel: `1.0.0.1.49.4`
- IVX Format: `1`

## Delta inventory

- Added: `6`
- Modified: `35`
- Removed: `0`
- Total replace-ready paths: `41`

### Added

- `PATCH_MANIFEST_v1.0.0.1.49.4.md`
- `docs/release-notes/1.0.0.1.49.4.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.4.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.49.4.md`
- `project/research/UPDATE_IMPLEMENTATION_VERIFICATION_v1.0.0.1.49.4.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.49.4.md`

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
- `docs/guides/providers.md`
- `docs/index.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `examples/provider_ivx_layout.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `pyproject.toml`
- `scripts/provider/build_ivx.py`
- `src/core/provider_manager/ivx.py`
- `src/core/provider_runtime/runtime.py`
- `src/ui/main_window.py`
- `src/ui/pages/providers_page.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_provider_ivx.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `vibproject.ygit`

## Seal contract

`SHA256SUMS.txt` contains hashes for every delta payload file except itself (`40/40`). The final ZIP must use direct project-root paths, contain no wrapper folder, no `.pyc`/`__pycache__`, and reconstruct the v1.49.4 candidate from the frozen v1.49.3 parent with `0` missing, `0` extra and `0` byte mismatch.
