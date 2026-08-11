# Invio v1.0.0.1.48.7 Replace-Ready Delta Patch Manifest

## Parent Official Baseline

`Invio_v1.0.0.1.48.6_Baseline.zip`

SHA-256: `c51c92b5e9e5f376e4fe03980b90c557c1487d276f2573c8de3b470abf735e22`

## Locked correction

Global Status Badge Rendering & Table Cell Alignment Fix only. The shared UI layer now owns semantic status mapping, display markers, badge refresh, and table-cell composition. A status cell that uses a badge keeps the raw domain value only as metadata/tooltip and renders no second visible raw-text source.

## Canonical status presentation

- Success: existing Vib Tools success token `#22C55E`.
- Warning: approved `#FCD34D`.
- Danger: approved `#F87171`.
- Neutral: existing neutral border/text tokens.
- Primary/focus: existing `#2563EB`.

## Verified consumers

- Accounts status table cells.
- New Task account-selection status cells.
- Reports task status cells.
- Reports recipient/delivery status cells.
- Task card status badge refresh.
- Provider card status badge mapping.
- Shared reusable status helpers in `src/ui/widgets.py`.

Customer Lists, Live Logs and Settings contain no domain-status badge/table consumer requiring conversion in this baseline. Existing shared inline feedback/status-message controls in dialogs remain unchanged because they are transient feedback messages, not duplicate table/domain status values.

## Verification

- Parent baseline audit: **462 total / 451 PASS / 11 SKIPPED / 0 failures**.
- Targeted final UI/repository/distribution suite: **179 total / 167 PASS / 12 SKIPPED / 0 failures**.
- Final full local audit: **468 total / 456 PASS / 12 SKIPPED / 0 failures**.
- Syntax / repository privacy / provider visibility: **PASS**.
- Native PySide6 in this forensic container: **unavailable; no false runtime PASS claimed**.
- Owner-supplied parent v1.48.6 Windows runtime evidence: existing Accounts action-menu runtime test and complete v1.48.6 audit PASS.
- Owner-supplied first v1.48.7 Windows verification: New Task canonical-status runtime test PASS; Accounts status-layout runtime test exposed one sizing-contract failure (`132px` Status column vs `184px` aggregate host size hint).
- Corrected renderer/test contract: table item sizing and runtime clipping checks now use the visible badge size, not the host-with-centering-stretches size hint. Local post-correction audit: **468 total / 456 PASS / 12 PySide6-gated SKIPPED / 0 failures**.
- Corrected native Windows Accounts status runtime re-verification remains required before release certification.

## Version mapping

- Application: `1.0.0.1.48.7`
- Tag: `v1.0.0.1.48.7`
- PE: `1.0.1.4807`
- MSI: `1.1.4807`
- Wheel: `1.0.0.1.48.7`

## Added

- `PATCH_MANIFEST_v1.0.0.1.48.7.md`
- `docs/release-notes/1.0.0.1.48.7.md`
- `project/research/FINAL_FORENSIC_VERIFICATION_v1.0.0.1.48.7.md`
- `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.7.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.48.7.md`

## Modified

- `.github/workflows/ci.yml`
- `CHANGELOG.md`
- `COMPATIBILITY.md`
- `PROJECT_STRUCTURE.md`
- `README.md`
- `ROADMAP.md`
- `SHA256SUMS.txt`
- `VERSIONING.md`
- `docs/configuration/index.md`
- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `docs/developer/architecture.md`
- `docs/docs.manifest.ygit`
- `docs/features/ui-milestone.md`
- `docs/getting-started/installation.md`
- `docs/guides/accounts.md`
- `docs/index.md`
- `docs/troubleshooting/index.md`
- `docs/user/usage.md`
- `examples/accounts_flat_table_ui.md`
- `project/README.md`
- `project/architecture/ARCHITECTURE.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `pyproject.toml`
- `src/core/provider_runtime/runtime.py`
- `src/ui/dialogs.py`
- `src/ui/main_window.py`
- `src/ui/pages/accounts_page.py`
- `src/ui/pages/providers_page.py`
- `src/ui/pages/reports_page.py`
- `src/ui/pages/tasks_page.py`
- `src/ui/styles.py`
- `src/ui/widgets.py`
- `tests/test_p14_distribution_pipeline.py`
- `tests/test_repository_contracts.py`
- `tests/test_ui_contracts.py`
- `tests/test_ui_runtime_interactions.py`
- `vibproject.ygit`

## Removed

None.

## Delta policy

No wrapper directory. Only changed/new files are packaged. `__pycache__`, `.pyc`, `.pytest_cache` and unrelated baseline files are excluded. `SHA256SUMS.txt` hashes every other delta payload path and excludes itself.
