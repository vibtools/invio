# Invio Odoo Provider v1.0.1

Trusted executable external provider plugin for Invio `v1.0.0.1.49.6`.

## Scope

This plugin adds Odoo as an external provider through Invio's existing P13 interface. It does not modify Invio core source, SQLite schema, WorkerManager, Stripe, Refrens, Agiled, UI, or dependencies.

The implementation is based on:

- the owner-supplied InvoiceRouter/n8n Odoo workflow, which uses Odoo JSON-RPC `/jsonrpc` and a headless `account.move.send.wizard` flow;
- Odoo 18/19 External RPC API behavior, where an API key replaces the user's password for RPC authentication while the login remains in use;
- Odoo 18/19 `account.move.send.wizard.action_send_and_print` behavior for creating invoice documents and sending them.

## Installation

1. Extract this ZIP to a permanent folder.
2. Open Invio → **Providers** → **Load Provider**.
3. Select this folder's `provider.json`.
4. Invio will warn that `adapter.py` is trusted executable code. Approve only if you trust this bundle.
5. Install/Load the provider.
6. Go to **Accounts** → **Add Account** → **Odoo**.

## Account fields

- **Odoo Base URL**: instance origin only, e.g. `https://your-company.odoo.com`
- **Database**: Odoo database technical name
- **Username / Email**: Odoo login
- **API Key**: generated API key; it is used in the RPC password slot as documented by Odoo

## API Test

API Test performs only host-managed safe reads:

1. `common.authenticate`
2. `account.move.search_read`
3. `account.move.send.wizard.fields_get`

The test fails closed if the target database cannot expose the invoice/send-wizard contract used by this provider.

## Invoice workflow

For each recipient:

1. Authenticate.
2. When Customer Reuse is enabled, search `res.partner` by email.
3. Create a partner if needed.
4. Resolve `res.country` from the two-letter customer country.
5. Resolve `res.currency` from the invoice template currency.
6. Create `account.move` with `move_type=out_invoice` and invoice lines.
7. Post with `account.move.action_post`.
8. Verify posted invoice state.
9. Capture a pre-send `mail.message` baseline when permitted.
10. Create `account.move.send.wizard` with Email selected and the recipient partner bound.
11. Verify the wizard selected email and resolved a recipient.
12. Execute `account.move.send.wizard.action_send_and_print` with `mail_notify_force_send=True`.
13. Best-effort inspect new attempt-bound `mail.message`, `mail.notification`, and `mail.mail` evidence.
14. Return the Odoo partner ID and invoice ID into Invio's durable delivery ledger.

Invio Reports still correctly distinguish **Provider Accepted** from independently confirmed mailbox delivery.

## Supported Invio template behavior

- Invoice Type: `INVOICE`
- Currency: resolved by Odoo currency code
- Due date: supported
- Memo: mapped to Odoo `narration`
- Customer reuse: supported
- Line tax: not enabled by this adapter
- Automatic tax: not enabled by this adapter
- Footer, Customer Note, Terms: intentionally unsupported by this adapter
- Custom invoice title/subtitle: blocked rather than silently discarded

Use the default `Invoice` title and blank subtitle for the first live canary.

## Safety / retry boundary

Odoo's legacy JSON-RPC write calls do not provide a provider-supported idempotency key in this implementation. All external writes therefore use Invio's `NON_IDEMPOTENT_MUTATION` contract.

If a write has an ambiguous outcome or a later lifecycle stage fails after an external mutation succeeded, Invio may mark the recipient **Uncertain** and will not blindly replay it. This intentionally prevents duplicate customers/invoices/emails. Inspect Odoo before starting a new Task for an uncertain recipient.

Invio v1.49.6 also halts the external batch before the next recipient when Odoo reports the proven daily email limit, or when post-send provider evidence is `UNVERIFIED`. The current recipient remains subject to Invio's durable Uncertain safety rule after a non-idempotent send mutation; untouched recipients remain Pending for safe later continuation.

This is narrower than InvoiceRouter's own lifecycle checkpoint/resume implementation because Invio P13 interface v1 does not expose prior provider invoice IDs back to the external adapter on a later retry. No Invio core architecture was changed to bypass that safety boundary.

## Odoo version/API note

The plugin deliberately uses the currently proven `/jsonrpc` workflow from the supplied n8n node. Odoo 19 also provides the newer JSON-2 API. Odoo has announced long-term retirement of the legacy external RPC endpoints, so a future migration should be a separate approved plugin update rather than a silent protocol change.

## First live test

Use **one controlled recipient** first. See `docs/LIVE_TEST_CHECKLIST.md`.
