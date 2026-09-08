# v1.1.0 Browser OAuth forensic delta

The provider execution adapter remains interface v1. Browser OAuth is optional interface v1 metadata/hooks only. Authorization uses provider official OAuth endpoints, state validation is host-owned, PKCE is used where declared, browser completion returns refresh/bootstrap credentials only, and deterministic tests verify that the existing invoice/send paths remain unchanged. Live third-party OAuth and mailbox receipt remain owner acceptance gates.

# QuickBooks Online Provider — Forensic Verification Record

## Scope

Standalone external provider plugin only. Invio application source, storage schema, WorkerManager, Task state machine, UI architecture and built-in provider implementations are not modified.

## Production path

OAuth refresh with latest refresh-token persistence → CompanyInfo/Item/Preferences verification → resolve/create Customer → create invoice using real QBO Item references → POST the invoice send endpoint with recipient email.

## Verification gates

- `provider.json` P13 runtime declaration: interface v1.
- `adapter.py` imports and compiles under the Invio Python 3.12+ contract.
- ProviderManager/ProviderRuntime source validation against Invio v1.0.0.1.49.
- Deterministic request-contract tests for account verification and send/publish flow.
- Official provider hosts only in production adapter source.
- No mock/demo/fake transport branch in production adapter source.
- Bundle SHA-256 inventory and ZIP CRC verification.

## Live truth boundary

No vendor OAuth secret or controlled production recipient mailbox is available inside the build environment. Therefore the verification record does not fabricate a live vendor-side invoice/email receipt result. Use `LIVE_TEST_CHECKLIST.md` for final account-specific acceptance.

## v1.2.0 Easy Onboarding verification note

This bundle additionally declares Invio Easy Onboarding V1. Verify Quick Connect hides generated/discovered/managed fields by default, provider preparation is repeat-safe/fail-closed, automatic API Test runs after preparation, and Advanced / Manual Setup preserves the previous credential path. Production adapter paths remain real API only.
