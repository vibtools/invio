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
