# Data Grid UI Canary — v1.0.0.1.43.0

Run from the exact v1.43.0 candidate source and visually verify:

- Accounts: provider groups are visually distinct, 16px logos render, timestamps are compact, Search/Provider/Status filters and pagination work, and Edit/Re-test/Delete select only real account rows.
- Customer Lists: left list Search/state filter/pagination work; right customer Search/Country filter/pagination work; both tables select full rows.
- Invoice Templates: Search/Currency/Type filters and pagination work; Edit/Delete are fully visible in the 80px Actions column.
- Invoice Template dialog: Invoice Items Search/pagination hides only view rows; Add/Remove/Edit/Save still operate on the complete template item set.
- Reports: both table surfaces match; Search/filters/pagination work; numeric columns align right; semantic statuses remain truthful; hover tooltips expose elided full values.
- New Task: Accounts is a compact four-column table; verified available accounts remain checkable, unverified/reserved accounts remain disabled, selection survives paging/filtering, and the account area never exceeds 250px.
- Providers, Settings, other forms and Task execution behavior remain visually/behaviorally unchanged outside this approved scope.
