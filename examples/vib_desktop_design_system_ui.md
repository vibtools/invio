# v1.0.0.1.47.0 Desktop Visual Canary

Verify on Windows source/compiled builds:

1. Only one global application title bar is visible; the legacy second `VT / Invio / Home / ... / Medium` header is absent.
2. Main title bar shows app icon, `Invio`, current `Home / <Page>` context, `Vib Tools`, and compact minimize/maximize/close controls.
3. Sidebar is grouped under MAIN / OPERATIONS / SETTINGS, uses one SVG icon family, preserves all nine destinations, and shows a compact Vib Tools / Production version footer.
4. Add Account, New Customer List, Invoice Template, New Task and Re-test dialogs use the same dark custom title bar, padded body and separated action footer. No white Windows title bar appears.
5. Modal parent surfaces are subtly dimmed while an app-owned modal is active; only one normal workflow dialog is active at a time.
6. Dialog drag/close/resize (where previously allowed), Esc, Tab navigation and safe primary Enter behavior work.
7. Inputs/dropdowns/buttons retain existing values and workflows; custom dropdown arrows and hover/focus/disabled states are visually consistent.
8. Add Account API Test uses inline progress/success status; failure/critical warnings may still use the existing modal warning path.
9. Accounts, Customer Lists and Invoice Templates keep the existing search/filter/pagination, table columns and operations.
10. Providers, Tasks, Reports, Settings, Live Logs and backend behavior show no functional regression.
