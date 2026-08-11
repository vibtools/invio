## v1.0.0.1.48.8 — Canonical Status Column Runtime Correction

Accounts Status-column sizing now follows the canonical status badge's real Qt size requirement. The existing one-badge renderer and visual palette are unchanged.

## v1.0.0.1.48.7 — Global Status Badge Rendering & Table Cell Alignment

Status presentation is now centralized across shared UI consumers. Table status cells show one badge only, preserve raw status metadata, remain vertically centered, and use the established success/warning/danger/neutral palette.

## v1.0.0.1.48.6 — Accounts Compact Table / Action UI Correction

The v1.48.5 flat Accounts structure is retained. Column balance is corrected, Status/Action remain compact, Accounts-only semantic colors use success `#22C55E`, warning `#FCD34D`, danger `#F87171` and primary `#2563EB`, and the existing row menu is bounded to the Invio-window/current-screen safe region. Global tokens and account workflows remain unchanged.

## v1.0.0.1.48.5 — Accounts Flat Table Scope

The Accounts page now uses a scalable flat list rather than expandable provider groups. The approved compact toolbar, semantic status presentation, pagination and row action menu are implemented without changing the global design system or backend account workflows.

## v1.0.0.1.48.4 — New Task Modal Scope

Only the Tasks-page New Task modal is reflowed to the owner-approved compact layout. Existing design tokens, custom dialog chrome/shadow and all other pages remain frozen.

# Desktop UI Baseline

Invio uses the frozen Vib Tools Step-40J shell, colors, geometry, surfaces, navigation and compact control treatment.

Current pages in `v1.0.0.1.28` are Dashboard, Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, and Settings. P08 and its v1.0.0.1.24 verification correction add no page or layout change.

Release history relevant to the current UI:

- `v1.0.0.1`: official dark sidebar and Providers plugin-card correction.
- `v1.0.0.1.1`: persistent Settings surface.
- `v1.0.0.1.2`: provider Uninstall and compact application-owned dialogs.
- `v1.0.0.1.3`: Dashboard; compact Invoice Template editor; Settings typography/checkmarks; compact Live Logs and Reports based on supplied Vib Tools references.
- `v1.0.0.1.4`: corrected dark scroll/content surfaces in Settings and Invoice Template, repaired compact template spacing, and changed Currency to bounded type-to-search completion.
- `v1.0.0.1.5`: repaired Invoice Template card/form geometry so wrapped notes and controls retain minimum content height and no longer overlap inside the compact scroll area.
- `v1.0.0.1.6`: kept the existing visual design and added real non-blocking Add Account API Test status/availability behavior plus verified-account selection gating.

The core Step-40J tokens, provider/account reservation behavior, and one-QThread-per-active-task execution boundary remain preserved.

- `v1.0.0.1.7`: no UI redesign; re-verified the P01 Add Account API-test UI and corrected stale shipped Refrens installed-manifest presentation so no pre-production marker is shown from the supplied baseline state.

- `v1.0.0.1.8`: no UI redesign; P02 restores durable application state into the existing pages before the shell is shown.
- `v1.0.0.1.9`: no UI redesign; P02 verification correction is backend/recovery-only, with release markers synchronized.

- `v1.0.0.1.10`: P03 adds lifecycle actions to the existing Accounts page only; page inventory and shared design system remain unchanged.
- `v1.0.0.1.11`: no functional UI redesign; P03 verification correction is persistence/recovery-only, with release markers synchronized.
- `v1.0.0.1.12`: P04 updates only the existing Customer Lists page to show Email/Name/Country and customer-aware import summaries; no new page or shared design-system change.

- `v1.0.0.1.13`: no UI redesign; P04 verification restores the unrelated Dashboard customer metric label to its pre-P04 wording while keeping the approved Customer Lists Email/Name/Country UI unchanged.
- `v1.0.0.1.14`: no UI/UX change; the release is limited to the Windows operational-storage migration backup handle lifecycle plus version metadata.

## v1.0.0.1.17 P06 UI note

No new page or UI redesign is introduced. The existing Providers cards now distinguish manifest-declared capabilities from current executable runtime capabilities, while New Task/Start/Retry surface precise preflight correction messages through the existing message-dialog workflow.

## v1.0.0.1.19 P07 UI contract

No new page or button inventory is introduced. The existing Task card is state-driven: Start is available only for pristine Ready; on a safe Stopped current-session Task the same Start control is relabeled **Resume Remaining**; Retry Failed is available only for a safe exact Failed set; Completed exposes no resend action. Layout, tokens, styles, and unrelated pages remain unchanged.
- `v1.0.0.1.19`: no page inventory or shared design-system change; P07 makes existing Task controls state-deterministic and relabels the existing Start control to Resume Remaining for a safe Stopped continuation.

## v1.0.0.1.20 P07 control-state correction

No page, button inventory, token, style or layout changes. Existing Pause/Resume/Stop controls additionally depend on an active Task worker, and safe-empty continuation tooltips/messages now say that no recipients remain rather than describing the set as unavailable.

## v1.0.0.1.22 UI verification

No UI/UX layout or workflow change is introduced. Source-contract verification confirms the Providers page remains manifest-driven, runtime capability display remains effective-capability based, and Add Account continues to gate persistence/Task readiness on an executable API-test adapter.


P09 adds no page, dialog, layout, control or visual redesign. Scheduling/health feedback uses existing Task status and Live Logs surfaces only.


`v1.0.0.1.26` is CI/repository-contract verification only and introduces no UI page, layout, control, style, workflow or UX change.

## v1.0.0.1.27 P10 UI boundary

P10 adds no page, sidebar item, Settings control, report surface or design-token change. Existing Task controls use the durable delivery summary after restart so Resume Remaining / Retry Failed can be available when exact P10 evidence permits it. Existing Live Logs/status messaging may describe durable recovery or Uncertain outcomes; page inventory and layout remain unchanged.

## v1.0.0.1.28 P10 verification UI boundary

No page, widget, layout, navigation or Settings change is introduced. Existing Tasks/Live Logs status behavior consumes the corrected durable P10 summary only.
