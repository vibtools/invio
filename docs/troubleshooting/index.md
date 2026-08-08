# Troubleshooting

## Provider does not appear in Accounts or Tasks

Install it from **Providers**. Bundled packages can be Available without being installed.

## A bundled provider remains on Providers after Uninstall

Expected. Uninstall removes its installed registry copy and returns the bundled provider to Available status so it can be installed again.

## Account cannot be selected for a new task

It is reserved by another open task. Stop/close the owning task to release it.

## New Task says an invoice template is required

Create at least one template first. Every `v1.0.0.1.3` task must bind to an invoice template.

## Stripe task fails

Open Live Logs for the provider response. Common causes include key/mode mismatch, API permissions, unsupported account/currency combinations, automatic-tax configuration, invalid invoice values, or network failure. Failed recipients remain available to **Retry Failed** while the task remains open.

## Refrens task is blocked with `billedTo.country`

This is deliberate data-integrity protection. Refrens requires a customer name and ISO country for invoice creation, while the approved Customer List model currently stores email only. Invio does not guess a billing country and sends no create request in this state.

## Invoice Template dialog does not fit the display

The editor is compact and internally scrollable. Resize the main window if needed; the dialog is bounded relative to the application window.

## Settings checkbox looks unchecked after patching

Confirm `assets/icons/checkmark.svg` and the updated `src/ui/styles.py` are both present. The checked indicator references that bundled asset.

## Settings do not save

Select **Save Changes** and read the feedback. A configured default folder must exist. Invalid/corrupt settings files fall back to defaults rather than preventing startup.

## Reports or Live Logs look different

`v1.0.0.1.3` intentionally applies the approved compact Vib Tools reference layout. Existing report CSV export, log save/clear behavior, masking, and log settings remain.
