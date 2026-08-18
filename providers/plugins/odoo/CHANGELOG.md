# Changelog

## 1.0.1 — 2026-08-17

- Added authoritative Odoo daily-email-limit classification for Invio's generic external-provider batch circuit breaker.
- Treat post-send `UNVERIFIED` mail evidence as an uncertain provider outcome instead of confirmed success.
- Preserve recipient-level mail failures as non-fatal unless the provider reports the proven daily-limit condition.
- Keep Odoo scheduling policy, JSON-RPC workflow, account schema, and invoice/send operations unchanged.

## 1.0.0 — 2026-08-10

- Initial Invio external Odoo provider.
- Added API-key JSON-RPC authentication and API Test.
- Added Odoo partner search/create flow.
- Added customer invoice create/post flow.
- Added headless `account.move.send.wizard.action_send_and_print` email execution.
- Added best-effort attempt-bound Odoo mail evidence inspection.
- Preserved Invio P13/P10 fail-closed uncertainty semantics for non-idempotent external mutations.
