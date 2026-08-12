## v1.0.0.1.49.2 host compatibility note

`onboarding.interface_version = 1` remains optional. The host UI must treat a missing Easy Onboarding runtime capability as unsupported rather than requiring it from Browser-OAuth-only integrations. Manifest schema, ownership values, Browser OAuth v1, External Provider Adapter v1 and provider Task execution contracts are unchanged.

# Provider Manifest Contract

## v1.0.0.1.41.1 UI resource boundary

The Providers Page logo polish does **not** add a provider-manifest icon/logo field. Current built-in/Odoo card logos are host-owned packaged UI resources under `assets/icons/providers/`. P13 manifest schema, executable-adapter declaration and trust semantics are unchanged.

Provider manifests are validated JSON files describing provider identity, credentials, account modes, and declared capabilities. Manifest loading itself does not execute provider code.

## Schema

```json
{
  "id": "provider-id",
  "name": "Provider Name",
  "version": "1.0.0",
  "description": "Provider description",
  "credential_fields": [
    {
      "key": "secret_key",
      "label": "Secret key",
      "kind": "password",
      "required": true,
      "placeholder": "credential placeholder"
    }
  ],
  "account_modes": ["Test", "Live"],
  "capabilities": ["invoice", "send_invoice", "api_test"]
}
```

## Rules

- `id` must use lowercase letters, digits, hyphens, or underscores.
- `name` and `version` are required.
- Credential field `kind` must be `text` or `password`.
- A provider is selectable by Accounts and Tasks only when its validated manifest exists in `providers/registry`.
- `ProviderManager.uninstall(provider_id)` removes only the installed registry manifest after validated lookup; it does not delete the packaged provider manifest or current in-memory domain data.
- Provider execution is supplied separately through the existing task-runner boundary; loading a manifest alone never executes provider code.
- `ProviderManifestError` is part of the public `src.core.provider_manager` package surface so UI code can safely catch manifest validation/install errors.

## Current packaged manifests

- `stripe` `v1.0.0`: `secret_key`; modes `Test`, `Live`.
- `refrens` `v1.0.3`: `base_url`, `url_key`, `app_id`, `app_secret`; mode `Default`.

## Execution binding in v1.0.0.1.3

Manifest installation and executable provider behavior remain separate concerns. `MainWindow` first checks the existing explicitly registered task-runner extension point; when none is registered, packaged Stripe/Refrens behavior is resolved by `src.core.provider_runtime.ProviderRuntime`.

A manifest capability therefore describes supported intent but does not make arbitrary external provider code executable by itself. Custom/external providers still require an owner-approved runner implementation.


## Executable API-test capability

A manifest capability named `api_test` is declarative metadata only. In `v1.0.0.1.6`, Add Account treats API Test as available only when `ProviderRuntime.supports_api_test(provider_id)` confirms an executable built-in adapter. A loaded manifest alone cannot turn required-field validation into a successful provider verification.

## P06 manifest/runtime reconciliation

A manifest capability remains a **declaration**, not proof of executable code. P06 compares packaged-ID installed manifests with the canonical packaged manifest across execution-relevant fields: provider ID, ordered credential key/kind/required contract, account modes, and declared capabilities. Display-only name/version/description differences do not define the runtime binding.

The packaged IDs `stripe`, `refrens`, and `agiled` are reserved. `ProviderManager.load_external()` rejects external manifests using a packaged ID rather than overwriting `providers/registry/<id>.json`. Existing conflicting packaged-ID registry state is preserved on disk but Account/Test/Task operations fail closed until the owner explicitly uninstalls/reinstalls the packaged provider.

Current executable capabilities are reported separately from declared capabilities. Stripe currently executes `invoice`, `send_invoice`, and `api_test`; Refrens currently executes `api_test` only because its normal Task pipeline remains P11 scope. External manifests do not gain executable capability from declaration alone; the historical injected task-runner API remains the only existing external execution boundary until P13.

## v1.0.0.1.18 P06 verification correction

Packaged `stripe` and `refrens` manifests are now checked against an independent hard-coded executable credential/mode/capability contract as well as the installed registry copy. This prevents a modified packaged manifest from validating a matching modified registry manifest against itself. The comparison still ignores display-only name/version/description fields.

Provider cards render the declaration from the actual installed registry manifest when a packaged ID is installed. Effective runtime capabilities are shown only when that installed declaration also matches the packaged and hard-coded executable contract. Existing external provider IDs and the historical injected task-runner boundary remain unchanged.

## Packaged Runtime Binding in v1.0.0.1.21

