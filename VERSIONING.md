# Versioning

Invio release versions are controlled by Vib Tools. Every approved update freezes the latest verified release as the next baseline and produces a replace-ready project-root delta.

- `v1.0.0`: frozen source baseline.
- `v1.0.0.1`: official sidebar/provider-card and production-marker correction.
- `v1.0.0.1.1`: persistent user-friendly Settings UI/backend.
- `v1.0.0.1.2`: provider uninstall plus compact application-owned dialogs.
- `v1.0.0.1.3`: invoice-template expansion and provider/task binding, built-in provider runtime, Settings visual fixes, compact Live Logs/Reports, and Dashboard.
- `v1.0.0.1.4`: dark scroll-surface correction for Settings/Invoice Template, compact Invoice Template spacing repair, and bounded type-to-search Currency selection.
- `v1.0.0.1.5`: Invoice Template geometry repair that preserves wrapped-text/control height inside the compact scroll area and removes the faulty card-level maximum-height policy.

Future version changes require a new explicit scope lock. No unapproved feature or architecture change is included in a release delta.
