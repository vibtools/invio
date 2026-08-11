# Patch Manifest — Invio v1.0.0.1.47.0

## Identity

- Parent baseline: `Invio v1.0.0.1.46.0`
- Candidate: `Invio v1.0.0.1.47.0`
- Patch type: replace-ready project-root delta
- Scope: approved Vib Tools Desktop Design System UI/UX refinement only

## Scope summary

- one global custom main title/header system; duplicate legacy header removed from presentation
- grouped compact sidebar with packaged SVG navigation icons
- standardized app-owned dialog shell/title/footer/modal overlay and inline status presentation
- centralized compact visual states/tokens/icons
- Accounts empty-state visual cleanup
- package/distribution resource contracts synchronized
- required version/docs/tests synchronized

## Explicit preservation

No provider/business/storage/task workflow changes. No database migration. No dependency addition. No page/feature rename. Existing data-grid search/filter/pagination and all existing columns are preserved.

## Delta inventory

Final sealed delta inventory:

- Added: **21**
- Modified: **37**
- Removed: **0**
- Total delta paths: **58**
- `SHA256SUMS.txt`: **57** payload entries (all delta payload paths except the checksum manifest itself)

No baseline file is removed.

## Verification

- Targeted UI/resource suite: `78/78 PASS`
- Repository/version/distribution suite: `74/74 PASS`
- Exact second-cycle truthfulness assertion: `1/1 PASS`
- Final full audit: `428/428 PASS`
- Wheel content audit: PASS
- All 20 `required_runtime_resources()` present in actual wheel
- Final ZIP integrity: PASS
- Exact parent-baseline + delta overlay reconstruction: PASS (0 missing / 0 extra / 0 byte mismatch)
