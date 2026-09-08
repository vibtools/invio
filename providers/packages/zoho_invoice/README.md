# Invio Zoho Invoice Provider Plugin v1.2.0

Trusted external provider bundle for **Invio v1.0.0.1.49.1+ / P13 external adapter interface v1 + optional Browser OAuth v1**.

## v1.2.0 Easy Onboarding

This bundle implements Invio **Provider Easy Onboarding V1** in addition to Browser OAuth v1 and External Provider Adapter v1. Quick Connect is provider-driven and uses the same generic host contract as the other v1.2.0 OAuth provider bundles; no Zoho/provider-specific setup logic is hardcoded into Invio Accounts UI.

**Quick Connect user inputs:**
- Zoho Region
- OAuth Client ID
- OAuth Client Secret

**Automatically managed/discovered:**
- OAuth Refresh Token
- Zoho Invoice Organization ID
- Default Item ID (`Invio Service`)

After authorization, Invio discovers the authorized organization and reuses or creates exactly one active `Invio Service` Service item using the provider settings CREATE permission. The host then runs the existing real API Test automatically. Generated/discovered/managed raw fields are hidden by default and remain available under **Advanced / Manual Setup** for backward compatibility. Existing saved accounts are not forced to reconnect solely because this bundle is upgraded.

**Required scopes/permissions:** `ZohoInvoice.settings.READ,ZohoInvoice.settings.CREATE,ZohoInvoice.contacts.READ,ZohoInvoice.contacts.CREATE,ZohoInvoice.invoices.READ,ZohoInvoice.invoices.CREATE`

## v1.1.0 Browser OAuth foundation (historical)

This bundle supports Invio `v1.0.0.1.49.1+` Browser OAuth interface v1 while preserving the existing production invoice/send adapter interface. Use **Connect Zoho Invoice** for first-time authorization; after the account is saved, the provider refresh-token workflow renews access automatically without repeated browser login unless the provider grant can no longer be refreshed. Manual refresh-token setup remains supported for backward compatibility.

**Browser redirect:** `http://127.0.0.1:8766/oauth/callback/zoho-invoice`

**v1.1.0 scopes (historical):** `ZohoInvoice.settings.READ,ZohoInvoice.contacts.READ,ZohoInvoice.contacts.CREATE,ZohoInvoice.invoices.READ,ZohoInvoice.invoices.CREATE`

## Purpose

OAuth refresh → verify organization/items/contacts/invoices → resolve/create customer → create real Zoho Invoice invoice → email the created invoice to the recipient.

## Install in Invio

1. Extract this provider ZIP to a temporary folder.
2. Open **Invio → Providers**.
3. Click **Load Provider** and select this bundle's `provider.json`.
4. Review and approve the executable external-provider trust prompt.
5. Open **Accounts → Add Account**, choose the provider, and enter the provider credentials described below.
6. Save the account and run **Re-test/API Test**. The account must be Verified before task execution is allowed.
7. Create/select an invoice template and customer list, then create a task with this provider.

Credentials entered through Invio Accounts use Invio's protected credential-storage boundary. Do not place secrets in `provider.json`, source files, screenshots, Git commits, or issue reports.

## Advanced / Manual account fields

- Zoho Accounts Server
- OAuth Client ID
- OAuth Client Secret
- OAuth Refresh Token
- Zoho Invoice Organization ID
- Default Item ID (optional)

## OAuth / API setup

See [`docs/OAUTH_SETUP.md`](docs/OAUTH_SETUP.md).

## Live acceptance

See [`docs/LIVE_TEST_CHECKLIST.md`](docs/LIVE_TEST_CHECKLIST.md). Use a provider account and recipient mailbox you control before production rollout.

## Safety model

- All invoice/customer/order mutations flow through Invio's existing external-provider operation contract.
- Provider-supported idempotency is used where the provider offers a stable idempotency primitive; otherwise mutations are declared non-idempotent so ambiguous outcomes fail closed rather than blindly replay.
- OAuth secrets are account credentials, not source configuration.
- Unsupported Invio template semantics fail validation rather than being guessed.

## Verification truth boundary

The bundle contains production REST/OAuth implementation only; there is no mock/demo sending path in `adapter.py`. Automated tests use deterministic transport doubles so they can verify request construction, mutation classification, idempotency/uncertainty behavior, and Invio P13 compatibility without creating real third-party invoices. A real provider account and controlled recipient mailbox are still required for final live acceptance.

