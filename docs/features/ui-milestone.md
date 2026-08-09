# Desktop UI Baseline

Invio uses the frozen Vib Tools Step-40J shell, colors, geometry, surfaces, navigation and compact control treatment.

Current pages in `v1.0.0.1.26` are Dashboard, Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, and Settings. P08 and its v1.0.0.1.24 verification correction add no page or layout change.

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
