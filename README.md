# Invio

**Invio** is a Vib Tools desktop application for provider-based invoice automation. Release **`v1.0.0.1.17`** completes **P06 - Provider Capability and Preflight Validation** on top of the verified `v1.0.0.1.16` P05 baseline.

## Current Application Scope

- **Dashboard**: live summary for installed providers, accounts, templates, customer count, task activity, account reservations, and next setup/action.
- **Accounts**: provider-grouped accounts with Add/Edit/Re-test/Delete lifecycle controls, real non-blocking API verification, durable verification health, protected credentials, and task reservation safety.
- **Invoice Templates**: reusable invoice-only content. Templates never store customer, billing, shipping, or payment details.
- **Customer Lists**: independent named bulk-customer lists. Email is mandatory; explicit name and country are optional. CSV/TSV/XLSX/XLSM structured imports and legacy email-only imports are supported.
- **Tasks**: installed provider -> one or more available verified accounts -> invoice template -> customer list. One account cannot belong to two open tasks.
- **Providers**: manifest-based install/load/uninstall workflow with P06 declared-vs-executable capability visibility and packaged-runtime contract reconciliation. A provider is selectable in Accounts and Tasks only while installed.
- **Reports / Live Logs / Settings**: compact reporting, masked execution logs, and persistent non-sensitive application preferences.
- **Threading**: each active Task runs through its own `QThread`; provider network sending remains outside the GUI thread.

## P02 Durable Storage

Non-sensitive operational state now survives application restart in a per-user SQLite database:

- Accounts metadata and verification status;
- Customer Lists and ordered customer records (email, optional name, optional country);
- Invoice Templates, items, Decimal amounts/rates, and ordered terms;
- Tasks, account selections, status/counters/message;
- account reservations.

The database schema is versioned with SQLite `PRAGMA user_version`. Writes use explicit transactions, foreign keys, WAL journaling, and full synchronous durability. Corrupt/newer/unrecognized storage is not silently replaced. P03 introduced schema v2 verification-health metadata and WAL-aware migration backups. P04 upgrades to schema v3 for customer metadata. P05 upgrades to **schema v4**, adding durable immutable Task execution-snapshot tables for recipients, copied invoice-template content, provider identity, and the ordered account-assignment basis while preserving existing Task/customer/template tables.

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

## P04 Verification Corrections in v1.0.0.1.13

The v1.0.0.1.12 P04 implementation was re-audited against the approved plan. v1.0.0.1.13 keeps the P04 architecture and feature scope unchanged while correcting four P04 contract defects and one out-of-scope UI drift:

- the historical mutable `CustomerList.emails` list behavior is restored through a customer-record-backed compatibility view;
- conflicts against existing Customer List metadata now retain the source row number in import diagnostics;
- explicit country values are restricted to two ASCII alphabetic characters so provider-required two-letter codes cannot accept non-ASCII lookalikes;
- malformed workbook/parser failures are converted to the existing user-facing import error contract instead of escaping as uncaught parser exceptions;
- the unrelated Dashboard metric label is restored to its pre-P04 wording.

No P05 immutable Task behavior, Refrens Task enablement, provider/worker architecture change, dependency change, or new page is included.

## v1.0.0.1.14 Operational Storage Runtime Hotfix

A Windows startup failure was reproduced in the schema-migration backup path. `DomainStore` created the WAL-aware SQLite backup into a temporary `.bak.tmp` database using the SQLite connection context manager and then immediately attempted to atomically replace the final `.bak` file. Python's `sqlite3.Connection` context manager commits or rolls back but does **not** close the connection, so Windows could keep the temporary backup file locked and raise `WinError 32` during `Path.replace()`.

`v1.0.0.1.14` explicitly closes the temporary backup destination connection before the atomic replacement. The migration sequence, WAL-aware live-backup semantics, schema version **3**, corruption/future-schema fail-closed rules, protected credentials, provider runtime, Task workers, UI and production roadmap are otherwise unchanged. A platform-neutral regression test now verifies that the destination handle is closed before replacement.


## P05 Immutable Task Execution Snapshots

Every newly created Task now captures and durably stores the exact execution inputs approved at Task creation time:

- ordered customer records (`email`, optional `name`, optional `country`);
- a complete immutable copy of the selected Invoice Template, its items and terms;
- provider ID;
- ordered selected Account IDs and the existing round-robin assignment strategy;
- `Task.id` as the canonical logical run identity.

