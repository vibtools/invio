# Configuration

Invio `v1.0.0.1.17` separates Settings, durable operational data, provider registry state, and protected provider credentials.

## Settings

Settings includes Startup & Window, Confirmations, Live Logs, and File Locations. The default startup page remains Accounts.

The non-sensitive settings JSON uses atomic temporary-file replacement and never stores provider credential dictionaries.

Typical settings paths:

- Windows: `%APPDATA%\\Vib Tools\\Invio\\settings.json`
- macOS: `~/Library/Application Support/Vib Tools/Invio/settings.json`
- Linux: `$XDG_CONFIG_HOME/Vib Tools/Invio/settings.json`, otherwise `~/.config/Vib Tools/Invio/settings.json`

## Durable Operational Storage

P02 uses SQLite for non-sensitive operational state:

- Accounts metadata/status and credential reference;
- Customer Lists and ordered customer records (email, optional name/country);
- Invoice Templates/items/terms;
- Tasks, account selection, counters/status/message;
- account reservations;
- P05 immutable Task execution snapshots (ordered recipients, copied template/items/terms, provider ID and assignment strategy).

Typical database filename: `domain.sqlite3` in the same per-user Invio directory as `settings.json`.

The database uses schema version `5`, foreign keys, transactional writes, WAL journaling, and `synchronous=FULL`. Schema v3 added optional customer `name` and `country`; schema v4 added immutable Task execution-snapshot tables; schema v5 adds exactly three durable P10 delivery-ledger tables for runs, per-run recipients and provider operations. Corrupt, newer, partial, or unrecognized storage is not silently replaced.

Migration backups use SQLite live-backup semantics. The `v1.0.0.1.14` close-before-replace correction remains active for the v3-to-v4 P05 migration, preventing Windows from self-locking the temporary backup file during startup.

## Protected Credentials

Provider credential values are stored with Python `keyring` through approved OS-protected backend families only. SQLite stores only `account:<account-id>` references. Invio has no plaintext credential fallback.

If the protected credential entry/backend is unavailable at startup, the Account metadata is still restored for visibility but its runtime status becomes **Not Verified**, so P01 Task gates block execution.

## Provider Registry

Bundled manifests remain under `providers/packages/`; installed manifests remain under ignored `providers/registry/`. P02 does not change ProviderManager behavior.


P03 uses SQLite schema v2 to persist Account verification timestamp and safe error summary. Provider secrets remain outside SQLite.

## P06 provider endpoint configuration

Refrens `API Base URL` remains an Account credential field, but P06 restricts executable authentication to the canonical `https://api.refrens.com` origin. The validation rejects HTTP, alternate/deceptive hosts, embedded URL credentials, non-root paths, queries, and fragments before App ID/App Secret authentication data is constructed. No configurable trust override is added.


## v1.0.0.1.18 Refrens endpoint rule

The trusted Refrens API Base URL is exactly `https://api.refrens.com` (optional trailing slash only). Explicit ports, including `:443`, are rejected before App ID/App Secret transport.

## Agiled Credential Configuration

The packaged Agiled manifest defines one required `API Key` password field and `Default` mode. The value is handled through the same protected Account credential store as other provider secrets. In `v1.0.0.1.21` it is not transmitted because the Agiled executable adapter is fail-closed pending API contract revalidation. There is no configurable Agiled base-URL field in this release, specifically to prevent routing a key to an unverified host.

## v1.0.0.1.22 Agiled Verification

The Agiled credential contract remains one protected `API Key` field with `Default` mode. No base URL is added and no key is transmitted by this release. The official Agiled materials remain internally inconsistent for the executable API contract, so configuration remains fail-closed.

## Customer defaults — v1.0.0.1.40

Settings now includes **Default customer name** and **Default customer country**. If Default customer name is nonblank, that configured value is used for imported customers; if blank, an imported row keeps an explicit name and an email-only/missing-name row uses the email local-part. Default customer country accepts a two-letter ASCII code and is stored uppercase; if blank, explicit imported country is preserved and a missing country becomes `US`. These are non-sensitive preferences saved in the existing Settings JSON.

## v1.0.0.1.40.1 Settings visual contract

Settings values and persistence semantics are unchanged from v1.40. The correction only removes Settings-specific reduced spacing/typography so the existing controls inherit the frozen shared Vib Tools page/card/form tokens. Customer Default Name/Country behavior remains exactly the v1.40 import-time default policy.

## v1.0.0.1.40.2 provider configuration boundary

No new Settings key or provider credential field is added. Agiled continues to store only its protected `api_key` through the existing CredentialStore. The built-in API Test uses the fixed current Public API endpoint `https://api.agiled.ai/public/v1/me`; there is no configurable Agiled endpoint override. Refrens configuration remains API Base URL, URL Key, App ID and App Secret.


## Odoo Provider v1.0.0 configuration

The bundled external Odoo plugin requires four protected Account fields: Odoo Base URL, Database, Username / Email, and API Key. The Base URL is the instance origin only; the plugin adds `/jsonrpc`. Credentials are stored through the same protected credential store as other providers. The plugin remains external trusted code and must be explicitly loaded before its Account type is available.
