# Invio v1.0.0.1.10 Replace-Ready Delta Patch Manifest

**Parent Official Baseline:** `Invio_v1.0.0.1.9.zip`  
**Parent SHA-256:** `ab7c324b9d4970686fb47fd0d1d2f98bf9ad9c066baceca9af115697481b20f2`  
**Target release:** `Invio v1.0.0.1.10`  
**Phase:** P03 - Account Lifecycle, Verification Health and Provider-Install Consistency

## Apply

Extract the delta ZIP directly over the `v1.0.0.1.9` project root and replace matching files. The ZIP has no wrapper directory.

## Runtime/source delta

- `src/accounts/models/account.py`
- `src/core/state/app_state.py`
- `src/core/storage/schema.py`
- `src/core/storage/domain_store.py`
- `src/ui/dialogs.py`
- `src/ui/pages/accounts_page.py`
- `src/ui/main_window.py`
- `src/core/provider_runtime/runtime.py` - release User-Agent marker only
- `pyproject.toml` - release version only; dependency set unchanged
- `vibproject.ygit` - release version only; dependency set unchanged

## Test delta

- `tests/test_state.py`
- `tests/test_storage.py`
- `tests/test_ui_contracts.py`
- `tests/test_repository_contracts.py`

## Documentation/release delta

The patch contains only P03-required release/documentation synchronization, including:

- `README.md`
- `CHANGELOG.md`
- `ROADMAP.md`
- `VERSIONING.md`
- `COMPATIBILITY.md`
- `PROJECT_STRUCTURE.md`
- `.github/SECURITY.md`
- current user/developer/provider/task/configuration documentation
- `docs/release-notes/1.0.0.1.10.md`
- private `project/` P03 architecture/roadmap/phase/research/baseline records

## Frozen/unchanged by P03

No change to:

- ProviderManager architecture
- WorkerManager architecture
- protected CredentialStore implementation/technology
- packaged Stripe/Refrens provider manifests
- Customer List model/import contract
- Invoice Template model
- Task model
- shared UI style/token/widget system
- `requirements.txt`

No P04+ feature is included.

## Verification

- 105/105 unit/contract tests PASS.
- repository audit PASS.
- Python compileall PASS.
- JSON/YGIT/TOML validation PASS.
- zero removed/renamed pre-existing top-level Python classes/functions.
- zero parent-baseline non-cache file deletions in the release delta.
- 42 replace/add files in the project-root delta.
- fresh parent baseline + delta overlay matches the verified release tree byte-for-byte after excluding generated cache artifacts.
- fresh overlaid project: 105/105 tests PASS and repository audit PASS.
- native PySide6/keyring/live-provider certification is not claimed in the audit container and remains P14.

The final ZIP SHA-256 is provided in the companion `Invio_v1.0.0.1.10_delta_patch.zip.sha256` artifact.
