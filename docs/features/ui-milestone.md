# Desktop UI Baseline

Invio uses the frozen Vib Tools Step-40J shell, colors, geometry, surfaces, navigation and compact control treatment.

Current pages in `v1.0.0.1.14` are Dashboard, Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, and Settings.

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
