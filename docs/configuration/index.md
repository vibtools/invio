# Configuration

Invio `v1.0.0.1.2` provides persistent **application settings** for non-sensitive desktop preferences while keeping account credentials and domain state in memory for the active application session.

## Settings page

Open **Settings** and select **Save Changes** after changing preferences. **Restore Defaults** loads the baseline values into the form; select **Save Changes** to persist them.

### Startup & Window

- **Open Invio on**: choose Accounts, Invoice Templates, Customer Lists, Tasks, Providers, Reports, Live Logs, Settings, or **Last page used**.
- **Remember window size and position**: when enabled, Invio stores the normal window geometry on exit and restores it on the next launch if the saved position is on an available screen.

The baseline defaults remain **Accounts** and window-memory **off**, matching `v1.0.0.1` behavior.

### Confirmations

Each confirmation can be controlled independently:

- exit while tasks are running;
- close a task;
- delete an invoice template;
- delete a customer list;
- clear Live Logs.

The first four preserve their previous confirmation behavior by default. Live Logs clearing remains immediate by default, matching the frozen baseline.

### Live Logs

- **Show time on each log entry**: enabled by default.
- **Automatically follow the newest log entry**: enabled by default.
- **Maximum log lines**: `Unlimited` by default. A numeric limit causes Qt to retain only the newest lines in the current session.

Stripe-style secret/restricted keys continue to be masked regardless of these settings.

### File Locations

- **Default file folder**: optional starting directory for provider manifest loading, customer email imports, task-report exports, and log exports.
- **Remember the last folder I used**: when enabled, the most recently used valid directory takes precedence over the default folder for later file dialogs.

Leave the default folder blank to use the operating system's normal file-dialog location.

## Settings storage

Only application preferences and runtime convenience state are stored. The settings file never stores account credential dictionaries or provider secrets.

The default per-user path is:

- Windows: `%APPDATA%\\Vib Tools\\Invio\\settings.json`
- macOS: `~/Library/Application Support/Vib Tools/Invio/settings.json`
- Linux: `$XDG_CONFIG_HOME/Vib Tools/Invio/settings.json`, or `~/.config/Vib Tools/Invio/settings.json` when `XDG_CONFIG_HOME` is not set.

Writes are atomic. If the settings file is unreadable or malformed, Invio falls back to baseline defaults and records a warning in Live Logs instead of failing startup.

## Other runtime configuration

- Packaged provider definitions live under `providers/packages/`.
- Stripe and Refrens are included as packaged manifests.
- Installed provider manifests are copied locally into `providers/registry/` and are intentionally excluded from Git.
- Account credentials remain runtime-only; persistent protected credential storage is not configured.
- Refrens exposes its API Base URL as an account credential field because the supplied reference application stores it per API profile.


## Dialog presentation

Application-owned dialogs use compact responsive sizing based on the current Invio window. This is UI presentation only and is not a user-configurable setting. Native operating-system file/folder picker dialogs are unchanged.
