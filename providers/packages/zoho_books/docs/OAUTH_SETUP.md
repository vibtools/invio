# Zoho Books — OAuth / Easy Onboarding Setup for Invio v1.2.0

## Quick Connect

1. Configure the provider OAuth application and its redirect rules for the intended environment.
2. In **Invio → Accounts → Add Account**, select **Zoho Books**.
3. Supply only the visible Quick Connect inputs:
   - Zoho Region
   - OAuth Client ID
   - OAuth Client Secret
4. Choose **Quick Connect** / the provider Connect action and complete provider login/consent.
5. Invio receives the refresh token and provider account identity, runs provider preparation/discovery, and then runs the real API Test automatically. If more than one valid organization/tenant/location/account is available, choose the friendly provider account shown by Invio.
6. Save the account after it reaches the verified/ready state.

## Automatically managed values

- OAuth Refresh Token
- Zoho Books Organization ID
- Default Item ID (`Invio Service`)

discovers the authorized organization and reuses or creates exactly one active `Invio Service` Service item. Item creation uses the provider settings CREATE permission and is not blindly retried; a later onboarding attempt searches the deterministic name before creating again.

Generated/discovered/managed values remain in Invio's existing protected account credential boundary and are hidden in Quick Connect. They can be inspected/configured only through **Advanced / Manual Setup** when recovery or legacy setup requires it. Access tokens are transient and are not persisted by the host.

## Required scopes / permissions

```text
ZohoBooks.settings.READ,ZohoBooks.settings.CREATE,ZohoBooks.contacts.READ,ZohoBooks.contacts.CREATE,ZohoBooks.invoices.READ,ZohoBooks.invoices.CREATE
```

## Persistent connection

After the account is saved, the provider uses the stored refresh token to obtain short-lived access tokens automatically. When a provider rotates refresh tokens, the newest refresh token is preserved through the existing protected credential workflow. Reconnect is required only when the provider grant cannot be refreshed, is revoked/expired, scopes change, or provider-side security policy requires new consent.

## Backward compatibility

Existing manually configured accounts remain supported. **Advanced / Manual Setup** exposes the full manifest-declared credential set. Easy Onboarding does not alter invoice creation/send semantics.

## Live acceptance

Deterministic tests do not certify a third-party live account. After setup, use a provider account and recipient mailbox you control, verify API Test, create one controlled Task, confirm the provider invoice/send acceptance, and separately confirm recipient mailbox delivery.
