# Agiled Runtime Contract

Current correction candidate: **Invio v1.0.0.1.40.2**.

## Verified current API surface

The owner-supplied current `openapi.yaml` identifies:

- OpenAPI `3.1.0`;
- API title/version `Agiled Public API` / `1.0.0`;
- HTTP Bearer authentication;
- `GET /public/v1/me` for the authenticated token/organization scope;
- `GET/POST /public/v1/invoices` and CRUD operations for invoice resources;
- `Idempotency-Key` guidance for create operations.

## Invio API Test

Agiled Account API Test uses exactly:

`GET https://api.agiled.ai/public/v1/me`

Headers include `Accept: application/json` and `Authorization: Bearer <protected API key>`. The request has no body and is side-effect free. A successful provider response is required before the existing Add Account/Re-test workflow can mark the account verified.

## Task sending remains fail-closed

The supplied OpenAPI does **not** define an invoice email/send endpoint. It defines `/public/v1/documents/{documentId}/send` for Documents only; Invio does not reinterpret that operation as invoice sending.

The invoice create operation references a generic `MutationRequest` whose schema permits additional properties but publishes no invoice-specific field names, required customer/client mapping, currency representation, line-item shape or other field-level requirements. Invio therefore cannot safely construct a production invoice mutation from its immutable Task snapshot without guessing.

Accordingly, v1.40.2 does not register an Agiled Task runner and performs no Agiled invoice mutation. This preserves the provider-neutral fail-closed contract until an authoritative invoice request/send schema is available.
