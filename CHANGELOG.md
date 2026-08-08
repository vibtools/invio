# Changelog

## Unreleased

No unapproved changes are scheduled. Future implementation requires explicit approval and a new scope lock.

## 1.0.0.1.2 - 2026-08-07

### Added
- Added a real **Uninstall** action for installed provider cards. Uninstall removes only the validated local registry manifest; packaged provider files and current in-memory account/task data are not deleted.

### Updated
- Made the Add Account dialog wider and shorter, tightened its margins/spacing, and arranged provider/account controls in a compact two-column form.
- Added adaptive one/two-column credential layout: providers with more than two credential fields use two columns while smaller credential sets remain single-column.
- Applied shared compact sizing to all application-owned custom dialogs and application message/confirmation boxes.
- Reflowed the Invoice Template dialog into a wider, shorter two-column upper section without changing template fields or behavior.
- Reduced the New Task account-list minimum height to support the compact modal layout without changing account selection behavior.

### Backend
- Added `ProviderManager.uninstall()` with validated installed-provider lookup and explicit manifest-removal error handling.
- Wired provider Uninstall through the existing Providers page → MainWindow → ProviderManager callback boundary.

### Verification
- Added provider uninstall tests, compact-modal source contracts, and Add Account two-column layout contracts.
- Updated README, user/provider/developer/configuration/API/installation/troubleshooting documentation, release notes, version metadata, patch manifest, and private forensic/update records for `v1.0.0.1.2`.

### Scope protection
- No page, provider ID, provider credential field, provider capability, account mode, account/task model, settings behavior, task runner contract, dependency, or existing feature was removed, renamed, or replaced.
- Provider uninstall does not delete packaged providers, accounts, tasks, customer lists, invoice templates, reports, logs, or settings.
- Native operating-system file/folder picker behavior is unchanged.

## 1.0.0.1.1 - 2026-08-07

### Added
- Replaced the informational Settings page with persistent, user-facing application preferences backed by a dedicated non-sensitive settings manager.
- Added startup selection for a fixed page or the last page used.
- Added optional window size/position memory.
- Added individual confirmation controls for exiting with active tasks, closing tasks, deleting invoice templates, deleting customer lists, and clearing Live Logs.
- Added Live Logs preferences for timestamps, automatic scrolling, and an optional maximum retained line count (`0` = unlimited).
- Added file-location preferences for a default file folder and optional last-used-folder memory. These settings are used by provider manifest loading, customer email import, report export, and log export dialogs.
- Added Restore Defaults and Save Changes controls with validation and user-facing save feedback.

### Backend
- Added `src/core/settings/` with validated JSON settings storage, cross-platform per-user configuration paths, atomic writes, corruption-safe fallback to baseline defaults, runtime last-page/folder/window state, and no credential persistence.
- Settings defaults preserve the behavior of the frozen `v1.0.0.1` baseline until the user explicitly changes a preference.
- Settings are applied to the existing application actions without changing provider, account, invoice, customer-list, task, report, or worker architecture.

### Fixed
- Added a guarded viewport-size chip update so restoring a saved window size cannot access the header chip before it exists.
- Added off-screen protection for restored window position by applying saved coordinates only when they are on a currently available screen.

### Verification
- Added settings backend and wiring tests covering defaults, persistence, invalid settings recovery, folder/window opt-in behavior, credential exclusion, UI controls, and runtime action hooks.
- Updated README, configuration, user, architecture, installation, troubleshooting, versioning, release notes, patch manifest, and private forensic/update records for `v1.0.0.1.1`.

### Scope protection
- No existing page was added, removed, renamed, or reordered.
- No provider manifest, provider credential field, provider ID, capability, account mode, install/load contract, or provider execution contract was changed.
- No account, invoice-template, customer-list, task, report, or worker model was removed, renamed, or replaced.
- No provider network adapter, invoice-sending backend, credential persistence, domain-data persistence, or unrelated feature was added.

## 1.0.0.1 - 2026-08-07

### Fixed
- Fixed the Windows sidebar navigation surface so the scroll area, viewport, and navigation host use the official Vib Tools `#090D14` sidebar background instead of the platform default light surface.
- Corrected the repository audit so an existing validated installed-provider registry state is audited rather than incorrectly treated as a failure.

### Updated
- Restyled the Providers page cards to the official Vib Tools Plugin Page visual contract while preserving the existing provider install/load workflow and provider behavior.
- Removed development-stage and UI-only wording from current runtime labels, provider descriptions, dialogs, Reports, Settings, and current source documentation without enabling or simulating unavailable provider operations.
- Removed the `-ui` suffix from the bundled Stripe and Refrens provider package version labels; credential fields, modes, capabilities, and provider IDs are unchanged.
- Marked the desktop shell as the Invio production build `v1.0.0.1`.
- Synchronized public documentation and release metadata with the production UI baseline.

### Scope protection
- No page was added, removed, or renamed.
- No provider credential field, capability, account mode, provider ID, or install/load behavior was changed.
- No task, account, customer-list, invoice-template, report, log, or settings feature was removed or replaced.
- No provider network adapter or invoice-sending backend was added.

## 1.0.0 - 2026-08-07

### Baseline freeze
- Frozen the user-supplied `Invio_v1.0.0.zip` as the immutable source baseline for subsequent delta updates.
- Baseline SHA-256: `50188d56d416ccd359e748e69996fb3a5566dbeefb469d3d7cf7f7f41336636b`.
- The frozen baseline already includes the `ProviderManifestError` export fix, bundled Stripe and Refrens provider manifests, provider visibility rules, account reservation, and per-task worker-thread architecture.

## 0.1.0 - 2026-08-07

### Added
- New Invio desktop project created from the Vib Tools project template.
- Vib Tools Step-40J compliant dark desktop shell and all requested pages.
- Provider manifest install/load flow with installed-provider-only visibility.
- Provider-grouped account UI and dynamic credential fields.
- Invoice-only template editor without customer/billing/shipping fields.
- Named customer lists with bulk email import.
- Multi-account task creation with strict account reservation exclusivity.
- Dedicated `QThread` worker slot architecture per active task.
- Reports, live logs, and settings UI.
- Public user/developer documentation and private `project/` forensic records.

### Deferred
- Provider API networking and real invoice sending.
- Durable account/credential persistence.
- Provider-specific backend adapters and retry/idempotency implementation.
