# Accounts — Flat Account List

As of `v1.0.0.1.48.5`, Accounts are presented as one flat list rather than expandable provider groups.

- **Search** matches the existing account/provider/status/mode/verification/task/credential metadata.
- **Provider** and **Status** filters keep the existing filter semantics.
- **Rows** and pagination scale the same in-memory account collection without mutating application data.
- The row **⋯** menu exposes the existing **Edit**, **Re-test**, and **Delete** callbacks.
- If a provider is not installed, the row status is presented as **Not Installed** while the stored account record and credentials remain preserved under the existing backend rules.

No API, credential, provider-runtime, task-reservation or persistence contract changes are introduced by this UI update.
