# PATCH MANIFEST — Invio v1.0.0.1.49.5

## Official frozen parent

- Parent: `Invio v1.0.0.1.49.4`
- Parent Git commit: `a647bb35730fb22b46758c1f309bbebd5d3e699d`
- Scope: `Phase 1 — RDP / TLS Trust & API Connectivity` only
- Target: `Invio v1.0.0.1.49.5`

## Verified root cause

On the affected Windows Server 2025 RDP host, `https://applemobileshopnow.odoo.com` validates through Windows CryptoAPI/Schannel, .NET HTTPS, and curl/Schannel, while frozen Invio v1.49.4 fails in the packaged Python/OpenSSL certificate-chain path with `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`. The correction therefore belongs in the shared Windows HTTPS trust boundary, not in Odoo business logic.

## Functional changes

1. Add native Windows certificate trust through `truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)` in the shared ProviderRuntime HTTPS boundary.
2. Keep `ssl.CERT_REQUIRED` and hostname verification enabled.
3. Route Windows HTTPS provider and OAuth-discovery requests through the same verified native-trust context.
4. Fail closed if the Windows native-trust backend is absent or cannot initialize.
5. Preserve the v1.49.4 non-Windows stdlib `urlopen()` transport path.
6. Add TLS fail-closed regression coverage and Odoo API-Test contract regression coverage.
7. Require/package `truststore>=0.10.4,<0.11` in wheel/Nuitka/MSI distribution contracts.
8. Add compiled and MSI-installed native-TLS backend smoke gates.
9. Synchronize v1.49.5 version metadata and Phase 1 documentation.

## Delta inventory

- Added files: 6
- Modified files: 31
- Removed files: 0
- Total delta files: 37
- Layout: direct project-root overlay; no wrapper directory

`SHA256SUMS.txt` is regenerated after this manifest and covers the release-critical baseline set plus every v1.49.5 delta file, excluding itself.

## Frozen boundaries

The following remain outside Phase 1 and are required to stay functionally unchanged: Odoo provider business/API/send workflow, Browser OAuth V1 contract, Easy Onboarding, IVX Format V1 and provider-manager lifecycle, Task state machine, WorkerManager/QThread architecture, retry/delivery-ledger semantics, SQLite/storage/CredentialStore, Accounts/Tasks/Providers/Reports/Settings UI behavior, MSI UX/WiX architecture, and all Phase 2-4 work.

## Security invariants

No `verify=False`, `ssl.CERT_NONE`, disabled hostname verification, hard-coded provider certificate/fingerprint, certificate-error suppression, or HTTP downgrade is permitted. Existing certificate-verification failure classification remains permanent (`category=tls`, `retryable=False`).

## Verification gates

The patch must pass targeted TLS/Odoo/distribution contracts and the complete repository audit before delivery. Native Windows OneDir/MSI smoke, the affected RDP Odoo API Test, and GitHub `windows-build` are post-apply acceptance gates because this delivery environment is not Windows. Their results must not be represented as locally executed PASS results.
