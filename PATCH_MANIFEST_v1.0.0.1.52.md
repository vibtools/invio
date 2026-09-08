# Invio v1.0.0.1.52 Patch Manifest

**Parent baseline:** Invio v1.0.0.1.50.1 @ `5534c82e5d325031e042a7f8c7057d6846c00fae`
**Accepted parent CI:** GitHub Actions run `34226609792` — SUCCESS (669/669 tests PASS, Linux + Windows)

## Scope of this release

- Website-issued RSA license system (`src/core/license/client.py`): activation, local tamper-resistant caching, and periodic server re-validation (revocation propagation via `revalidate_license()`).
- License gate in `ExternalAdapterRegistry.reload_installed()`: unlicensed external providers register as `Unlicensed`.
- `LicenseActivationDialog` and license status UI on the Providers page.
- Online Provider Catalog (`src/core/provider_manager/remote_registry.py`): fetch/download/install providers from invio.vib.tools.
- Providers page redesign: scrollable layout, 3-column grid, Settings-page-matching styling, card-overlap fix.
- Three additional reference provider packages: QuickBooks Online, Zoho Books, Zoho Invoice.
- New `cryptography` dependency; repinned `constraints/ci-linux-py312.txt` transitive `cryptography` version to stay within the declared `<50` range.

## Explicitly frozen

Phase-1 TLS logic, Phase-2 circuit-breaker semantics, Phase-3 sending controls, Phase-4 Dynamic Tags implementation, schema v7, existing provider/Odoo code and manifests, WorkerManager, Task state machine, delivery ledger, Settings behavior, CredentialStore, OAuth/Easy Onboarding, and ProviderManager/IVX validation rules.

## Release mapping

- Application/wheel: `1.0.0.1.52`
- PE: `1.0.1.52`
- MSI: `1.1.52`
- Tag: `v1.0.0.1.52`

## Test evidence

669/669 tests passed locally (`scripts/test/audit.py`) and on GitHub Actions run `34226609792` (both the Linux `test` job and native Windows `windows-test` job).