A `provider.json` manifest remains metadata and installation state; it is **not executable code**. For packaged built-in IDs, Invio now compares execution-relevant manifest fields against the corresponding `ProviderAdapterContract` registry entry. The registry also defines effective executable capabilities and handler bindings. A manifest may declare a capability while the runtime exposes none; UI/preflight must use the effective executable capability.

Current packaged IDs are `stripe`, `refrens`, and `agiled`. Agiled declares invoice/send/API-test product intent in its package, but its adapter exposes zero executable capabilities until the current API contract is authoritative. Dynamic executable loading for arbitrary external manifests is not implemented in this release.

## v1.0.0.1.22 Verification Note

The packaged-manifest/runtime rules introduced in `v1.0.0.1.21` are unchanged. Verification now explicitly covers Agiled install/uninstall through `ProviderManager`, runtime handler binding integrity for executable packaged providers, and the absence of an Agiled executable handler. A declared Agiled capability still does not become executable capability.

## P13 runtime_adapter block

External manifests may optionally declare:

```json
"runtime_adapter": {
  "interface_version": 1,
  "adapter_version": "1.0.0",
  "entrypoint": "create_adapter"
}
```

The source bundle must contain fixed sibling `adapter.py`. Invio stages both files, validates the staged bytes before registry replacement, rejects validation-time staged-byte mutation, and validates adapter import plus `create_adapter()` without allowing a persistent `sys.path` change. The adapter must report the same provider ID and adapter version, expose interface version 1, return a `ProviderCapabilityProfile` whose executable capabilities exactly match the manifest declaration, and provide required API-Test/Task callables. Sending providers must also expose executable `api_test`, whose success requires a host-managed `SAFE_READ`. Omitting `runtime_adapter` preserves manifest-only loading but grants no executable capability.


## Bundled external provider source — Odoo v1.0.0

Invio v1.0.0.1.40.2 ships a validated external P13 bundle under `providers/plugins/odoo/`. This directory is intentionally **not** part of `providers/packages/`; therefore the `odoo` provider ID is not reserved as a packaged provider and the bundle is not auto-installed. Its `provider.json` + sibling `adapter.py` continue to use external adapter interface v1 and the existing explicit trusted-code installation path.

## Browser OAuth declaration (v1.0.0.1.49.1)

An executable external provider may opt into host browser authorization with:

```json
"browser_auth": {
  "interface_version": 1
}
```

Rules:
- `runtime_adapter` is mandatory when `browser_auth` is present.
- Browser OAuth interface version must be `1`.
- The adapter must expose a valid `BrowserOAuthProfile`, `build_oauth_authorization_url(context)`, and `complete_oauth_authorization(context)`.
- The profile defines exactly one redirect source: a fixed `redirect_uri` or a `redirect_uri_credential_key`.
- Returned credential updates are restricted to manifest-declared credential keys; access-token persistence is rejected by the host.
- This declaration is optional and does not alter the External Provider Adapter v1 task interface.

## Provider Easy Onboarding V1 — v1.0.0.1.49.1

Trusted executable external providers may optionally declare:

```json
"onboarding": {
  "interface_version": 1
}
```

`runtime_adapter` is required. The adapter must expose `onboarding_profile: ProviderOnboardingProfile` and `prepare_account(context) -> ExternalOnboardingResult`. This contract is additive to Browser OAuth and External Provider Adapter v1.

Credential fields may also declare `ownership`: `user_required`, `user_choice`, `generated`, `discovered`, or `managed`. Omitted ownership remains `user_required` so old provider manifests preserve their existing UI. Quick Connect shows only `user_required` fields by default; Advanced / Manual Setup exposes the complete manifest-declared field set. Optional `choices` on a text credential field provide friendly labels while storing the exact machine value, for example a Zoho region label mapped to its Accounts server URL.

`prepare_account()` receives protected bootstrap credentials and a host `request()` function. Onboarding requests must use absolute HTTPS. `SAFE_READ` may retry transient failures. `IDEMPOTENT_MUTATION` may retry only when the provider exposes a stable idempotency primitive and the adapter declares its stable reference. `NON_IDEMPOTENT_MUTATION` is single-attempt; providers must reconcile on the next onboarding run before creating again. Returned credential keys and choice targets must already be declared in the manifest. The host rejects attempted access-token persistence.

The contract intentionally does not prescribe provider business objects. A provider may discover an organization/tenant/company/location, return friendly choices, or bootstrap a narrowly required invoice resource. Provider-specific accounting or legal policy must remain fail-closed rather than guessed.
