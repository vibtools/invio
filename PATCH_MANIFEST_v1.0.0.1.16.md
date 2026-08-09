# Invio v1.0.0.1.16 - Replace-Ready Delta Patch Manifest

**Release:** `Invio v1.0.0.1.16`  
**Official parent baseline:** exact uploaded `Invio v1.0.0.1.15.zip` non-cache tree  
**Parent ZIP SHA-256:** `ad24e21a11ca27d905f554f6e3cce583f4d486684cda4b7972efc4779b092e7e`  
**Parent tree SHA-256:** `4950ba3510ecde0cb0d28864d84578a9dfece2cdfa63fd390d1273ff046eb61a`  
**Scope:** P05 forensic verification and consistency correction  
**Production phase count:** 5 / 14

## Functional corrections

- Normal post-P05 Task persistence requires a captured immutable snapshot; `LegacyUnavailable` stays migration-only.
- Captured Task processed/success/failed counters must agree with the immutable recipient snapshot at runtime, persistence and startup load boundaries.
- Routine Task status/progress persistence no longer rewrites immutable snapshot-derived `Task.total`.

## Runtime/source files changed

- `src/core/state/app_state.py`
- `src/core/storage/domain_store.py`
- `src/core/provider_runtime/runtime.py` - release User-Agent marker only
- `src/ui/main_window.py` - release marker only

## Tests changed

- `tests/test_state.py`
- `tests/test_storage.py`
- `tests/test_repository_contracts.py`

## Explicitly unchanged

SQLite remains schema v4. Snapshot models/tables and migration policy, Task UI behavior, WorkerManager, ProviderManager, CredentialStore, provider manifests, Stripe/Refrens execution semantics, dependencies and P06-P14 remain unchanged.

## Delivery

The ZIP is a project-root overlay with no wrapper folder and no generated Python/test caches. Final ZIP SHA-256 is distributed in the adjacent `.sha256` sidecar to avoid self-referential archive hashing.

## Verification gate

- exact parent baseline: **162/162 tests PASS**;
- final corrected tree: **169/169 tests PASS**;
- compile/repository/privacy/provider-visibility/metadata audits: PASS;
- parent non-cache deletions: 0;
- pre-existing Python top-level symbol removals/renames: 0;
- protected out-of-scope hash comparison: PASS;
- replace-ready delta file count: **38**;
- schema: v4 unchanged;
- dependency/provider-manifest changes: 0.
