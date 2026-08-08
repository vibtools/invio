# Desktop UI Baseline

The Invio desktop UI baseline contains the requested Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, and Settings pages. It preserves the installed-provider visibility rule, one-account-one-task reservation invariant, and the per-task worker-thread execution boundary.

Release `v1.0.0.1` corrects the sidebar surface and aligns the Providers card presentation with the official Vib Tools Plugin Page design contract. No application feature or provider workflow is removed or replaced by this update.

Release `v1.0.0.1.1` keeps the same page inventory and visual baseline while implementing the existing Settings page as a real persistent preference surface. Only startup/window, confirmation, Live Logs, and file-dialog behavior is configurable; provider, task-thread, account-reservation, and invoice/customer domain contracts remain unchanged.


Release `v1.0.0.1.2` adds the approved provider Uninstall action and compact application-owned modal layouts. It does not alter page inventory, provider credential schemas, task/account domain rules, settings behavior, or the per-task worker-thread boundary.
