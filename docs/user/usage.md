# User Guide

## 1. Providers

Open **Providers** first. Stripe and Refrens are bundled as packaged providers and appear as `Available`. Select **Install** to place the validated manifest in the local provider registry. After installation, the same card exposes **Uninstall**. Uninstall removes only the registry manifest; bundled provider files and current in-memory account/task data are kept. Only installed/loaded providers appear in Accounts and new Task selection.

The provider cards follow the official Vib Tools Plugin Page visual contract: compact dark cards, version/category-style chip, availability status, provider title/description, capability information, credential-field count, and the Install/Uninstall state and action.

## 2. Accounts

Open **Accounts** and choose **Add Account**. The compact dialog is wider and shorter than the previous layout. Select an installed provider, enter an account label, provider mode, and the provider-defined credential fields. Providers with more than two credential fields automatically use a two-column credential form.

For Stripe, enter the Stripe secret/restricted API key. For Refrens, enter API Base URL, URL Key, App ID, and App Secret.

The existing **API Test** control validates the required credential structure for the current provider integration. Network verification is unavailable unless implemented by that provider integration. Credentials remain in memory for the active application session and are not persisted.

Accounts are displayed under their provider group. If an account is reserved by a task, the assigned task is shown.

## 3. Invoice Templates

Open **Invoice Templates** and create a reusable invoice definition. Templates contain invoice settings and line items only. They do not contain customer, billing, or shipping data.

## 4. Customer Lists

Create multiple named lists. Select a list and upload email data from CSV, TSV, XLSX, XLSM, or TXT. Each list maintains its own unique email set.

## 5. Tasks

Choose **New Task**, then select:

1. Provider
2. One or more available accounts belonging to that provider
3. Customer list

Once the task is created, its selected accounts are reserved. They cannot be selected by another task until the task is closed and those accounts are released.

Task cards include Start, Pause, Resume, Stop, Retry Failed, Close Task, status, progress, and counters. A task starts only when a task runner is registered for its provider. If no runner is registered, the provider is reported as unavailable and no invoice is sent.

## 6. Reports and Logs

Reports summarize current task state and can be exported to CSV. Live Logs contain application/task messages and mask Stripe-style secret-key patterns.


## 7. Settings

Open **Settings** to control existing Invio application behavior without editing configuration files. The page is divided into Startup & Window, Confirmations, Live Logs, and File Locations.

- Choose a fixed start page or **Last page used**.
- Optionally remember the window size and position.
- Turn individual confirmation prompts on or off for active-task exit, closing tasks, deleting invoice templates, deleting customer lists, and clearing Live Logs.
- Choose whether Live Logs show timestamps, follow new entries automatically, and retain an unlimited or limited number of lines.
- Choose a default file folder and optionally remember the last folder used by provider loading, customer import, report export, and log export dialogs.

Select **Save Changes** to validate, persist, and apply the settings. **Restore Defaults** loads the behavior-compatible default values into the page; select **Save Changes** to persist them. Settings are stored locally for the current operating-system user. Account credentials are never written to the application settings file.


## 8. Compact dialogs

Application-owned custom dialogs and Invio message/confirmation boxes use compact sizing relative to the main window. The Invoice Template dialog uses a two-column upper section and the New Task dialog uses a shorter account-list area. Native operating-system file/folder picker windows keep their platform behavior.
