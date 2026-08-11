# Root Cause / Scope Verification — v1.0.0.1.47.0

## Parent baseline
`Invio v1.0.0.1.46.0`.

## Verified presentation causes
1. `MainWindow._build_shell()` rendered both the new `MainTitleBar` and the legacy `WindowHeader`, producing a duplicated global header/context row.
2. App-owned dialogs had custom frameless title bars, but form dialogs still used overlay chrome rather than one layout-owned title/body/footer system.
3. Sidebar navigation still used mixed platform `QStyle` standard icons and no MAIN / OPERATIONS / SETTINGS grouping.
4. Shared controls already had a strong dark baseline but dropdown arrows, state styling, inline feedback, footer treatment and runtime SVG resource checks were not one centralized visual contract.
5. Existing Accounts / Customer Lists / Invoice Templates data/search/filter/pagination workflows were already functional and therefore required preservation, not replacement.

## Scope lock
Approved decisions: target `v1.0.0.1.47.0`; description rule A (no reintroduced page/dialog subtitles); Inline Status primary feedback; responsive columns rule A (do not hide/collapse existing columns).

Provider/runtime/storage/task/customer/invoice/settings business behavior is frozen.

## CI checkout availability
This historical verification record is intentionally allowlisted from the otherwise private `project/` tree because the frozen repository contract reads it during clean GitHub Actions checkout tests. No historical finding or runtime behavior is changed by this tracking correction.
