# PATCH MANIFEST — Invio v1.0.0.1.49.7

## Official frozen parent

- Parent: `Invio v1.0.0.1.49.6`
- Parent Git commit: `7ec5ea38c620af26430d862aba5373a903b95bff`
- Scope: `CI / P14 release-payload audit correction` only
- Target: `Invio v1.0.0.1.49.7`

## Verified root cause

GitHub Actions Windows job `95552861559` proved that full tests, OneDir startup, protected credential storage, native Windows TLS, WiX MSI construction and MSI install/run/uninstall all succeeded. Final release assembly failed because `scripts/test/p14_distribution_audit.py` incorrectly required `Invio/truststore/__init__.py`. Nuitka had compiled `truststore` into the working executable distribution, so the source `.py` path was not a stable runtime artifact contract. The unit fixture hid the defect by fabricating that source path.

## Functional correction

1. Remove the unstable `Invio/truststore/__init__.py` source-layout requirement from the portable audit.
2. Remove the same fabricated path from the synthetic P14 distribution fixture.
3. Add regression coverage proving the release audit relies on the existing compiled OneDir/MSI native-TLS smoke gates instead of Python source layout.
4. Synchronize application/PE/MSI/wheel identity to v1.0.0.1.49.7.
5. Synchronize required public release documentation/checksum records.

## Delta inventory

- Added files: 2
- Modified files: 20
- Removed files: 0
- Total delta files: 22
- Layout: direct project-root overlay; no wrapper directory

`SHA256SUMS.txt` is regenerated after this manifest and covers the release-critical baseline set plus every v1.49.7 delta file, excluding itself.

## Frozen boundaries

Phase 1 and Phase 2 runtime behavior remains unchanged. No provider/API/send logic, Odoo v1.0.1 adapter behavior, Task/WorkerManager/state-machine/storage schema, CredentialStore, OAuth/Easy Onboarding, IVX/provider lifecycle, Settings, retry/backoff/timeout/rate/delay controls, Dynamic Tags, application page/layout behavior, or WiX/MSI architecture is changed.

## Acceptance gates

- Targeted P14 distribution tests pass.
- Complete repository audit passes once after the correction.
- Root release checksum manifest is synchronized.
- Parent + delta reconstruction is exact.
- GitHub Windows build must progress through the previously failing release-payload audit and artifact upload after push.
