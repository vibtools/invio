# Invio Project Structure

Invio keeps the Vib Tools responsibility-based repository layout and uses the existing domain folders from the blank project template.

```text
.
├── .github/                 GitHub metadata and CI
├── assets/                  Static UI resources
├── config/                  Future runtime configuration
├── data/                    Runtime/import/export data location
├── docs/                    Public user and developer documentation
├── examples/                Public examples
├── project/                 PRIVATE development material (Git ignored)
├── providers/
│   ├── packages/            Packaged Stripe/Refrens provider manifests available to install
│   └── registry/            Locally installed provider manifests (Git ignored)
├── scripts/
│   └── test/                Audit/test entrypoints
├── src/
│   ├── accounts/            Provider-account models
│   ├── core/
│   │   ├── provider_manager/ Manifest validation/install/load
│   │   ├── settings/         Persistent non-sensitive application preferences
│   │   ├── state/            UI milestone in-memory state and account reservations
│   │   └── worker_manager/   One QThread per active task
│   ├── customers/           Customer-list models and email importer
│   ├── invoices/            Invoice-template models
│   ├── tasks/               Task models
│   └── ui/                  Step-40J shell, widgets, dialogs and pages
├── tests/                   Automated unit tests
├── main.py                  Desktop application entrypoint
├── requirements.txt
└── pyproject.toml
```

## Execution Flow

1. `main.py` calls `src.app.main()`.
2. `MainWindow` loads per-user non-sensitive preferences through `SettingsManager`, builds the Step-40J shell/page stack, applies approved settings, and chooses the configured startup page.
3. `ProviderManager` lists packaged Stripe/Refrens manifests as available, exposes only manifests in `providers/registry` as installed providers, and can uninstall by removing only the validated registry manifest.
4. `AppState` owns UI milestone accounts, templates, customer lists, tasks, and account reservations.
5. A task creation validates that every selected account belongs to the chosen provider and is not reserved by another task.
6. Settings control only existing startup/window, confirmation, Live Logs, and file-dialog behavior; credentials and domain state remain outside the settings file.
7. Application-owned custom dialogs use compact parent-relative geometry; Add Account can render provider credentials in two columns when the selected manifest declares more than two fields.
8. When a provider backend runner is later registered, `WorkerManager` creates a distinct `QThread` for that task. Sending never runs on the GUI thread.

## Privacy Rule

`project/` is personal development material, not public documentation. `/project/` is locked in `.gitignore`.
