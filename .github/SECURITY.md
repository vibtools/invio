# Security

## Provider credentials

Invio `v1.0.0.1.9` stores provider credential values through the owner-approved Python `keyring` integration and requires an approved OS-protected backend. There is no plaintext-file fallback. The normal operational SQLite database stores only an opaque credential reference, and application settings remain non-sensitive.

If protected credential storage is unavailable, Account persistence fails closed. If a persisted credential entry is missing/unreadable at startup, the Account metadata is retained but the runtime Account is restored as `Not Verified`, so the existing P01 Task gates prevent execution.

Do not include provider secrets, exported logs containing sensitive customer data, or local per-user application databases in issues, pull requests, commits, screenshots, or diagnostic archives.

## Reporting security issues

Use the repository's private/security reporting channel where available. Do not publish active provider credentials or customer data in a public issue.

## Current boundary

P02 protects credential persistence. Recipient-level delivery reconciliation, generalized PII/log redaction, and full live/native security certification are later production roadmap phases and are not claimed by this release.
