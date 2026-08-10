# Refrens Runtime Request Contract

Invio uses the existing Refrens authentication flow and `POST /businesses/:urlKey/invoices` create-invoice endpoint.

For v1.0.0.1.40, the create request contains the already-supported Invio mappings for invoice title/subtitle/type, currency, due date, `billedTo`, `items`, optional `notes`, and the existing create-time `email.to` request used by the send workflow.

The v1.39 mapping of Invio template terms as `terms: list[str]` is intentionally not emitted. Owner live evidence showed Refrens rejecting that representation with an embedded-value cast error, while the published Create New Invoice request documentation does not define request-side `terms`.

This correction does not invent a new Refrens terms schema. Invio retains template terms in its immutable Task snapshot; a future mapping requires separate explicit scope and provider-contract evidence.
