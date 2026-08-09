# Provider Guide

Providers are manifest-based registrations. Bundled packages appear on **Providers** as Available until installed. Installed providers become selectable in Accounts and Tasks. **Uninstall** removes the local installed manifest but keeps a bundled package available for reinstall.

## Real API Verification

Add Account requires an executable provider API-test adapter. Bundled Stripe and Refrens runtimes provide one. API Test runs outside the GUI thread and only a successful test creates a `Verified` Account. Stripe verification enforces selected Test/Live mode; Refrens authenticates and checks invoice-list access.

## P03 Provider/Account Consistency

Uninstall is deterministic: a provider cannot be uninstalled while one of its Tasks has an active worker. With no active worker, uninstall removes only provider installation state; Accounts, protected credentials, Tasks and reservations remain durable. Preserved accounts stay visible as **Not Installed**, and Task Start/Retry is blocked until the provider is installed again.

Account Re-test and Edit require the provider to be installed. Reinstall does not silently delete/recreate the account and does not invent an age-based verification expiry.

## P02 Credential Protection

After successful API Test and account acceptance:

1. provider credential values are written to the approved OS-protected keyring;
2. SQLite receives non-sensitive account metadata plus an opaque credential reference;
3. the Account becomes durable only after both operations succeed.

If the database write fails after a new protected secret is written, Invio performs a compensating protected-store deletion and does not add the account to application state. There is no plaintext fallback.

At restart, Account metadata is restored from SQLite and credentials are retrieved from protected storage. Missing/unavailable credentials downgrade only the runtime account state to **Not Verified** and are logged without secret values.

## Stripe

Credential: secret/restricted key. Modes: Test and Live. The existing built-in runtime remains unchanged by P02.

## Refrens

Credentials: API Base URL, URL Key, App ID, App Secret. P02 protects the credential dictionary but does not change the current required-country Task block.

## External Providers

Loading a manifest alone declares provider metadata; executable behavior still requires a corresponding built-in/injected runner. P02 does not create a new external runtime-plugin system.
