# Invio v1.0.0.1.40.2 Production CI Checksum Portability Fix

This replace-ready overlay is strictly limited to the Odoo external-provider bundle checksum portability failure observed in GitHub Actions run `31432485639`. Application version remains `1.0.0.1.40.2`.

## Functional correction

- `.gitattributes` now applies `providers/plugins/odoo/** text eol=lf`.
- This prevents Windows checkout CRLF conversion from invalidating the Odoo bundle's raw-byte `SHA256SUMS.txt`.

## Scope boundary

No provider implementation, runtime code, UI, database, WorkerManager, workflow, test, dependency, API contract, filename, module, or version mapping is changed.

## Delta inventory

Added:
- `PATCH_MANIFEST_v1.0.0.1.40.2_PRODUCTION_CI_FIX.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.40.2_PRODUCTION_CI.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.40.2_PRODUCTION_CI.md`

Modified:
- `.gitattributes`
- `CHANGELOG.md`
- `README.md`
- `docs/release-notes/1.0.0.1.40.2.md`
- `SHA256SUMS.txt`

Removed: none.
