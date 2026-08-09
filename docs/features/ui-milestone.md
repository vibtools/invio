# Desktop UI Baseline

Invio uses the frozen Vib Tools Step-40J shell, colors, geometry, surfaces, navigation and compact control treatment.

Current pages in `v1.0.0.1.9` are Dashboard, Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, and Settings.

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
