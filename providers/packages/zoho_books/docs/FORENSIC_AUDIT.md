# v1.1.0 Browser OAuth forensic delta

The provider execution adapter remains interface v1. Browser OAuth is optional interface v1 metadata/hooks only. Authorization uses provider official OAuth endpoints, state validation is host-owned, PKCE is used where declared, browser completion returns refresh/bootstrap credentials only, and deterministic tests verify that the existing invoice/send paths remain unchanged. Live third-party OAuth and mailbox receipt remain owner acceptance gates.

# Forensic Audit — Invio Zoho Books Provider v1.0.0

## Scope

Standalone external provider bundle only. No Invio core, UI, storage, WorkerManager, provider registry, schema, or business-logic modification is required.

## Architecture contract

- External adapter interface: v1
- Provider ID: `zoho_books`
- Capabilities: `invoice`, `send_invoice`, `api_test`
- Runtime entrypoint: `create_adapter`
- Uses only Python standard library plus Invio's exported external-provider contract.
- Does not mutate `sys.path`.
- Does not bypass Invio's host-managed `context.request` transport.

## Real API paths used

- OAuth refresh: `{accounts_server}/oauth/v2/token`
- Organization read: `/books/v3/organizations/{organization_id}`
- Currencies: `/books/v3/settings/currencies`
- Items: `/books/v3/items` and `/books/v3/items/{item_id}`
- Contacts: `/books/v3/contacts`
- Invoices: `/books/v3/invoices`
- Invoice email: `/books/v3/invoices/{invoice_id}/email`

## Mutation classification

- OAuth/resource lookups: `SAFE_READ`
- Contact create: `NON_IDEMPOTENT_MUTATION`
- Invoice create: `NON_IDEMPOTENT_MUTATION`
- Invoice email send: `NON_IDEMPOTENT_MUTATION`

This intentionally uses Invio's existing write-ahead delivery ledger and uncertain-outcome handling. No provider mutation is retried blindly by the adapter.

## Known truth boundary

The implementation is wired only to real Zoho endpoints. A true external send cannot be certified without owner-supplied valid Zoho OAuth credentials, an authorized organization, and a real recipient mailbox. Production acceptance must therefore complete `LIVE_TEST_CHECKLIST.md`.
## Verification result

- Python syntax compilation: PASS (`adapter.py`, provider test module).
- Standalone provider tests against the frozen Invio v1.0.0.1.48.9 source baseline: 6/6 PASS.
- Compatibility re-check against the reconstructed Invio v1.0.0.1.49 UI-continuation state: 6/6 PASS.
- Full P13 install/load/validate/task-run integration path: PASS under deterministic host-managed test transport.
- Production adapter direct-network bypass audit: PASS; all OAuth and Books calls use Invio `context.request`.
- Production mock/demo endpoint audit: PASS; none present.
- Live Zoho credential/send certification: PENDING OWNER LIVE GATE because no owner OAuth secret or mailbox is available in the forensic environment.

## v1.2.0 Easy Onboarding verification note

This bundle additionally declares Invio Easy Onboarding V1. Verify Quick Connect hides generated/discovered/managed fields by default, provider preparation is repeat-safe/fail-closed, automatic API Test runs after preparation, and Advanced / Manual Setup preserves the previous credential path. Production adapter paths remain real API only.
