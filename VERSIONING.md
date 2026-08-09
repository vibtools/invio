# Versioning

Invio release versions are controlled by Vib Tools. Every approved update freezes the latest verified release as the next baseline and produces a replace-ready project-root delta.

- `v1.0.0`: frozen source baseline.
- `v1.0.0.1`: official sidebar/provider-card and production-marker correction.
- `v1.0.0.1.1`: persistent user-friendly Settings UI/backend.
- `v1.0.0.1.2`: provider uninstall plus compact application-owned dialogs.
- `v1.0.0.1.3`: invoice-template expansion/provider binding, built-in provider runtime, compact logs/reports, and Dashboard.
- `v1.0.0.1.4`: dark scroll-surface correction, compact Invoice Template spacing repair, and bounded searchable Currency control.
- `v1.0.0.1.5`: Invoice Template geometry/root-cause repair.
- `v1.0.0.1.6`: P01 real non-blocking Stripe/Refrens API verification and verified-account Task gates.
- `v1.0.0.1.7`: P01 verification corrective release and shipped registry/test-boundary correction.
- `v1.0.0.1.8`: P02 durable SQLite domain state, schema/migration/recovery controls, and OS-protected `keyring` provider credentials with no plaintext fallback.
- `v1.0.0.1.9`: P02 verification corrective release; fixes persistence-failure re-entrancy, exact reservation-state recovery validation, and stale P02 roadmap progress metadata.

- `v1.0.0.1.10`: P03 production release; adds reservation-safe account lifecycle, durable verification health, SQLite schema v2, provider-uninstall preservation and Task provider-install execution gates.

Future version changes require a new explicit scope lock. No unapproved feature or architecture change is included in a release delta.
