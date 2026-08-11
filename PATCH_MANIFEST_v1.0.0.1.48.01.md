# Invio v1.0.0.1.48.01 Replace-Ready Delta Patch Manifest

## Parent baseline
`Invio v1.0.0.1.48.0`

## Target
`Invio v1.0.0.1.48.01`

## Locked scope
Tasks subsystem only: restore reliable **Close Task** confirmation on Windows while preserving the existing Task action/state, WorkerManager, persistence, account-reservation release and delivery-ledger behavior.

## Final delta inventory
- Added: **6**
- Modified: **25**
- Removed: **0**
- Total paths: **31**
- `SHA256SUMS.txt`: **30** payload hashes (every delta payload path except the checksum manifest itself).

## Product implementation paths
- `src/ui/dialogs.py` — opt-in widget-backed message-box flag; default behavior unchanged.
- `src/ui/main_window.py` — Close Task confirmation opts into the widget-backed message box before existing backend close/release execution.

## Frozen task/backend paths
- `src/ui/pages/tasks_page.py`
- `src/tasks/state_machine.py`
- `src/core/state/app_state.py`
- `src/core/worker_manager/manager.py`
- `src/core/storage/domain_store.py`
- `src/tasks/delivery_ledger.py`

## Version / verification
Application `1.0.0.1.48.01` maps to PE `1.0.1.4801`, MSI `1.1.4801`, tag `v1.0.0.1.48.01`. Direct regression tests, repository/distribution contracts and synchronized documentation are included. No file is renamed or removed.
