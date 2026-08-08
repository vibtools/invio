# Provider Guide

Providers are manifest-based plugins. Bundled packages appear on **Providers** as Available until installed. Installed providers become selectable in Accounts and Tasks. **Uninstall** removes the local installed manifest but keeps a bundled package available for reinstall.

## Stripe

Credential: secret/restricted key. Modes: Test and Live.

The built-in runtime implements customer lookup/create, draft invoice creation, invoice items, finalize, send-invoice, deterministic idempotency keys, stable multi-account assignment, and failed-recipient retry state. Template currency is converted to Stripe's lowercase API code and monetary values are converted to provider minor-unit rules.

## Refrens

Credentials: API Base URL, URL Key, App ID, App Secret.

The built-in runtime implements app-secret authentication, invoice payload construction, invoice creation, and the documented create-time email-delivery payload. Refrens requires `billedTo.name` and `billedTo.country`; the approved Invio Customer List currently supplies email only. Invio does not invent billing country, so normal Refrens task execution is blocked before network invoice creation until that required data is available through an owner-approved customer-data extension.

## External providers

The existing `register_task_runner(provider_id, runner)` extension point remains available. Loading a manifest alone declares provider metadata; executable behavior still requires a corresponding runner/adapter.

## Visibility

Only installed providers are exposed to Accounts/Tasks. Existing in-memory accounts/tasks are not silently deleted when a provider is uninstalled.
