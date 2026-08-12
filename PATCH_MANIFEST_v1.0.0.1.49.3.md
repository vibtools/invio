# Invio v1.0.0.1.49.3 Replace-Ready Delta Patch Manifest

## Official frozen parent

The owner-approved **Invio v1.0.0.1.49.2 Provider Easy Onboarding Compatibility Correction** replace-ready state is the exact parent baseline for this update.

## Approved scope

Provider IVX Package System V1 only:

- secure ZIP-based `.ivx` provider import with root-level `provider.json`;
- conditional root `adapter.py` when `runtime_adapter` is declared;
- optional `logo.png`, README/LICENSE/docs and verified optional `SHA256SUMS.txt`;
- safe archive inspection, resource limits, staging, canonical `providers/packages/<provider_id>` storage and rollback-safe replacement;
- plugin-owned logo resolution with `assets/icons/providers/fallback.png` fallback;
- existing trusted executable-provider Install/P13 validation semantics;
- legacy direct `provider.json` loading compatibility;
- deterministic `scripts/provider/build_ivx.py` developer tooling;
- IVX artifacts for the current external provider v1.2.0 set;
- directly required v1.0.0.1.49.3 version, tests and documentation.

## Frozen boundaries

Task state machine, WorkerManager/QThread architecture, immutable task snapshots, retry/resume, delivery ledger, storage/schema/credential behavior, External Provider Adapter V1 execution semantics, Browser OAuth V1, Provider Easy Onboarding V1, provider Task/send/API behavior, customer/template/report/settings behavior, MSI/WiX implementation, dependency stack and unrelated UI remain unchanged except release identity strings directly required by v1.0.0.1.49.3.

## Implementation contract

IVX Load is deliberately non-executing. The archive is inspected and staged without importing `adapter.py`. Imported packages receive an internal `.invio-ivx.json` marker so runtime/preflight code can continue to distinguish host-shipped built-in packages from imported external packages. Executable adapter trust confirmation and existing staged P13 adapter validation occur only at Install.

Provider-card logo resolution is: imported package `logo.png` → existing built-in host logo → owner-supplied `assets/icons/providers/fallback.png`.

## Version mapping

- Application: `1.0.0.1.49.3`
- Tag: `v1.0.0.1.49.3`
- PE: `1.0.1.4903`
- MSI: `1.1.4903`
- Wheel: `1.0.0.1.49.3`
- IVX Format: `1`

## Final verification

- Full repository audit: **529 discovered / 510 PASS / 19 SKIPPED / 0 FAIL / 0 ERROR**.
- Native PySide6 interaction tests are the 19 skips because PySide6 is unavailable in the delivery Linux environment; they remain a Windows/GitHub CI gate.
- Current external provider suites: **42 / 42 PASS**.
- IVX import + trusted Install/runtime discovery: **5 / 5 PASS**.
- Deterministic IVX rebuild: **5 / 5 byte-identical PASS**.
- Wheel build + P14 wheel audit: PASS (**58 source modules / 12 exact runtime resources**).
- Owner `fallback.png` SHA-256: `0428b3bd969699c41c0b103ce29618709ed90696571bc4c52079c55e569826e7`.
- Companion IVX hashes are recorded in `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.49.3.md`.
- Final replace-ready delta inventory/hash/overlay seal is generated after this manifest and the forensic record are synchronized.

## Final delta inventory

- Added: **10**
- Modified: **38** (including the regenerated root `SHA256SUMS.txt`)
- Removed: **0**
- Total replace-ready paths: **48**
- `SHA256SUMS.txt` payload entries: **47**; the checksum file intentionally excludes itself.
- Runtime/build caches (`__pycache__`, `.pyc`, `.pyo`, top-level `build/`, `*.egg-info`) are excluded from the delta.
- Baseline + delta overlay is required to verify **0 missing / 0 extra / 0 byte mismatch** across the logical project file set.
