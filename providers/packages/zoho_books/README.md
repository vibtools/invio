# Invio Zoho Books Provider v1.2.0

Trusted executable external provider plugin for Invio's P13 external-adapter interface v1.

This bundle contains **no mock/demo sending path**. At runtime it uses Zoho OAuth 2.0 and the real Zoho Books v3 REST API to resolve customers/items/currency, create invoices, and request invoice email sending.

## v1.2.0 Easy Onboarding

This bundle implements Invio **Provider Easy Onboarding V1** in addition to Browser OAuth v1 and External Provider Adapter v1. Quick Connect is provider-driven and uses the same generic host contract as the other v1.2.0 OAuth provider bundles; no Zoho/provider-specific setup logic is hardcoded into Invio Accounts UI.

**Quick Connect user inputs:**
- Zoho Region
- OAuth Client ID
- OAuth Client Secret

**Automatically managed/discovered:**
- OAuth Refresh Token
- Zoho Books Organization ID
- Default Item ID (`Invio Service`)

After authorization, Invio discovers the authorized organization and reuses or creates exactly one active `Invio Service` Service item. Item creation uses the provider settings CREATE permission and is not blindly retried; a later onboarding attempt searches the deterministic name before creating again. The host then runs the existing real API Test automatically. Generated/discovered/managed raw fields are hidden by default and remain available under **Advanced / Manual Setup** for backward compatibility. Existing saved accounts are not forced to reconnect solely because this bundle is upgraded.

**Required scopes/permissions:** `ZohoBooks.settings.READ,ZohoBooks.settings.CREATE,ZohoBooks.contacts.READ,ZohoBooks.contacts.CREATE,ZohoBooks.invoices.READ,ZohoBooks.invoices.CREATE`

## v1.1.0 Browser OAuth foundation (historical)

This bundle supports Invio `v1.0.0.1.49.1+` Browser OAuth interface v1 while preserving the existing production invoice/send adapter interface. Use **Connect Zoho Books** for first-time authorization; after the account is saved, the provider refresh-token workflow renews access automatically without repeated browser login unless the provider grant can no longer be refreshed. Manual refresh-token setup remains supported for backward compatibility.

**Browser redirect:** `http://127.0.0.1:8765/oauth/callback/zoho-books`

**v1.1.0 scopes (historical):** `ZohoBooks.settings.READ,ZohoBooks.contacts.READ,ZohoBooks.contacts.CREATE,ZohoBooks.invoices.READ,ZohoBooks.invoices.CREATE`

## What it does

For every Invio recipient, the adapter:

1. Refreshes/caches a real Zoho OAuth access token.
2. Resolves the configured Zoho Books organization and template currency.
3. Resolves each Invio line item to a real Zoho Books Item. Quick Connect normally prepares and stores the reusable **Invio Service** Default Item ID; Advanced/manual accounts can still use an explicit Default Item ID or the existing exact-name fallback.
4. Reuses an existing active customer by exact email when `Reuse Customer` is enabled; otherwise creates a real Zoho Books customer contact.
5. Creates a real Zoho Books invoice with the Invio quantity/rate/due date/memo/terms.
6. Calls the real Zoho Books `POST /invoices/{invoice_id}/email` API with the recipient email and invoice attachment enabled.
7. Returns the real Zoho contact ID and invoice ID to Invio's external-provider execution ledger.

## Required OAuth scopes

Generate the refresh token with these Zoho Books scopes:

- `ZohoBooks.settings.READ`
- `ZohoBooks.settings.CREATE`
- `ZohoBooks.contacts.READ`
- `ZohoBooks.contacts.CREATE`
- `ZohoBooks.invoices.READ`
- `ZohoBooks.invoices.CREATE`

API Test verifies OAuth, organization access, Contacts READ, Items READ, Invoices READ, and an optional Default Item ID. Quick Connect may exercise `ZohoBooks.settings.CREATE` only to create the deterministic managed `Invio Service` item when no compatible existing item is found. Customer/invoice CREATE scopes remain exercised by real Task execution.

## Installation

1. Keep this folder intact.
2. Open **Invio → Providers → Load Provider**.
3. Select `provider.json` from this folder.
4. Invio will warn that `adapter.py` is trusted executable code. Approve only if you trust this bundle.
5. Open **Accounts → Add Account → Zoho Books**.
6. Configure the account fields and run API Test.

## Advanced / Manual account fields

- **Zoho Accounts Server** — data-center-specific OAuth origin, e.g. `https://accounts.zoho.com`.
- **OAuth Client ID** — Zoho API Console client ID.
- **OAuth Client Secret** — corresponding client secret.
- **OAuth Refresh Token** — offline refresh token with the required scopes.
- **Zoho Books Organization ID** — numeric organization ID.
- **Default Item ID (optional)** — numeric Zoho Books Item ID. When blank, each Invio line-item description must exactly match one active Zoho Books Item name.

Supported Accounts origins in this plugin: US, EU, IN, AU, JP, CA, CN, and SA Zoho data centers.

## Template compatibility

Supported:

- Invoice Type: `INVOICE`
- Currency: any currency configured in the target Zoho Books organization
- Due days
- Memo → Zoho invoice `notes`
- Terms → Zoho invoice `terms`
- Customer reuse by exact email
- Multiple line items

Fail-closed / intentionally unsupported because the current Invio template does not carry the Zoho IDs required for an authoritative mapping:

- Automatic tax
- non-zero Invio line tax (Zoho requires a real `tax_id` mapping)
- custom Invio invoice title/subtitle
- Invio footer
- Invio customer-note field

## Real-send semantics

A successful Zoho email API response means Zoho Books accepted/scheduled the invoice email request. It does **not** claim end-recipient mailbox delivery. Invio's existing provider-acceptance vs. email-delivery distinction remains intact.

## Important operational note

Zoho Books publishes an organization-wide API rate limit. This plugin declares a conservative Invio per-account request pace. If several Invio accounts point to the same Zoho Books organization, their combined traffic still shares Zoho's organization-wide limit.

See `docs/OAUTH_SETUP.md` and `docs/LIVE_TEST_CHECKLIST.md` before production use.
## Verified Invio compatibility

The bundle was contract-tested against Invio's frozen external-provider interface v1 using the v1.0.0.1.48.9 baseline and re-checked against the reconstructed v1.0.0.1.49 UI-continuation state. It does not require an Invio core patch.

The deterministic tests use an injected host transport only to verify request shape, mutation ordering, ledger integration, and fail-closed behavior. The production `adapter.py` contains no simulated sending path and only targets official Zoho OAuth/Books endpoints.

