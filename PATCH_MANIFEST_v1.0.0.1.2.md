# Patch Manifest: Invio v1.0.0.1.2

## Baseline

- Frozen previous release: `v1.0.0.1.1`
- Reconstruction inputs:
  - `Invio_v1.0.0.zip`
  - `Invio_v1.0.0.1_delta_patch.zip`
  - `Invio_v1.0.0.1.1_delta_patch.zip`
- Reconstructed baseline non-cache file count: **155**
- Reconstructed baseline deterministic non-cache tree digest: `6844b7c1f581c9ba6795596af8a2ff2c3eae3264dc61ba0e3351a6a0c035c5f5`

## Approved scope

1. Providers page: installed state exposes a working **Uninstall** action.
2. Accounts → Add Account modal: shorter, wider, spacing corrected, with adaptive two-column credential fields for providers that declare more than two fields.
3. Global application-owned popup/modal presentation: shorter, wider, compact layout.
4. Directly required backend uninstall support, tests, release metadata, forensic verification, and synchronized Markdown documentation.

## Functional patch areas

- `src/core/provider_manager/manager.py`
- `src/ui/pages/providers_page.py`
- `src/ui/dialogs.py`
- `src/ui/main_window.py`
- directly required tests and release/documentation files

No baseline file is deleted by this patch.

## Verification summary

- Final non-cache working-tree file count: **160**
- Baseline files deleted: **0**
- Delta payload files: **30**
- Unit/contract tests: **34/34 PASS**
- Repository audit: **PASS**
- Final forensic report: `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.2.md`
- Delta archive paths are project-root relative; no wrapper directory is permitted.
