# Root Cause / Scope Verification — v1.0.0.1.48.0

## Parent baseline
`Invio v1.0.0.1.47.0`.

## Verified root causes
1. `MainTitleBar` and `DialogTitleBar` both used `setContentsMargins(10, 0, 0, 0)`, leaving a **zero right margin** after the Close control.
2. App-owned dialogs used a dark top-level QDialog border but had no dedicated elevated dialog surface or drop-shadow layer, so the popup could visually blend into the similarly colored parent page.
3. The five app-owned form dialogs rendered their window title in `DialogTitleBar` and also rendered a duplicate body `PageTitle` (`Create Customer List`, `Add/Edit Provider Account`, `Re-test Provider Account`, `Invoice Template`, `Create Task`). This **duplicate body PageTitle** caused the title duplication visible in the owner screenshots.

## Scope lock
Only custom Main/Dialog title-bar spacing, popup surface separation, and removal of duplicate dialog-body title labels are approved. Form fields, cards, labels, validation/status, action footers, modal behavior, move/resize handling and all backend/business/runtime behavior remain frozen.

## CI checkout availability
This historical verification record is intentionally allowlisted from the otherwise private `project/` tree because the frozen repository contract reads it during clean GitHub Actions checkout tests. No historical finding or runtime behavior is changed by this tracking correction.
