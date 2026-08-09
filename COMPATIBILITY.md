# Compatibility

Target runtime: Python 3.12+ with PySide6 on Windows, Linux, and macOS desktop environments. Primary desktop validation target is Windows.

P02 adds `keyring>=25.7,<26` for protected credentials. Invio accepts only approved OS-protected keyring backend families: Windows Credential Locker, macOS Keychain, Freedesktop Secret Service/libsecret, or KWallet. If no approved backend is available, provider credentials fail closed and are not written to plaintext storage.

Linux keyring availability depends on the desktop/system secret-service configuration. No fallback file keyring is bundled or enabled by Invio.
