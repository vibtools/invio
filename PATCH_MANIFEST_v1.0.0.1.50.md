# Invio v1.0.0.1.50 — Phase 4 Dynamic Tags Patch Manifest

**Parent baseline:** Invio v1.0.0.1.49.9 @ `5b4dc934e62a9aead3a20e9b321b5eaf8fbf85d1`  
**Parent uploaded ZIP SHA-256:** `ce6641afcdb0bb457db80285641a894374f80c108cea02797a3d1583b64803cc`

## Approved implementation

- Central provider-neutral Dynamic Tags V1 renderer.
- Exact tags: `#NAME#`, `#EMAIL#`, `#R5#`, `#R11#`, `#DATE#`, `#DATE-NAME#`, `#YAAR#`.
- Task-creation UTC date reference; unknown tags KEEP_LITERAL.
- Deterministic R5/R11 per Task+recipient.
- Settings Default Customer Name provenance only; explicit imported names remain literal.
- Template rendering only for Memo, Footer, Customer Note, Terms and Item Description.
- Additive SQLite schema v7 persistence and v6 compatibility migration.
- Host-side Stripe/Refrens/external rendering with provider contracts unchanged.

## Frozen boundaries

Phase-1 TLS, Phase-2 fatal-limit semantics, Phase-3 sending controls, WorkerManager, Task state machine, P10 delivery semantics, OAuth/Easy Onboarding, CredentialStore, ProviderManager/IVX, provider manifests/adapters and unrelated UI/UX remain outside scope.

## Verification status

Local verification is complete: Phase-4 direct tests 11/11 PASS; affected backend regression 300/300 PASS; release/P14/repository gate 109/109 PASS; final audit 642 total with 622 executed PASS, 20 PySide6-gated SKIP, 0 FAIL and 0 ERROR; syntax/privacy/provider-visibility PASS; wheel/P14 wheel audit PASS (59 source modules, 12 exact runtime resources). The final owner delta contains 8 added + 32 modified + 0 removed = 40 paths, including regenerated root `SHA256SUMS.txt`. GitHub Windows CI is a post-push acceptance gate and is not represented as passed until an actual run succeeds.
