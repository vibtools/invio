# Refrens Runtime Request Contract

Invio uses the existing Refrens authentication flow and canonical `https://api.refrens.com` host.

## v1.0.0.1.40.1 explicit send boundary

Owner v1.40 live evidence proved that invoice creation succeeded for all seven controlled recipients but did not prove that an invoice email was triggered. The runtime therefore treats invoice creation and email triggering as separate provider mutations:

1. authenticate;
2. `POST /businesses/:urlKey/invoices`;
3. require and durably record the returned invoice `_id`;
4. `POST /businesses/:urlKey/invoices/:invoiceID/email` with the recipient `to` object;
5. mark provider send acceptance only after the explicit email endpoint succeeds.

If invoice creation succeeds but the explicit email endpoint returns a definitive failure, `Retry Failed` reuses the durable invoice `_id` and retries only the email trigger. It does not create another invoice for that recipient. Ambiguous non-idempotent provider outcomes remain fail-closed under the existing P10 uncertainty policy.

The v1.40 omission of the unsupported request-side Invio `terms: list[str]` representation remains unchanged. Customer identity comes only from the immutable Task snapshot. No Refrens authentication, host-trust, rate policy, WorkerManager or SQLite schema change is introduced.

Provider acceptance is not the same as independently confirmed mailbox delivery. P11 remains live-acceptance pending until the controlled recipient actually receives the invoice email.

## v1.0.0.1.40.2 live provider rejection evidence

Owner live v1.40.1 evidence confirms authentication and invoice creation, followed by a deterministic `HTTP 400` response from the explicit invoice-email operation with provider message `Not allowed to send mail`. The endpoint and `to`/`cc` request shape remain unchanged because they already match the current documented post-create email operation. v1.40.2 does not bypass the provider rejection or create a second invoice; it additionally emits `CODE 400` in provider Live Logs while the durable ledger continues to retain `HTTP_400`.

This is a provider-side API mail permission/capability blocker. Manual dashboard email capability is not treated as proof that the API credential/business is allowed to invoke API mail. P11 remains LIVE ACCEPTANCE PENDING until Refrens permits the API mail operation and a controlled recipient mailbox receives the invoice.
