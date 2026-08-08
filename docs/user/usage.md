# User Guide

## 1. Providers

Open **Providers** first. Stripe and Refrens are bundled as packaged providers and appear as `Available`. Select **Install** to place the validated manifest in the local provider registry. Only installed/loaded providers appear elsewhere in the application.

The provider cards follow the official Vib Tools Plugin Page visual contract: compact dark cards, version/category-style chip, availability status, provider title/description, capability information, credential-field count, and the existing Install state/action.

## 2. Accounts

Open **Accounts** and choose **Add Account**. Select an installed provider, enter an account label, provider mode, and the provider-defined credential fields.

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
