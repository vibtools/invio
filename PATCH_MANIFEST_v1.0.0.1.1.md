# Patch Manifest: Invio v1.0.0.1.1

## Baseline

- Frozen previous release: `v1.0.0.1`
- Previous replace-ready delta: `Invio_v1.0.0.1_delta_patch.zip`
- Previous delta SHA-256: `acf63c148d8740dbcf94f00e304afe3bffc537b6c04420a3482496646bcd7c73`
- Reconstruction rule: frozen `Invio_v1.0.0.zip` + `Invio_v1.0.0.1_delta_patch.zip`

## Approved scope

Settings-related UI and backend only, plus directly required versioning, tests, forensic verification, and synchronized Markdown documentation.

## Functional patch areas

- `src/core/settings/`: persistent non-sensitive settings backend.
- `src/ui/pages/settings_page.py`: user-friendly settings controls.
- `src/ui/pages/logs_page.py`: applies log retention/auto-scroll settings.
- `src/ui/main_window.py`: applies startup, window, confirmation, log, and file-location settings to existing actions.
- `tests/`: settings backend and wiring verification.

No baseline file is deleted by this patch.
