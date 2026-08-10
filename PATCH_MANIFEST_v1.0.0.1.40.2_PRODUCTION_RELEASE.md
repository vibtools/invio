# Invio v1.0.0.1.40.2 Production Release Finalization Patch Manifest

This overlay keeps application version `1.0.0.1.40.2` unchanged and finalizes the owner-accepted first production release. It adds the live-tested Odoo Provider v1.0.0 as a distributable P13 external plugin and synchronizes production-release documentation/packaging contracts. No core provider runtime, database schema, WorkerManager, Task state machine, UI/UX, or dependency behavior is changed by this finalization.

## Inventory

- Added: **15**
- Modified: **27**
- Removed: **0**
- Total overlay paths: **42**

### Added

- `PATCH_MANIFEST_v1.0.0.1.40.2_PRODUCTION_RELEASE.md`
- `examples/odoo_provider_canary.md`
- `project/research/FINAL_PRODUCTION_RELEASE_VERIFICATION_v1.0.0.1.40.2.md`
- `project/research/ODOO_LIVE_ACCEPTANCE_v1.0.0.1.40.2.md`
- `project/research/PRODUCTION_RELEASE_ACCEPTANCE_v1.0.0.1.40.2.md`
- `project/specifications/P14_CERTIFICATION_COMPLETE_v1.0.0.1.40.2.md`
- `providers/plugins/odoo/CHANGELOG.md`
- `providers/plugins/odoo/LICENSE`
- `providers/plugins/odoo/README.md`
- `providers/plugins/odoo/SHA256SUMS.txt`
- `providers/plugins/odoo/adapter.py`
- `providers/plugins/odoo/docs/FORENSIC_AUDIT.md`
- `providers/plugins/odoo/docs/LIVE_TEST_CHECKLIST.md`
- `providers/plugins/odoo/provider.json`
- `tests/test_odoo_provider_bundle.py`

### Modified

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
- `docs/developer/architecture.md`
- `docs/getting-started/installation.md`
- `docs/guides/providers.md`
- `docs/index.md`
- `docs/release-notes/1.0.0.1.40.2.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.40.2.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.40.2.md`
- `project/specifications/P14_CERTIFICATION_PENDING_v1.0.0.1.40.2.md`
- `pyproject.toml`
- `scripts/test/p14_wheel_audit.py`

### Removed

- None

## Odoo distribution contract

- Source bundle: `providers/plugins/odoo/`
- P13 external adapter interface: v1
- Installation remains explicit trusted-code `Load Provider`; Odoo is not converted into a packaged/auto-installed provider.
- Wheel inclusion is enforced by `scripts/test/p14_wheel_audit.py`.
- Nuitka/portable/MSI inclusion uses the existing `providers=providers` data-directory distribution rule.

## Production acceptance boundary

- Owner-confirmed real Odoo invoice sending: PASS.
- P14: COMPLETE by explicit owner production acceptance.
- P11 Refrens: IMPLEMENTED / LIVE ACCEPTANCE DEFERRED and non-blocking for this release.
- Refrens API email is not certified; observed provider response remains `HTTP 400: Not allowed to send mail`.
- Agiled remains API-Test-only/fail-closed for Task sending.
