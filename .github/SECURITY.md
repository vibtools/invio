# Security

## Credential protection

Invio stores provider credential values through Python `keyring` and requires an approved OS-protected backend. There is no plaintext-file fallback. The operational SQLite database stores only opaque credential references; ordinary application settings remain non-sensitive.

If protected credential storage is unavailable, Account persistence fails closed. If a persisted credential is missing or unreadable at startup, Account metadata remains visible but runtime state is downgraded to `Not Verified`, preserving the existing Task execution gates.

## Transport and provider trust boundaries

Provider HTTPS certificate and hostname verification remain mandatory. On Windows, the shared provider transport uses the native Windows trust store through `truststore`; certificate-verification failures are not silently bypassed.

External executable provider adapters are trusted code. Invio validates the supported external-adapter/IVX contract and requires the existing explicit trust boundary before executable adapter use. Installing an external provider must not be treated as sandboxing untrusted Python code.

## Privacy, logs, exports, and local data

Recipient-level delivery reconciliation, structured privacy redaction, safe exports, and closed-history retention controls are implemented through the existing P10/P12 operational contracts. Do not include provider secrets, unredacted customer data, local application databases, protected credential material, or sensitive exported logs in public issues, pull requests, commits, screenshots, or diagnostic archives.

## Windows release signing

The current Windows distribution follows owner-approved Signing Option C and may be unsigned, so Windows can display `Unknown Publisher`. This is a documented distribution boundary, not a claim of Authenticode verification. Use the release checksum asset when verifying downloaded release files.

## Reporting security issues

Use the repository's private/security reporting channel where available. Do not publish active provider credentials, customer data, authorization codes, refresh tokens, local databases, or other sensitive operational evidence in a public issue.

## Current security boundary

The current release combines OS-protected credential persistence, fail-closed credential recovery, mandatory TLS verification, privacy-redacted operational logging/export controls, and explicit trusted external-provider execution boundaries. These controls reduce repository and runtime exposure but do not make third-party providers, provider credentials, user endpoints, or unsigned binaries inherently trusted.
