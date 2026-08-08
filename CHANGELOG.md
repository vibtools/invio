# Changelog

## Unreleased

No unapproved changes are scheduled. Future implementation requires explicit approval and a new scope lock.

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
