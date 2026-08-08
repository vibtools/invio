# Configuration

Invio currently keeps account credentials and domain state in memory for the active application session.

- Packaged provider definitions live under `providers/packages/`.
- Stripe and Refrens are included as packaged manifests.
- Installed provider manifests are copied locally into `providers/registry/` and are intentionally excluded from Git.
- Account credentials are runtime-only; persistent protected credential storage is not configured.
- Refrens exposes its API Base URL as an account credential field because the supplied reference application stores it per API profile.
