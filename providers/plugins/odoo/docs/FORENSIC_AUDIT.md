# Forensic Audit — InvoiceRouter n8n Odoo → Invio External Provider

## Source artifacts audited

- `InvoiceRouter-v2.0.1-install-bundle.zip`
- `n8n-nodes-invoicerouter-2.0.1.zip`

No uploaded package code was executed during the audit. The archives were extracted and inspected as source/data only.

## Proven InvoiceRouter lifecycle

The supplied lifecycle declares:

`customer.search_by_email → customer.create_if_missing → invoice.create → invoice.post → invoice.send_email`.

The source implementation uses Odoo JSON-RPC `/jsonrpc` with Database + Username + Password/API Key. Its runtime:

1. calls `common.authenticate`;
2. searches `res.partner` by email and creates it if missing;
3. creates an `account.move` customer invoice;
4. posts it using `account.move.action_post`;
5. creates `account.move.send.wizard` with Email selected and the partner recipient;
6. executes `account.move.send.wizard.action_send_and_print`;
7. inspects attempt-bound `mail.message`, `mail.notification`, `mail.mail`, and PDF-related evidence.

The source explicitly rejects treating `account.move.action_send_and_print` by itself as a headless email send because that path opens the interactive wizard.

## Mapping to Invio P13

The plugin uses only Invio's public external-provider interface v1:

- `SAFE_READ` for authentication/lookups/evidence reads;
- `NON_IDEMPOTENT_MUTATION` for partner create, invoice create, post, wizard create, and send;
- `ExternalRecipientResult` to persist safe Odoo customer/invoice references;
- existing P05 immutable Task snapshot, P06 preflight, P08 transport reliability, P10 durable ledger, and WorkerManager thread architecture.

No direct AppState, DomainStore, Qt, filesystem-registry, or credential-store access is added to the plugin.

## Important architecture difference from InvoiceRouter

InvoiceRouter has provider-specific lifecycle checkpoints and can reuse an existing Odoo invoice ID at a later resume stage. Invio external-adapter interface v1 does not pass a prior provider invoice ID back to adapter code during a later retry.

Therefore this plugin does **not** fabricate equivalent resume behavior. Ambiguous/partial non-idempotent operations remain fail-closed/Uncertain under Invio's existing P13/P10 safety rules.

## External Odoo evidence checked

Odoo 18/19 official External RPC documentation supports API keys by replacing the RPC password with the key while preserving the login. Odoo 19 retains the legacy RPC APIs during the migration period while providing JSON-2 as the future external API.

Odoo 18/19 official `account.move.send.wizard` source exposes `move_id`, `sending_methods`, `sending_method_checkboxes`, and `mail_partner_ids`; `action_send_and_print` creates invoice documents and sends them.

This validates the supplied n8n sender path as an appropriate current protocol for the first Invio Odoo plugin without silently migrating to a different API.
