# Troubleshooting

## Provider does not appear in Accounts or Tasks

Install it from **Providers**. Bundled packages can be Available without being installed.

## Account cannot be saved after a successful API Test

P02 requires an approved OS-protected credential backend. If protected storage is unavailable/locked/unsupported, Invio fails closed and does not save provider secrets to a plaintext file. Restore the OS credential service and retry Add Account.

## A restored account shows Not Verified

Its non-sensitive metadata was loaded from SQLite but the protected credential entry could not be read or was missing. No plaintext fallback is used. The account remains blocked by the existing P01 Task gates.

## Invio reports an operational-storage startup error

Invio does not silently replace a corrupt, unsupported, or newer `domain.sqlite3`. Keep the database file for forensic/recovery work. Correct the underlying file/storage/version issue before reopening. An existing v0 database is backed up before the supported v0->v1 migration.

## A Task was Running before restart but is now Stopped

Expected P02 behavior. Worker threads do not survive process restart, so `Running`, `Paused`, and `Stopping` tasks are recovered as **Stopped** and are not automatically resumed.

## Account remains reserved after restart

Expected while the owning Task remains open. P02 restores reservations. Close the Task through the normal workflow to release its selected accounts.

## API Test fails or is unavailable

Stripe/Refrens API Test performs real provider connection/permission requests. Correct credentials/mode and retry. Providers without an executable API-test adapter cannot become Task-ready.

## Refrens Task is blocked with `billedTo.country`

Expected. P02 does not change the email-only Customer List contract or guess required billing country.

## Invoice Template dialog does not fit the display

The editor remains compact and internally scrollable; P02 does not change its UI geometry.
