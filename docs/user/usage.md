# User Guide

## 1. Dashboard

Dashboard shows installed providers, accounts, templates, customer-email count, task activity, account usage, and next setup/action. P02-restored state appears automatically after startup.

## 2. Providers

Install Stripe/Refrens or load an approved external manifest. Provider install/uninstall behavior is unchanged by P02.

## 3. Accounts

Open **Accounts** to Add, Edit, Re-test, or Delete a provider account. Add/Edit require a successful real API Test before commit. Edit is blocked while an account is assigned to an open Task. Re-test checks the current protected credentials without changing them and records the latest UTC test time plus a safe failure summary. Delete is blocked while a Task still references the account.

If a provider is uninstalled, its existing accounts remain visible under **Not Installed** and are not deleted. Edit/Re-test require reinstalling the provider; Delete remains available when the account is not Task-protected. Credentials remain in the approved OS-protected keyring and are never displayed.

If protected credentials cannot be safely saved or restored, the Account is not Task-ready. A missing protected credential restores and durably records the Account as **Not Verified**; restoring the secret later does not make the Account executable until a real Re-test succeeds.

## 4. Invoice Templates

Create reusable invoice content. Templates are now restart-durable. Customer/billing/shipping/payment identity data remains outside templates.

## 5. Customer Lists

Create independent named lists and import CSV, TSV, XLSX, XLSM, or TXT email data. Lists and email ordering are durable across restart.

## 6. Tasks

Choose Provider, Verified Account(s), Invoice Template, and Customer List. Tasks and account reservations survive restart. A Task that was actively Running/Paused/Stopping when the app ended is recovered as **Stopped** and is never auto-resumed.

Existing Start/Pause/Resume/Stop/Retry Failed/Close behavior otherwise remains unchanged.

## 7. Reports and Live Logs

Reports use the restored Task state. Live Logs remain current-session display data; P02 does not add durable log storage or recipient-level delivery records.

## 8. Settings

Settings remain separate non-sensitive JSON preferences. Provider credentials are never written into `settings.json`.
