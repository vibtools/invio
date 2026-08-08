# Invio Project Structure

```text
.
├── .github/                  GitHub metadata and CI
├── assets/                   Static UI resources, including checkbox checkmark
├── config/                   Runtime configuration location
├── data/                     Runtime/import/export data location
├── docs/                     Public user and developer documentation, including implementation/error inventories
├── examples/                 Public examples
├── project/                  PRIVATE development material (Git ignored)
│   ├── planning/             Production roadmap, phase ledger and update protocol
│   ├── research/             Forensic readiness and release verification records
│   └── specifications/       Baseline/scope freeze records
├── providers/
│   ├── packages/             Bundled Stripe/Refrens provider manifests
│   └── registry/             Locally installed provider manifests (Git ignored)
├── scripts/test/             Repository audit entrypoint
├── src/
│   ├── accounts/             Provider-account models
│   ├── core/
│   │   ├── provider_manager/ Provider manifest validation/install/load/uninstall
│   │   ├── provider_runtime/ Built-in provider API/task execution adapters
│   │   ├── settings/         Persistent non-sensitive preferences
│   │   ├── state/            Runtime domain state and account reservations
│   │   └── worker_manager/   One QThread per active task
│   ├── customers/            Customer-list model and email importers
│   ├── invoices/templates/   Invoice template/currency models
│   ├── tasks/                Task model including template binding
│   └── ui/                   Step-40J shell, dialogs, Dashboard and pages
├── tests/                    Unit/contract tests
├── main.py
├── requirements.txt
└── pyproject.toml
```

## Execution Flow

1. `main.py` calls `src.app.main()`.
2. `MainWindow` loads Settings, builds the shell, state, provider manager, provider runtime, and worker manager.
3. Installed provider manifests control provider visibility.
4. Accounts, invoice templates, customer lists, tasks, and reservations are held in `AppState` for the current session.
5. A task binds one installed provider, one or more unreserved accounts, one invoice template, and one customer list.
6. `ProviderRuntime` snapshots task inputs before execution and returns the applicable provider runner.
7. `WorkerManager` owns a separate `QThread` for each active task. Provider network work executes inside that task worker.
8. Worker signals update Tasks, Reports, Dashboard, and Live Logs on the UI side.

## Privacy

`project/` remains private internal material and is locked by `/project/` in `.gitignore`.

## Production Planning Records

The `v1.0.0.1.5` production-hardening planning delta adds documentation only. Runtime architecture remains unchanged. The current production planning records are:

- `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- `docs/developer/ERROR_HANDLING.md`
- `project/specifications/BASELINE_FREEZE_v1.0.0.1.5.md`
- `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.5.md`
- `project/planning/PRODUCTION_ROADMAP.md`
- `project/planning/PHASE_COMPLETION_LOG.md`
- `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`
