# Provider Guide

## v1.0.0.1.41 compact Providers page

The Providers page now presents the same provider manifests/runtime truth in equal-height 220px cards. Cards use a 32x32 neutral initial placeholder, title/version/status header, three-line description, compact effective-runtime capability chips, one runtime/credential line and a bottom-anchored Install/Uninstall action. The grid reflows between 2 and 4 columns using a 280px minimum card width. This is a UI-only representation change: Load Provider trust handling, packaged install, external adapter validation and uninstall semantics are unchanged.

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

## v1.0.0.1.21 Packaged Adapter Registry and Agiled

Packaged provider execution is now bound through one internal registry rather than independent provider-ID maps. This does not make `Load Provider` execute arbitrary code: external manifests remain metadata-only unless the existing injected runner API is supplied by application code.

Agiled is bundled with one required protected credential, `API Key`. It is intentionally shown as non-executable because the accessible current Agiled materials do not provide one internally consistent authoritative base URL/authentication/invoice-send contract. API Test and Task execution therefore stop before network transport. Do not interpret package installation as live Agiled readiness.

## v1.0.0.1.22 Verification Note

Agiled installation continues to use the normal Providers workflow. The package remains visible/installable, but Add Account cannot become Task-ready because API Test has no executable Agiled handler. This is the intended fail-closed behavior, not a demo success path. Stripe/Refrens behavior is unchanged.

## P10 provider-operation evidence

P10 does not change provider manifests or enable Refrens/Agiled Task execution. For the existing supported Stripe Task path, ProviderRuntime now persists write-ahead operation evidence and the existing Task-derived idempotency key before transport, then stores safe provider references/outcomes. The external injected-runner API remains first-run compatible but does not gain a fabricated stage-level P10 contract; its continuation remains fail-closed until the separately approved external provider architecture phase.

## Refrens Task execution - v1.0.0.1.29 candidate

The built-in Refrens adapter exposes API Test, invoice and send-invoice Task capabilities in the P11 implementation candidate. Credentials remain URL Key, App ID and App Secret with canonical API Base URL `https://api.refrens.com`. Invio requires explicit customer email/name/country, blocks India under the current customer model, uses 1 request/second/account internal safety pacing, retries only authentication, and records invoice-create/email as a write-ahead P10 operation. The candidate remains live-acceptance pending.

## External executable adapter bundles (P13)

An external executable bundle contains `provider.json` and a fixed sibling `adapter.py`. The manifest declares `runtime_adapter.interface_version`, `adapter_version`, and the fixed `create_adapter` entrypoint. Invio validates staged adapter bytes before atomic installation, rejects validation-time byte mutation, forbids packaged provider IDs, contains adapter import/entrypoint failures, restores/rejects persistent `sys.path` changes, and separates declared capabilities from executable runtime capabilities. Executable Python is trusted in-process code, not sandboxed code; no remote download or dependency auto-installation occurs.


P13 API Test is not allowed to self-certify: a validated external adapter must complete at least one successful host-managed `SAFE_READ` before the existing account-verification workflow can mark the account verified. Task recipient success likewise requires a successful host-managed mutation with an exact matching final stage.

## v1.0.0.1.40.1 Refrens email trigger and Agiled boundary

Refrens Task sending now uses two explicit provider mutations: create the invoice, persist its `_id`, then call the invoice-specific `/email` endpoint. A definitive email-trigger failure can retry the email against the same invoice reference; an ambiguous provider mutation still fails closed.

Agiled remains intentionally fail-closed. The current Agiled product page describes Bearer-token authentication, while the currently published OpenAPI document uses an `api_token` query parameter plus a required `Brand` account-URL header for `/invoices`. Invio's frozen packaged Agiled manifest has only one protected `api_key` field and no approved Brand/base-URL/send contract. Enabling it in this hotfix would require inventing or changing credentials/provider behavior, so no Agiled runtime is added.

## v1.0.0.1.40.2 Agiled current OpenAPI boundary

The owner-supplied current Agiled OpenAPI verifies HTTP Bearer authentication and the safe `GET /public/v1/me` endpoint. Invio therefore enables Agiled API Test using exactly `https://api.agiled.ai/public/v1/me`; only `api_test` is an effective executable capability.

Agiled invoice CRUD is declared by the same OpenAPI, but Task sending remains unavailable because no invoice email/send operation is published and the generic invoice mutation body does not define the invoice-specific field contract. The Documents `/send` endpoint is not reused for invoices. No guessed API behavior is introduced.

## v1.0.0.1.40.2 Refrens live mail rejection

Refrens continues to use the documented explicit post-create invoice `/email` endpoint and durable invoice-ID reuse on Retry Failed. If Refrens returns a deterministic HTTP rejection, Live Logs now include `CODE <status>`. The observed `HTTP 400: Not allowed to send mail` requires provider-side API mail permission/capability resolution and is not treated as a successful send.


## Odoo Provider v1.0.0 — production-certified external plugin

Invio v1.0.0.1.40.2 ships the owner-live-accepted Odoo plugin at `providers/plugins/odoo/`. It remains an external P13 trusted-code bundle and is not automatically installed.

To use it:

1. Open **Providers → Load Provider**.
2. Select `providers/plugins/odoo/provider.json` from the Invio installation/source tree.
3. Review and approve the trusted executable `adapter.py` warning.
4. Add an Odoo account using Base URL, Database, Username/Email and API Key.
5. Run API Test before creating a Task.
6. Begin with one controlled recipient.

Owner live acceptance confirms the plugin can create/post an Odoo invoice and execute invoice email sending. Invio Reports still distinguish provider acceptance from independently confirmed mailbox delivery. For partial/ambiguous non-idempotent operations, inspect Odoo before replay because the frozen P13/P10 uncertainty rules intentionally prevent blind duplicate writes.
