# Invio

**Invio** is a Vib Tools desktop application for provider-based invoice automation workflows. Invio is maintained as a production application: unavailable provider operations are reported as unavailable rather than represented by placeholder or simulated success states.

## Current Application Scope

- **Accounts**: added accounts are grouped under installed providers. Provider-defined credential fields are rendered dynamically.
- **Invoice Templates**: reusable invoice-only templates with currency, due period, memo, footer, tax/reuse flags, and line items. No customer, billing, or shipping data is stored in a template.
- **Customer Lists**: multiple named lists, each containing its own bulk email set. CSV, TSV, XLSX, XLSM, and TXT email import is supported.
- **Tasks**: provider → one or more provider accounts → customer list. Reserved accounts cannot be selected by another task.
- **Providers**: manifest-based install/load flow. A provider appears in Accounts and Tasks only after installation/loading.
- **Reports / Live Logs / Settings**: application reporting, diagnostic, and settings surfaces.
- **Threading contract**: every active task receives a distinct `QThread` slot; a registered provider runner executes through that worker layer rather than the GUI thread.

## Packaged Providers

Two provider manifests are bundled and available from the **Providers** page:

- **Stripe**: one secret/restricted API key field with Test and Live account modes.
- **Refrens**: API Base URL, URL Key, App ID, and App Secret fields based on the supplied Refrens Invoice Sender v1.0.3 credential contract.

Installing either provider copies its validated manifest into the local provider registry. Until then it does not appear in Accounts or Tasks.

## Vib Tools UI Baseline

The desktop UI follows the official Vib Tools Step-40J design baseline. The Providers page follows the official Plugin Page card contract, and the sidebar navigation surface uses the official dark shell background across the scroll area, viewport, and navigation host.

## Runtime Availability

Provider manifests define provider identity, credential fields, account modes, and declared capabilities. A task can execute only when a task runner has been registered for the selected provider. If no runner is registered, Invio reports the provider as unavailable and sends nothing. Account credentials currently remain in memory for the active application session.

## Requirements

- Python 3.12+
- PySide6 6.7+
- openpyxl 3.1+

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

Open **Providers** and install Stripe and/or Refrens as required. Installed providers become available on the Accounts and Tasks pages.

## Tests

```bash
python scripts/test/audit.py
```

The audit validates source syntax, unit contracts, packaged and installed provider manifests, provider visibility rules, account reservation exclusivity, customer-list behavior, invoice-template validation, and repository privacy rules.

## Documentation

- User guide: `docs/user/usage.md`
- Installation: `docs/getting-started/installation.md`
- Provider guide: `docs/guides/providers.md`
- Provider manifest contract: `docs/api/provider-manifest.md`
- Architecture: `docs/developer/architecture.md`
- Troubleshooting: `docs/troubleshooting/index.md`
- Release notes: `docs/release-notes/1.0.0.1.md`

## Private Project Material

The `project/` directory is reserved for personal development notes and internal forensic/design records. It is explicitly ignored by Git and is not public documentation.

## License

MIT License. See `LICENSE`.

Maintained by **Vib Tools** — https://vib.tools/
