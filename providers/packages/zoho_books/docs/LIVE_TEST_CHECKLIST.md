# v1.1.0 Browser OAuth acceptance

- [ ] Provider Browser OAuth/PKCE app registration matches `docs/OAUTH_SETUP.md`.
- [ ] `Connect` completes with state/redirect validation and populates the required refresh/account bootstrap fields.
- [ ] API Test passes after the account is saved.
- [ ] Close/reopen Invio and API Test again without browser authorization to prove persistent refresh-token operation.
- [ ] Run a one-recipient invoice Task and confirm provider acceptance and actual mailbox receipt separately.
- [ ] Reconnect/cancel/denied-auth path fails closed without exposing secrets in Live Logs.

# Live Zoho Books Verification Checklist

This checklist intentionally requires real Zoho credentials and a real recipient mailbox. Unit/contract tests cannot certify external delivery.

## Before test

- Use a non-production or explicitly approved Zoho Books organization for the first live run.
- Confirm OAuth scopes listed in `OAUTH_SETUP.md`.
- Confirm the organization ID.
- Create/identify an active Zoho Books Item.
- Either configure its numeric ID as **Default Item ID**, or make the Invio invoice-item description exactly equal the Zoho Item name.
- Use a recipient mailbox you control.

## Invio verification

1. Load `provider.json` through Providers → Load Provider and approve the trusted executable adapter.
2. Add the Zoho Books account.
3. Run **API Test**. Expected: `Zoho Books API connection verified.`
4. Create an Invio customer list with a real test recipient and a non-empty customer name.
5. Create an INVOICE template with:
   - Automatic Tax off
   - line tax 0
   - no custom title/subtitle
   - no footer/customer-note
6. Create and start one Task.
7. Confirm Live Logs show:
   - currency/item resolution
   - customer found/created
   - real Zoho invoice ID
   - Zoho Books email request accepted
8. In Zoho Books, confirm the invoice exists under the configured organization.
9. Confirm the intended recipient address received the Zoho Books invoice email.
10. Confirm Invio Reports retains the provider invoice ID and provider-acceptance evidence without claiming mailbox delivery unless independently evidenced.

## Failure safety

- Do not blindly Retry a recipient reported **Uncertain** after a successful non-idempotent Zoho mutation; Invio intentionally fails closed to avoid duplicate invoices/sends.
- A 429 response indicates Zoho rate limiting; reduce concurrent accounts targeting the same organization and retry only through Invio's permitted continuation path.

## v1.2.0 Easy Onboarding verification note

This bundle additionally declares Invio Easy Onboarding V1. Verify Quick Connect hides generated/discovered/managed fields by default, provider preparation is repeat-safe/fail-closed, automatic API Test runs after preparation, and Advanced / Manual Setup preserves the previous credential path. Production adapter paths remain real API only.
