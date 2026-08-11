# Accounts — Flat Account List

As of `v1.0.0.1.48.6`, Accounts retain the v1.48.5 flat list with a compact balanced table. `ACCOUNT` and `PROVIDER` share available width; `STATUS` and `ACTION` remain compact. The row `⋯` menu uses the existing Edit/Re-test/Delete callbacks and is positioned inside the safe intersection of the Invio window and current screen.

- **Search** keeps the existing account/provider/status/mode/verification/task/credential matching behavior.
- **Provider** and **Status** filters keep their existing semantics.
- **Rows** and pagination are unchanged.
- Status presentation is Accounts-scoped: success uses existing `#22C55E`, warning `#FCD34D`, danger `#F87171`, and primary interaction `#2563EB`.
- The `ACTION` header is fully visible and every 30x24 `⋯` control remains centered inside its row cell.
- The popup opens inward from the action control and falls back above the row when bottom space is insufficient.

No API, credential, provider-runtime, task-reservation, persistence, business, global token, or data-contract behavior changes are introduced.
