# User Guide

## 1. Dashboard

Dashboard shows current Invio state only: installed providers, accounts, templates, customer-email count, task activity, account usage and the next setup/action. Use **New Task** when prerequisites are ready.

## 2. Providers

Open **Providers**, then Install Stripe/Refrens or load an approved external manifest. Uninstall removes the installed registration; bundled providers remain available to reinstall.

## 3. Accounts

Open **Accounts**, choose **Add Account**, select an installed provider/mode and enter the provider-defined credentials. Run **API Test**. Stripe/Refrens verification performs real provider connection/permission requests on a background `QThread`; only a successful test creates a current-session `Verified` account. Providers without an executable API-test adapter show API Test as unavailable. Accounts are grouped by provider, and an account reserved by an open task cannot be assigned to another task.

## 4. Invoice Templates

Create reusable invoice content. The compact editor includes title/subtitle/type, due period, uppercase currency, invoice note, customer note, footer, terms, provider options, and line items with optional tax rate. Do not put customer/billing/shipping/payment details in a template.

## 5. Customer Lists

Create independent named lists and import email data from CSV, TSV, XLSX, XLSM, or TXT. Each list deduplicates its own email addresses.

## 6. Tasks

Choose **New Task** and select Provider, **Verified** Account(s), Invoice Template, and Customer List. Unverified accounts are disabled and backend Task creation/Start/Retry also fail closed if verification is missing. Start uses the provider execution layer in a task-owned thread. Pause/Resume/Stop remain per task. **Retry Failed** retries failed Stripe recipients retained by the provider runtime. Close releases the accounts.

Stripe can create/finalize/send invoices with the built-in runtime. Refrens task execution currently blocks before creation because Refrens requires customer country while Customer Lists contain email only; Invio does not guess that billing data.

## 7. Reports and Live Logs

Reports use a compact table and include the assigned invoice template. Export remains CSV. Live Logs has compact Save Logs/Clear Logs actions and displays the current auto-scroll state. Stripe-style secret/restricted key patterns remain masked.

## 8. Settings

Settings controls startup/window, confirmations, Live Logs, and file locations. Dashboard can be selected as a startup page, but Accounts remains the default. Checked options display an explicit checkmark. **Save Changes** validates and persists preferences; credentials are never stored in the settings JSON.
