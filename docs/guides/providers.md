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

At restart, Account metadata is restored from SQLite and credentials are retrieved from protected storage. Missing/unavailable credentials downgrade the Account to **Not Verified**, and that fail-closed health state is persisted before startup completes; the event is logged without secret values.

## Stripe

Credential: secret/restricted key. Modes: Test and Live. The existing built-in runtime remains unchanged by P02.

## Refrens

Credentials: API Base URL, URL Key, App ID, App Secret. P02 protects the credential dictionary. P04 Customer Lists can now store explicit name/country data, but Refrens production Task execution remains disabled until P11.

## External Providers

Loading a manifest alone declares provider metadata; executable behavior still requires a corresponding built-in/injected runner. P02 does not create a new external runtime-plugin system.


## v1.0.0.1.11 P03 persistence-safety correction

Migration backups are WAL-aware, credential-loss `Not Verified` recovery is durable, and Account Edit stages a durable fail-closed state before protected credentials are replaced. Provider install/uninstall behavior and API verification contracts are otherwise unchanged.


## v1.0.0.1.12 P04 customer data boundary

Provider manifests and credential fields are unchanged. Customer Lists can carry explicit optional name/country data for provider contracts that require it. Stripe continues using email-only customer lookup/create semantics. Refrens Task execution remains blocked until P11; P04 does not activate it.

## v1.0.0.1.13 P04 verification correction

Explicit country metadata is constrained to two ASCII alphabetic characters before it can satisfy the provider-neutral customer contract or Refrens payload helper. This does not enable Refrens Task sending; the P11 gate remains unchanged.

## P05 Task snapshot provider boundary

P05 stores the Task provider ID and ordered Account IDs as execution basis, but it does **not** copy provider credentials into the Task snapshot. At Start/Retry, existing P03 provider-install and Account `Verified` gates still run, and credentials are resolved from protected Account state. Provider manifests, provider IDs, credential fields and Stripe/Refrens send contracts are unchanged by P05.

## P06 capability and endpoint safety

The Providers page now shows **Declared capabilities** from the installed manifest and **Runtime capabilities** from Invio's current executable adapter boundary. This prevents a manifest declaration from being mistaken for runnable behavior.

Packaged provider IDs are reserved against external-manifest collision. If an installed `stripe`/`refrens` manifest no longer matches the bundled execution-relevant credential/mode/capability contract, Invio fails closed and asks the user to uninstall/reinstall the packaged provider; it does not silently rewrite the registry.

Before Task creation and Start/Retry, P06 checks Account provider identity, `Verified` status, recorded successful verification timestamp, empty verification error, declared mode, and required credential presence. Stripe also rechecks key-format/Test-Live consistency locally. This preflight does not perform an automatic network Re-test.

Refrens API credentials are sent only to `https://api.refrens.com`; host aliases, deceptive subdomains, URL credentials, custom path/query/fragment values, or HTTP are rejected before the authentication payload is constructed. Normal Refrens Task sending remains disabled until P11.

## v1.0.0.1.18 P06 verification correction

P06 verification now fails closed if a packaged built-in manifest itself drifts from the hard-coded Stripe/Refrens executable credential, mode, or capability contract. Providers cards show the actual installed declaration and suppress effective built-in runtime capability when that declaration is inconsistent.

The trusted Refrens endpoint is exact: `https://api.refrens.com` (an optional trailing `/` is normalized). Explicit ports, including `:443`, are rejected together with alternate hosts, embedded credentials, custom paths, query strings, fragments, and HTTP. Refrens Task sending remains P11 scope.

## v1.0.0.1.19 P07 runner continuation boundary

P07 does not change packaged provider manifests, P06 capability/preflight rules, or the public `register_task_runner(provider_id, runner)` registration API. Built-in Stripe can expose exact current-session failed/pending recipient sets for safe Retry Failed / Resume Remaining. An injected/external runner callback does not expose such a subset, so P07 allows its existing first-run path but fail-closes Retry/Resume continuation instead of rerunning the full callback. A richer executable external-provider continuation contract remains P13.

## v1.0.0.1.20 P07 verification boundary

Provider manifests, P06 preflight, Stripe/Refrens send contracts and the injected-runner API are unchanged. The P07 correction is limited to Task terminal/control integration and continuation messaging; it does not add provider retries, cancellation, delivery ledgers or external-provider continuation capability.
