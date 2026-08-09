# Compatibility

Target runtime: Python 3.12+ with PySide6 on Windows, Linux, and macOS desktop environments. Primary desktop validation target is Windows.

P02 adds `keyring>=25.7,<26` for protected credentials. Invio accepts only approved OS-protected keyring backend families: Windows Credential Locker, macOS Keychain, Freedesktop Secret Service/libsecret, or KWallet. If no approved backend is available, provider credentials fail closed and are not written to plaintext storage.

Linux keyring availability depends on the desktop/system secret-service configuration. No fallback file keyring is bundled or enabled by Invio.


## v1.0.0.1.11 P03 Verification Correction

No schema version, dependency, provider ID, credential field, UI page, Task model, Customer model, Invoice Template model, ProviderManager API, or WorkerManager architecture changes are introduced. SQLite remains schema v2. Migration backup creation now uses SQLite's live backup API so committed WAL state is included. Missing/unreadable protected credentials are durably recorded as `Not Verified`, and Account Edit uses a fail-closed durable safety marker across the SQLite/keyring boundary.

## v1.0.0.1.10 P03

Existing schema-v1 operational databases migrate transactionally to schema v2 with a pre-migration backup. Existing provider IDs, credential field keys, Account IDs, Task IDs, Customer Lists, Invoice Templates, WorkerManager behavior, and supported desktop platforms are unchanged. P03 adds no dependency.
