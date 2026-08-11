# Invio v1.0.0.1.48.02 — CI Failure Fix Patch Manifest

## Baseline

- Official baseline: `Invio v1.0.0.1.48.02`
- Public version remains: `1.0.0.1.48.02`
- Tag identity remains: `v1.0.0.1.48.02`
- Scope: GitHub CI environment dependency + repository test-contract/artifact correction only

## Root causes corrected

1. Ubuntu GitHub Actions lacked `libEGL.so.1` / related Qt runtime support required by real PySide6 GUI interaction tests.
2. Four historical `ROOT_CAUSE_VERIFICATION_*.md` records were required by repository contract tests but were excluded from clean GitHub checkout by the broad `/project/` ignore rule.

## Functional/runtime impact

None. No `src/`, provider runtime, business logic, UI design, popup behavior, task engine, storage/schema, provider contract, or version identity is changed.

## Verification

- Targeted CI/repository contract suite: **80/80 PASS**
- Full local audit: **443 discovered / 439 PASS / 4 SKIPPED**
- Syntax audit: **PASS**
- Repository privacy audit: **PASS**
- Provider visibility audit: **PASS**
- Four local skips: real PySide6 runtime tests unavailable in local sandbox; the existing Windows GitHub job executed all four and all four passed.
- Post-correction GitHub non-tag run: **PENDING**; required as final remote acceptance gate.

## Modified files

1. `.github/workflows/ci.yml`
2. `.gitignore`
3. `CHANGELOG.md`
4. `README.md`
5. `docs/release-notes/1.0.0.1.48.02.md`
6. `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.47.0.md`
7. `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.0.md`
8. `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.01.md`
9. `project/research/ROOT_CAUSE_VERIFICATION_v1.0.0.1.48.02.md`
10. `tests/test_p14_distribution_pipeline.py`
11. `tests/test_repository_contracts.py`

## Added delivery records

12. `PATCH_MANIFEST_v1.0.0.1.48.02_CI_FIX.md`
13. `project/research/FINAL_CI_FORENSIC_VERIFICATION_v1.0.0.1.48.02.md`

## Removed files

None.

## Git commit

```bash
git add -A
git commit -m "fix(ci): install Linux Qt runtime and track CI verification records"
git push origin main
```

Do not create/push a release tag until the new non-tag GitHub Actions run is green.
