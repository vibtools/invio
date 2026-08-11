# Invio v1.0.0.1.48.02 Replace-Ready Delta Patch Manifest

## Parent baseline
`Invio v1.0.0.1.48.01`

## Target
`Invio v1.0.0.1.48.02`

## Locked implementation scope
- Global app-owned `QMessageBox` / popup lifecycle functional-regression repair.
- Real PySide6 popup interaction regression tests.
- Separately approved P14 wheel packaging compatibility correction for Python's canonical `1.0.0.1.48.2` wheel identity while preserving public `1.0.0.1.48.02` / `v1.0.0.1.48.02` and PE/MSI mappings.
- Required direct version/tests/documentation synchronization only.

## Product implementation paths
- `src/ui/dialogs.py` — all Invio-owned compact message boxes use the widget-backed Qt path before custom chrome; caller-captured message-box layout is no longer passed into chrome installation.
- `src/ui/title_bars.py` — complex dialog chrome reacquires the live dialog-owned layout only after frameless/translucent window mutation.

## Real runtime regression path
- `tests/test_ui_runtime_interactions.py` — actual `QApplication` / `QMessageBox.exec()` / `QTimer` button-click lifecycle tests; explicitly skips only when PySide6 is absent.

## P14 packaging compatibility paths
- `scripts/test/p14_wheel_audit.py` — validates canonical Python wheel metadata identity derived from the public numeric application version.
- `scripts/test/p14_distribution_audit.py` — portable/MSI retain public-version filenames; wheel release inventory uses the canonical Python wheel version.
- `tests/test_p14_distribution_pipeline.py` and directly related repository truthfulness tests/docs synchronize that contract.

## Frozen backend/runtime paths
Task state machine, AppState, WorkerManager, DomainStore/schema, delivery ledger, provider adapters/runtime, customer/invoice/settings logic and runtime dependencies are unchanged by this patch.

## Verification
- Approved packaging correction targeted gate: **11/11 PASS**.
- Real wheel build: `invio-1.0.0.1.48.2-py3-none-any.whl`.
- P14 real wheel content audit: **PASS**.
- Final repository audit: **442 discovered / 438 PASS / 4 SKIPPED**; four skips are only the real PySide6 interaction tests because PySide6 is unavailable in this local forensic container.
- Syntax/privacy/provider-visibility gates: **PASS**.

## Final delta inventory
- Added: **7**
- Modified: **28**
- Removed: **0**
- Total paths: **35**
- `SHA256SUMS.txt`: **34** payload hashes (every delta payload path except the checksum manifest itself).

No baseline file is intentionally removed.
