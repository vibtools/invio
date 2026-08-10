# Invio v1.0.0.1.39 Compiled Protected-Credential Storage Correction Delta Patch Manifest

Parent Official released baseline: `Invio v1.0.0.1.38`  
Target: `Invio v1.0.0.1.39` local/source/build correction candidate  
Release status: **NOT TAGGED / NOT RELEASED**

## Scope

Correct only the owner-observed released-app failure where Refrens API Test succeeds but `Add Account` fails with `Protected credential storage is unavailable.`. The exact failing boundary is the compiled production `CredentialStore` keyring import/dependency path.

Correction:

- explicit Nuitka inclusion of the existing keyring runtime dependency graph;
- build-only preservation of `keyring` distribution metadata;
- compiled OneDir and MSI-installed production CredentialStore set/get/delete smoke;
- CI-only smoke entry hook;
- v1.39 release identity, focused regression coverage and synchronized documentation.

No plaintext fallback, dependency replacement, provider API/send change, schema migration, WorkerManager/Task change, UI/UX change, provider manifest change or release-topology redesign is included.

## Verification

- v1.38 unchanged baseline audit already recorded: **385/385 PASS**; not rerun unnecessarily.
- v1.39 targeted P14/repository verification: **60/60 PASS on cycle 1**.
- additional targeted fix/retry cycles: **0**.
- v1.39 final `python scripts/test/audit.py`: **388/388 PASS**.
- syntax audit: **PASS**.
- repository privacy: **PASS**.
- provider visibility: **PASS**.
- removed/renamed parent files: **0**.
- protected storage/provider/schema/thread/runtime dependency contracts: verified unchanged except the approved build/test boundary and release markers.

## Delta inventory

Added files: **8**

1. `.github/nuitka-keyring.nuitka-package.config.yml`
2. `PATCH_MANIFEST_v1.0.0.1.39.md`
3. `docs/release-notes/1.0.0.1.39.md`
4. `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.39.md`
5. `project/research/P14_COMPILED_CREDENTIAL_STORAGE_CORRECTION_v1.0.0.1.39.md`
6. `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.39.md`
7. `project/specifications/BASELINE_FREEZE_v1.0.0.1.39.md`
8. `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.39.md`

Modified files: **27**

1. `.github/workflows/ci.yml`
2. `CHANGELOG.md`
3. `COMPATIBILITY.md`
4. `PROJECT_STRUCTURE.md`
5. `README.md`
6. `ROADMAP.md`
7. `SHA256SUMS.txt`
8. `VERSIONING.md`
9. `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
10. `docs/developer/architecture.md`
11. `docs/docs.manifest.ygit`
12. `docs/getting-started/installation.md`
13. `docs/index.md`
14. `docs/troubleshooting/index.md`
15. `docs/user/usage.md`
16. `project/README.md`
17. `project/architecture/ARCHITECTURE.md`
18. `project/planning/PHASE_COMPLETION_LOG.md`
19. `project/planning/PRODUCTION_ROADMAP.md`
20. `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
21. `pyproject.toml`
22. `src/app.py`
23. `src/core/provider_runtime/runtime.py`
24. `src/ui/main_window.py`
25. `tests/test_p14_distribution_pipeline.py`
26. `tests/test_repository_contracts.py`
27. `vibproject.ygit`

Removed/renamed files: **0**

Total delta paths: **35**.

`SHA256SUMS.txt` records the other 34 delta paths and intentionally excludes itself.
