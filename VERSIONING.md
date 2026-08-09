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
- `v1.0.0.1.11`: P03 verification/corrective release; makes schema-migration backups WAL-aware, persists credential-loss verification downgrades, and hardens cross-store Account Edit recovery to remain fail-closed.

Future version changes require a new explicit scope lock. No unapproved feature or architecture change is included in a release delta.

- `v1.0.0.1.12`: P04 customer data/import release; adds backward-compatible email/name/country customer records, schema v3, structured validation/duplicate handling and customer-aware runtime snapshots without enabling Refrens Task sending.
- `v1.0.0.1.13`: P04 verification/correction release; restores mutable `CustomerList.emails` compatibility, row-numbered existing-list conflicts, ASCII two-letter country validation, malformed-file error containment, and pre-P04 Dashboard label scope fidelity.
- `v1.0.0.1.14`: Windows operational-storage/runtime hotfix; explicitly closes the temporary SQLite migration-backup connection before atomic replacement, preventing the self-inflicted `WinError 32` startup failure while keeping schema v3 and P01-P04 behavior unchanged.

- `v1.0.0.1.15`: P05 immutable Task execution snapshots; schema v4 freezes ordered recipients, copied invoice-template content, provider ID and account-assignment basis at Task creation, uses `Task.id` as the canonical logical run identity, and preserves pre-P05 Tasks as non-executable `LegacyUnavailable` records rather than fabricating historical inputs.
- `v1.0.0.1.16`: P05 forensic verification/correction; rejects post-P05 Tasks without a captured immutable snapshot, validates captured Task progress against its frozen recipient set, and prevents routine Task updates from rewriting the immutable total. Schema remains v4 and production progress remains 5/14.

