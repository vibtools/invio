## Connect a browser-OAuth provider — v1.0.0.1.49.1

1. Install a trusted provider bundle that declares Browser OAuth v1.
2. Open **Accounts > Add Account**, select the provider and mode, and enter the provider's required pre-connect fields.
3. Choose **Connect <Provider>**. Invio opens the system default browser; embedded WebViews are not used.
4. Complete provider login/consent. Loopback callbacks return directly to Invio. Providers that require a production HTTPS redirect can require one-time pasting of the complete callback URL into Invio.
5. If more than one organisation/tenant/location is authorized, select the intended account.
6. Run **API Test** and save the Invio account.
7. Subsequent access-token renewal is automatic through the provider adapter's saved refresh-token workflow. Reconnect only when the provider authorization is revoked/expired or permissions change.

Manual refresh-token/account setup remains available for existing provider bundles and existing saved accounts.

## v1.0.0.1.48.8 Status Column Sizing

The flat Accounts table is unchanged except that the `STATUS` column now sizes to the canonical badge's natural width. This prevents clipping on Windows font/DPI environments while keeping `ACCOUNT`, `PROVIDER`, `ACTION`, search, filters and pagination behavior unchanged.

## v1.0.0.1.48.7 Status Rendering

Accounts retains the v1.48.6 flat compact layout and row actions. The Status column now uses the global shared table-status renderer, so each row displays exactly one centered badge while the raw status is retained only as item metadata/tooltip.

# Accounts — Flat Account List

As of `v1.0.0.1.48.6`, Accounts retain the v1.48.5 flat list with a compact balanced table. `ACCOUNT` and `PROVIDER` share available width; `STATUS` and `ACTION` remain compact. The row `⋯` menu uses the existing Edit/Re-test/Delete callbacks and is positioned inside the safe intersection of the Invio window and current screen.

- **Search** keeps the existing account/provider/status/mode/verification/task/credential matching behavior.
- **Provider** and **Status** filters keep their existing semantics.
- **Rows** and pagination are unchanged.
- Status presentation is Accounts-scoped: success uses existing `#22C55E`, warning `#FCD34D`, danger `#F87171`, and primary interaction `#2563EB`.
- The `ACTION` header is fully visible and every 30x24 `⋯` control remains centered inside its row cell.
- The popup opens inward from the action control and falls back above the row when bottom space is insufficient.

No API, credential, provider-runtime, task-reservation, persistence, business, global token, or data-contract behavior changes are introduced.
