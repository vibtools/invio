# v1.2.0

- Add generic Invio Provider Easy Onboarding V1 support; existing External Provider Adapter v1 task/send behavior is unchanged.
- Mark raw refresh/provider IDs as generated/discovered/managed so Quick Connect hides them while Advanced / Manual Setup preserves the legacy path.
- Quick Connect automatically prepares the account and chains into the existing real API Test.
- Discovers the authorized organization and reuses or creates exactly one active `Invio Service` Service item using the provider settings CREATE permission.
- Preserve existing saved/manual accounts and protected refresh-token behavior; no mock/demo production endpoint is added.

# v1.1.0

- Add optional Invio Browser OAuth interface v1 authorization bootstrap.
- Preserve existing real API Test/invoice/send implementation and External Provider Adapter v1 execution semantics.
- Add persistent refresh-token behavior after first connection; provider-specific refresh rotation is stored through protected OS credentials where required.
- Add browser OAuth contract tests; no mock/demo production endpoint added.

# Changelog

## 1.0.0

- Initial production REST/OAuth provider implementation for Invio P13 interface v1.
- Real Zoho Invoice account verification, invoice creation and provider-side invoice email/publish workflow.
- Fail-closed template validation and deterministic provider-contract tests.
- Setup and controlled live-acceptance documentation.
