# Versioning

Invio uses release versioning controlled by Vib Tools.

- `v1.0.0` is the frozen user-supplied baseline archive for the current update line.
- `v1.0.0.1` is the Update-001 delta release containing only the approved sidebar color correction, Providers page visual correction, production-facing marker cleanup, and directly required release/audit documentation.
- `v1.0.0.1.1` uses the fully reconstructed `v1.0.0.1` state as its frozen baseline and contains only the approved Settings UI/backend implementation, settings-related runtime wiring, settings tests, and synchronized documentation/audit records.
- `v1.0.0.1.2` uses the fully reconstructed `v1.0.0.1.1` state as its frozen baseline and contains only the approved provider uninstall workflow, Add Account compact/two-column layout, global application-owned modal compaction, directly required tests, version metadata, and synchronized documentation/audit records.

Future version changes require an explicitly approved scope. The latest completed version/delta becomes the baseline for the next approved update.
