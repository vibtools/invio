# Invio

**Invio** is a Vib Tools desktop application for provider-based invoice automation. Release **`v1.0.0.1.11`** is the P03 verification/correction baseline. P03 account lifecycle/provider-install consistency was introduced in `v1.0.0.1.10`; this corrective release hardens migration backup fidelity, durable fail-closed credential-loss recovery, and cross-store Account Edit safety without adding P04 functionality.

## Current Application Scope

- **Dashboard**: live summary for installed providers, accounts, templates, customer emails, task activity, account reservations, and next setup/action.
- **Accounts**: provider-grouped accounts with Add/Edit/Re-test/Delete lifecycle controls, real non-blocking API verification, durable verification health, protected credentials, and task reservation safety.
- **Invoice Templates**: reusable invoice-only content. Templates never store customer, billing, shipping, or payment details.
- **Customer Lists**: independent named bulk-email lists with CSV, TSV, XLSX, XLSM, and TXT import.
- **Tasks**: installed provider -> one or more available verified accounts -> invoice template -> customer list. One account cannot belong to two open tasks.
- **Providers**: manifest-based install/load/uninstall workflow. A provider is selectable in Accounts and Tasks only while installed.
- **Reports / Live Logs / Settings**: compact reporting, masked execution logs, and persistent non-sensitive application preferences.
- **Threading**: each active Task runs through its own `QThread`; provider network sending remains outside the GUI thread.

## P02 Durable Storage

Non-sensitive operational state now survives application restart in a per-user SQLite database:

- Accounts metadata and verification status;
- Customer Lists and ordered email addresses;
- Invoice Templates, items, Decimal amounts/rates, and ordered terms;
- Tasks, account selections, status/counters/message;
- account reservations.

The database schema is versioned with SQLite `PRAGMA user_version`. Writes use explicit transactions, foreign keys, WAL journaling, and full synchronous durability. Corrupt/newer/unrecognized storage is not silently replaced. P03 upgrades the schema to version 2 and creates a pre-migration backup before upgrading an existing version-1 database; `v1.0.0.1.11` makes that backup WAL-aware so committed state is preserved even when it is still present in SQLite WAL. The existing version-0 path remains supported.

Typical operational database paths use the same per-user Invio directory as Settings:

- Windows: `%APPDATA%\\Vib Tools\\Invio\\domain.sqlite3`
- macOS: `~/Library/Application Support/Vib Tools/Invio/domain.sqlite3`
- Linux: `$XDG_CONFIG_HOME/Vib Tools/Invio/domain.sqlite3`, otherwise `~/.config/Vib Tools/Invio/domain.sqlite3`

If Invio previously stopped while a Task was `Running`, `Paused`, or `Stopping`, P02 restores that Task as **Stopped** and does not automatically resume provider activity.

## Protected Provider Credentials

Provider credentials are not stored in SQLite or `settings.json`. P02 uses the owner-approved Python `keyring` integration and accepts only approved OS-protected backend families used by the keyring project for Windows Credential Locker, macOS Keychain, Freedesktop Secret Service/libsecret, or KWallet. There is **no plaintext fallback**.

SQLite stores only an opaque account credential reference such as `account:<account-id>`. At startup, credentials are restored into runtime memory from the protected store. If a protected credential is missing or unavailable, the account remains visible but is restored as **Not Verified**, so existing P01 Task creation/Start/Retry gates block provider execution.


## P03 Account Lifecycle and Provider Consistency

- Account metadata/credentials can be edited only while the account is not referenced by an open Task, and every edit requires a fresh successful API Test before commit.
- **Re-test** verifies the current protected credentials on a dedicated `QThread`; success/failure, UTC verification time, and a secret-scrubbed error summary are persisted.
- **Delete** is blocked for reserved/Task-referenced accounts and removes protected credentials with rollback/restore handling if durable deletion fails.
- Provider uninstall never deletes Accounts, protected credentials, Tasks, or reservations. Accounts remain visible under a **Not Installed** provider group.
- A provider with an active Task cannot be uninstalled. Existing inactive Tasks remain preserved, but Start/Retry is blocked until the provider is installed again.
- No age-based verification expiry or background health polling is introduced.

## Packaged Providers

### Stripe

Stripe remains bundled with Test and Live modes. The built-in runtime can find/create customers by email, create draft `send_invoice` invoices, create line items, finalize invoices, request invoice email delivery, and retain current-process failed-recipient state for **Retry Failed**.

### Refrens

Refrens remains bundled with API Base URL, URL Key, App ID, and App Secret. Authentication, invoice payload construction, invoice creation, and create-time email-delivery helpers remain implemented. Normal Refrens Task sending is still deliberately blocked because the current email-only Customer List cannot provide the required customer country. P02 does not change that data contract.

## Invoice Template Contract

A template can contain reusable invoice content only: template name, uppercase currency, due period, title/subtitle/type, invoice note, customer note, footer, terms, provider options, and line items. Customer identity, billing, shipping, and payment details remain outside templates.

## Settings

Settings remain a separate non-sensitive per-user JSON file. They control startup/window behavior, confirmations, Live Logs, and file-dialog locations. Provider secrets are never written to Settings.

## Requirements

- Python 3.12+
- PySide6 6.7+
- openpyxl 3.1+
- keyring 25.7+

P02 adds `keyring>=25.7,<26`. The current keyring release line supports Python 3.12 and provides the approved system-keyring APIs used by Invio. Provider HTTP calls still use Python's standard library. 

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

Install a packaged provider from **Providers**, add and verify its account, create an Invoice Template, create/import a Customer List, then create a Task.

## Tests

```bash
python -m unittest discover -s tests -v
python scripts/test/audit.py
```

The P03 suite covers schema-v1-to-v2 migration, Account edit/delete/re-test, protected-secret compensation, verification-health persistence, provider-uninstall consistency, Task execution gates, WAL-aware migration-backup fidelity, durable credential-loss downgrade, and fail-closed cross-store Account Edit recovery while retaining the P01/P02 regression suite.

## Documentation

- User guide: `docs/user/usage.md`
- Provider guide: `docs/guides/providers.md`
- Task guide: `docs/guides/tasks.md`
- Architecture: `docs/developer/architecture.md`
- Actual implementation status: `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- Error handling: `docs/developer/ERROR_HANDLING.md`
- Configuration: `docs/configuration/index.md`
- Troubleshooting: `docs/troubleshooting/index.md`
- Release notes: `docs/release-notes/1.0.0.1.11.md`

## Private Project Material

`project/` contains private development, architecture, scope-lock, forensic, phase, and baseline records. It remains Git-ignored and is not public documentation.

## Production Readiness Program

`v1.0.0.1.11` is the verified P03 corrective baseline. Production progress remains **3/14 phases complete**. The next separately approved phase is **P04 - Customer Data Contract and Import Upgrade**.

P02 makes operational metadata restart-durable, but it does **not** claim exact provider-side crash reconciliation. Per-recipient provider IDs, attempts, run identities, and durable retry/idempotency evidence remain P10 scope.

## License

MIT License. See `LICENSE`.

Maintained by **Vib Tools** - https://vib.tools/
