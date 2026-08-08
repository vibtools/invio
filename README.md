# Invio

**Invio** is a Vib Tools desktop application for provider-based invoice automation. Release `v1.0.0.1.5` is a scope-locked Invoice Template UI geometry repair over `v1.0.0.1.4`. The template editor now preserves the real height required by wrapped descriptions, captions, fields, and multiline controls inside its compact scroll area, so Currency/Invoice Type help text cannot overlap adjacent controls and surplus viewport height no longer breaks spacing between cards. Existing template data, validation, provider/task invoice creation and sending behavior are unchanged.

## Current Application Scope

- **Dashboard**: live state summary for installed providers, accounts, templates, customer emails, task activity, account reservations, and the next required setup/action.
- **Accounts**: provider-grouped runtime accounts with provider-defined credential forms and strict account reservation.
- **Invoice Templates**: reusable invoice-only content containing currency, due period, invoice title/subtitle/type, invoice note, customer note, footer, terms, provider options, and line items with quantity, unit amount, and optional tax rate. Templates never store customer, billing, shipping, or payment details.
- **Customer Lists**: independent named bulk-email lists with CSV, TSV, XLSX, XLSM, and TXT import.
- **Tasks**: installed provider -> one or more available provider accounts -> invoice template -> customer list. One account cannot belong to two open tasks.
- **Providers**: manifest-based install/load/uninstall workflow. A provider is selectable in Accounts and Tasks only while installed.
- **Reports / Live Logs / Settings**: compact task reporting, masked execution logs, and persistent non-sensitive application preferences.
- **Threading**: each active task runs through its own `QThread`; provider network sending is executed by the task worker and not by the GUI thread.

## Packaged Providers

### Stripe

Stripe is bundled with Test and Live modes and one secret/restricted-key credential field. The built-in runtime can:

1. find or create the customer by email according to the template option;
2. create a draft `send_invoice` invoice;
3. create the template line items;
4. finalize the invoice;
5. request Stripe to email the finalized invoice;
6. retain failed-recipient state for **Retry Failed**.

The template stores currency codes in uppercase for users and the adapter converts them to Stripe's lowercase API format. Currency amount conversion handles zero-decimal currencies and Stripe's ISK/UGX compatibility rules.

### Refrens

Refrens is bundled with API Base URL, URL Key, App ID, and App Secret credentials. Authentication, invoice-payload construction, invoice creation, and the documented create-time email-delivery payload are implemented in the built-in provider runtime.

The currently approved Customer List model stores email addresses only. Refrens requires `billedTo.name` and `billedTo.country` to create an invoice. Invio therefore blocks a Refrens task before any create/send request when the required country is unavailable instead of inventing billing data. No customer/billing fields were added to invoice templates in this release.

## Invoice Template Contract

A template can contain only reusable invoice content:

- template name;
- uppercase currency code;
- days until due;
- invoice title and optional subtitle;
- invoice type (`INVOICE` or `BOS`);
- invoice note/memo;
- customer-facing note;
- footer;
- one-per-line terms;
- automatic-tax option where supported;
- exact-email customer-reuse option where supported;
- line description, quantity, unit amount, and line tax rate.

Customer identity, billing, shipping, and payment details remain outside the template so the same template can be used for a bulk customer list.

The Currency control is searchable: type any part of a currency code to see a compact case-insensitive result list. Only codes from the existing approved currency catalog are accepted when saving.

## Vib Tools UI

The desktop shell continues to use the frozen Vib Tools Step-40J colors and geometry. `v1.0.0.1.5` changes only the Invoice Template editor's internal sizing contract: template cards keep minimum content height, wrapped helper text uses height-for-width sizing, Currency/Invoice Type notes occupy dedicated full-width rows, and upper/secondary/item cards remain top-aligned while the scroll area's terminal stretch absorbs unused height. Dashboard, Settings, Live Logs, Reports, Providers, and all other controls remain unchanged by this release.

## Settings

Settings remain non-sensitive per-user JSON preferences. Available controls cover startup page, optional window geometry memory, confirmations, Live Logs timestamp/auto-scroll/retention behavior, and file-dialog folders. Account/provider credentials are not written to the settings file. Dashboard is now available as a startup-page choice; the default remains Accounts for compatibility.

## Requirements

- Python 3.12+
- PySide6 6.7+
- openpyxl 3.1+

No new dependency was introduced in `v1.0.0.1.5`; provider HTTP calls continue to use Python's standard library.

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

Install a packaged provider from **Providers**, add its account, create an invoice template, create/import a customer list, then create a task.

## Tests

```bash
python -m unittest discover -s tests -v
python scripts/test/audit.py
```

The test suite covers provider management, settings, account reservation, invoice-template validation and task binding, Stripe provider execution contracts, Refrens required-data protection, UI contracts, and repository/privacy contracts.

## Documentation

- User guide: `docs/user/usage.md`
- Invoice templates: `docs/guides/invoice-templates.md`
- Task guide: `docs/guides/tasks.md`
- Provider guide: `docs/guides/providers.md`
- Architecture: `docs/developer/architecture.md`
- Configuration: `docs/configuration/index.md`
- Troubleshooting: `docs/troubleshooting/index.md`
- Release notes: `docs/release-notes/1.0.0.1.5.md`

## Private Project Material

`project/` contains private development, architecture, scope-lock, and forensic records. It remains explicitly ignored by Git and is not public documentation.

## Production Readiness Program

`v1.0.0.1.5` is the frozen implementation baseline for the production-hardening program. The current source contains real Stripe invoice execution and a partial Refrens adapter, but it is not yet production-certified for durable bulk sending. The production roadmap is documentation-only until each phase receives a separate owner scope lock.

Authoritative planning/status documents:

- Actual implementation status: `docs/developer/ACTUAL_IMPLEMENTATION_STATUS.md`
- Error-handling inventory: `docs/developer/ERROR_HANDLING.md`
- Private baseline freeze: `project/specifications/BASELINE_FREEZE_v1.0.0.1.5.md`
- Private forensic readiness report: `project/research/PRODUCTION_READINESS_FORENSIC_REPORT_v1.0.0.1.5.md`
- Private detailed roadmap: `project/planning/PRODUCTION_ROADMAP.md`
- Private phase completion log: `project/planning/PHASE_COMPLETION_LOG.md`
- Private update protocol: `project/planning/PRODUCTION_UPDATE_PROTOCOL.md`

Current production implementation progress is **0/14 phases complete**; governance/documentation phase `G0` is complete. The next implementation phase is `P01 - Real Account API Verification`, but no P01 code change is authorized by this documentation delta.

## License

MIT License. See `LICENSE`.

Maintained by **Vib Tools** - https://vib.tools/
