# v1.2.0

- Add generic Invio Provider Easy Onboarding V1 support; existing External Provider Adapter v1 task/send behavior is unchanged.
- Mark raw refresh/provider IDs as generated/discovered/managed so Quick Connect hides them while Advanced / Manual Setup preserves the legacy path.
- Quick Connect automatically prepares the account and chains into the existing real API Test.
- Discovers CompanyInfo and reuses or creates one `Invio Service` Service item. Creation occurs only when one active Income account can be selected unambiguously and uses QuickBooks `requestid` idempotency. Invio does not guess among multiple accounting accounts.
- Preserve existing saved/manual accounts and protected refresh-token behavior; no mock/demo production endpoint is added.

# v1.1.0

- Add optional Invio Browser OAuth interface v1 authorization bootstrap.
- Preserve existing real API Test/invoice/send implementation and External Provider Adapter v1 execution semantics.
- Add persistent refresh-token behavior after first connection; provider-specific refresh rotation is stored through protected OS credentials where required.
- Add browser OAuth contract tests; no mock/demo production endpoint added.
- Enforce Intuit environment redirect rules: Sandbox localhost is permitted; Production requires an HTTPS DNS hostname and rejects localhost/IP redirects before browser launch.

# Changelog

## 1.0.0

- Initial production REST/OAuth provider implementation for Invio P13 interface v1.
- Real QuickBooks Online account verification, invoice creation and provider-side invoice email/publish workflow.
- Fail-closed template validation and deterministic provider-contract tests.
- Setup and controlled live-acceptance documentation.