`Task.total` is derived from the frozen recipient set. Start and Retry reconstruct provider-runtime input from the same durable snapshot rather than reading the current Customer List or current Invoice Template. Later customer imports/enrichment or template edits therefore do not silently change an existing Task. A different logical execution requires creating a new Task, which receives a new Task ID and a new snapshot.

Existing pre-P05 Tasks are preserved during schema-v3-to-v4 migration but are marked **LegacyUnavailable** because their historical creation-time recipients/template were never stored. Invio does not invent those missing inputs from current data. Such Tasks remain visible and closable, but Start/Retry fail closed; create a new Task to execute current inputs. Provider credentials are never copied into snapshot storage.

## v1.0.0.1.16 P05 verification correction

The P05 re-audit found three consistency gaps not covered by the v1.0.0.1.15 suite. New post-P05 Task persistence now requires a real captured snapshot and can no longer silently create `LegacyUnavailable` records; captured Task progress is validated against the frozen recipient count; and routine status/progress persistence no longer rewrites the immutable Task total. SQLite remains schema v4 and no P06 behavior is introduced.

## Packaged Providers

### Stripe

Stripe remains bundled with Test and Live modes. The built-in runtime can find/create customers by email, create draft `send_invoice` invoices, create line items, finalize invoices, call Stripe's invoice-send endpoint, and retain current-process failed-recipient state for **Retry Failed**. Stripe documents that test-mode send requests do not emit real customer emails, so test-mode API success must not be interpreted as inbox delivery.

### Refrens

Refrens remains bundled with API Base URL, URL Key, App ID, and App Secret. Authentication, invoice payload construction, invoice creation, and create-time email-delivery helpers remain implemented. P04 can now store explicit customer name/country data required by the Refrens payload contract, but **normal Refrens Task sending remains deliberately disabled until the separately approved P11 pipeline**.

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

The current suite covers P01-P05 regression behavior plus P06 manifest/runtime reconciliation, packaged-ID collision protection, no-side-effect Task preflight, account-health validation, Stripe provider/template safety rules, Refrens endpoint trust enforcement, and the continued P11 Refrens Task gate.

## Documentation

- User guide: `docs/user/usage.md`
- Provider guide: `docs/guides/providers.md`
- Task guide: `docs/guides/tasks.md`
- Architecture: `docs/developer/architecture.md`
- Actual implementation status: `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- Error handling: `docs/developer/ERROR_HANDLING.md`
- Configuration: `docs/configuration/index.md`
- Troubleshooting: `docs/troubleshooting/index.md`
- Release notes: `docs/release-notes/1.0.0.1.17.md`

## Private Project Material

`project/` contains private development, architecture, scope-lock, forensic, phase, and baseline records. It remains Git-ignored and is not public documentation.

## Production Readiness Program

`v1.0.0.1.17` is the verified P06 baseline. Production progress is **6/14 phases complete**. The next separately approved phase is **P07 - Task State Machine and Resend Safety**.

P02 makes operational metadata restart-durable, but it does **not** claim exact provider-side crash reconciliation. Per-recipient provider IDs, attempts, run identities, and durable retry/idempotency evidence remain P10 scope.

## License

MIT License. See `LICENSE`.

Maintained by **Vib Tools** - https://vib.tools/

## P06 Provider Capability and Preflight Validation

Before a new Task is persisted, and again before Start or Retry creates a runner, Invio now performs a deterministic local preflight over the provider installation, packaged manifest/runtime binding, Account verification health, P05 immutable template/customer snapshot, and provider-specific capability rules. A failed preflight creates no Task/reservation at the New Task boundary and performs no provider-side invoice/customer mutation.

For packaged providers, declared manifest capabilities are now distinguished from executable runtime capability. Stripe currently has executable API Test + invoice/send support. Refrens has executable API Test support, but its normal Task invoice/send pipeline remains deliberately disabled until P11. External loaded manifests still require the existing injected runner API; P06 does not introduce the P13 external-adapter architecture.

Packaged IDs (`stripe`, `refrens`) are reserved against external-manifest collision. An already-installed packaged-ID manifest whose execution-relevant credential/mode/capability contract does not match the bundled package fails closed and is never silently rewritten.

The current Stripe adapter is preflighted as standard `INVOICE` only. Automatic Tax and non-zero template line tax are blocked before network execution because the current Invio customer/send contract does not supply the location/tax-rate object semantics needed to guarantee those behaviors. Customer reuse and the existing description/footer/customer-note/terms mappings remain supported.

Refrens authentication is now allowed only to the canonical `https://api.refrens.com` origin. URL trust is validated before App ID/App Secret authentication payload construction. No Refrens Task sending is enabled by P06.
