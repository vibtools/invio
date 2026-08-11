# Odoo Provider v1.0.0 — One-Recipient Production Canary

1. Load `providers/plugins/odoo/provider.json` through Providers → Load Provider and approve the trusted adapter.
2. Add an Odoo Account with Base URL, Database, Username / Email and API Key; require API Test PASS.
3. Create one Customer with a controlled mailbox.
4. Use a simple `INVOICE` template, one line item, supported currency, no automatic/line tax, default title and blank subtitle.
5. Create and Start one Odoo Task.
6. Verify Invio `Completed / Success 1 / Failed 0`.
7. Verify the Odoo invoice exists and is Posted.
8. Verify the recipient mailbox received the Odoo invoice email.
9. If Invio reports `Uncertain`, inspect Odoo before any replay.
## v1.0.0.1.41 Providers-page note

The Odoo live-canary workflow is unchanged. In the v1.0.0.1.41 UI candidate, the installed Odoo provider appears in the same Providers workflow using the compact fixed card, neutral `O` initial, effective capability chips, runtime/credential summary, and bottom-anchored Uninstall action. This visual change does not alter Odoo API Test or invoice sending.



## Providers Page note for v1.0.0.1.41.1

The shipped Odoo bundle still uses the same explicit trusted-code Load Provider flow. The Providers Page now shows the packaged Odoo logo, the owner-approved Verified badge after installation, and supports Search providers filtering. This is presentation-only and does not change Odoo API execution.
