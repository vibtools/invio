# v1.1.0 Browser OAuth acceptance

- [ ] Provider Browser OAuth/PKCE app registration matches `docs/OAUTH_SETUP.md`.
- [ ] `Connect` completes with state/redirect validation and populates the required refresh/account bootstrap fields.
- [ ] API Test passes after the account is saved.
- [ ] Close/reopen Invio and API Test again without browser authorization to prove persistent refresh-token operation.
- [ ] Run a one-recipient invoice Task and confirm provider acceptance and actual mailbox receipt separately.
- [ ] Reconnect/cancel/denied-auth path fails closed without exposing secrets in Live Logs.

# Zoho Invoice — Controlled Live Test Checklist

Use this only after the local plugin tests and Invio API Test pass.

- [ ] Provider bundle loaded and explicitly trusted.
- [ ] Account shows **Verified** after real API Test.
- [ ] Use a dedicated test/sandbox organization when the provider offers one.
- [ ] Use one recipient email address you control.
- [ ] Use a small, unmistakable invoice amount and a unique memo/reference.
- [ ] Customer name/email data satisfies the provider validation gate.
- [ ] Required provider Item/Account/Location mapping is exact.
- [ ] Create exactly one Invio Task with one recipient for the first acceptance run.
- [ ] Verify the provider UI contains exactly one new invoice for that run.
- [ ] Verify Invio records the provider invoice reference and no duplicate mutation occurred.
- [ ] Verify the provider reports the invoice as emailed/published/sent as applicable.
- [ ] Verify the controlled recipient mailbox actually receives the message.
- [ ] Verify Retry/Resume is not used to replay an uncertain non-idempotent mutation.
- [ ] Only after all checks pass, enable normal/bulk operation.

A provider API success/acceptance response is not, by itself, proof that the recipient mailbox delivered the email.

## v1.2.0 Easy Onboarding verification note

This bundle additionally declares Invio Easy Onboarding V1. Verify Quick Connect hides generated/discovered/managed fields by default, provider preparation is repeat-safe/fail-closed, automatic API Test runs after preparation, and Advanced / Manual Setup preserves the previous credential path. Production adapter paths remain real API only.
