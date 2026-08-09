# User Guide

## 1. Dashboard

Dashboard shows installed providers, accounts, templates, customer-email count, task activity, account usage, and next setup/action. P02-restored state appears automatically after startup.

## 2. Providers

Install Stripe/Refrens or load an approved external manifest. Provider install/uninstall behavior is unchanged by P02.

## 3. Accounts

Open **Accounts**, choose **Add Account**, select provider/mode, enter provider-defined credentials, and run **API Test**. Real verification runs outside the GUI thread. A successful account is stored with non-sensitive metadata in Invio's per-user SQLite database and credentials in the approved OS-protected keyring.

If protected credentials cannot be safely saved, the account is not added. If a previously stored protected credential is unavailable at restart, the account remains visible as **Not Verified** and cannot be used for a Task.

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
