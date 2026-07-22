# PAR-ID-001 — R4 evidence verification (R5 preparation input)

**Prepared:** 2026-07-22  
**Baseline `main` HEAD verified:** `2e7b5adc9f1d9e1aae4478888d0994f4edaf9e60`  
**R4 evidence path:** [`../2026-07-22-par-id-001-r4-staging/`](../2026-07-22-par-id-001-r4-staging/)  
**Purpose:** Verify R4 support for R5 packaging. Does **not** authorize R5.

---

## Verification result

**Overall:** R4 package supports R5 **authorization packaging**. Required operational outcomes for R4 PASS are present and consistent with the programme baseline.

R5 remains **Blocked**. This verification is not a cutover vote.

---

## Checklist

| Required item | Present | Source |
|---|---|---|
| Environment identity | Yes | `par-id-001-r4-staging-equivalent` (`staging_env/README.md`, `R4_EXIT_REPORT.md`) |
| Activation timestamp | Yes | `activation_timestamp.txt` → `2026-07-22T19:44:04Z` |
| Rollback timestamp | Yes | `rollback_timestamp.txt` → `2026-07-22T19:47:22Z` |
| Flag state before / during / after | Yes | `flag_state_*.txt` |
| Committed defaults remain false | Yes | `committed_defaults_check.txt` |
| Resolver parity counts | Yes | `resolver_parity_during.json` (MATCH 89 / AMBIGUOUS 5 / critical 0) |
| Assignment parity counts | Yes | `assignment_parity_during.json` / `scenarios_executed.json` |
| All 16 scenarios | Yes | `scenarios_executed.json` (16 EXERCISED) |
| Fail-open behaviour | Yes | scenario `comparison_error_and_fail_open`; unit suite |
| Rollback by flag-off | Yes | `rollback_result.json` PASS; comparisons → 0 |
| Test results | Yes | `django-tests-*.txt` (91 targeted OK) |
| `manage.py check` | Yes | `django-check.txt` |
| Security findings | Yes | embedded in `R4_EXIT_REPORT.md` / `scenarios_executed.json` |
| Approval evidence | Yes | `STAGING_RESOLVER_PARITY_ACTIVATION_AUTHORIZATION.md` + exit report |
| Evidence review attestation | Yes | Product/Eng/Sec `19:49:25–27Z` in `R4_EXIT_REPORT.md` |
| Roadmap R4 Completed PASS | Yes | living `PLATFORM_ALIGNMENT_ROADMAP.md` (working tree / this PR) |

---

## Gap / inconsistency list (precise)

These are **packaging / process gaps**, not R4 PASS failures:

1. **Commit status:** At preparation start, R4 evidence lived only in the working tree (not yet committed on `main` @ `2e7b5adc`). This preparation PR is expected to land R4 evidence + R5 prep together so links resolve on the branch.
2. **Environment class:** R4 used a **local staging-equivalent SQLite** named environment, not a remote shared staging deployment URL. No remote staging host is documented. R5 proposal therefore remains staging-equivalent / non-production only.
3. **CI scope:** R4 recorded targeted PAR-ID-001 suites (91 tests) + `manage.py check`. Full `make test` / remote GitHub Actions green for the R4 evidence commit was not part of the R4 pack.
4. **Security review file naming:** Security content is embedded in the exit report and scenario JSON; there is no standalone `SECURITY_REVIEW.md` filename (content present).
5. **Intentional probe noise:** `scenarios_stderr.txt` contains expected `RuntimeError: forced comparison failure` log lines from the fail-open probe (not product failure).
6. **Org coverage:** R4 corpus orgs were `demo-firm`, `clmone-demo`, `clmone-mvp`, `controlled-pilot-org`, `payrollminds-demo`. Historical optional companion `controlled-pilot-org-b` was not present in this R4 recreate.
7. **Scenario aggregate counters:** `resolver_summary_after_scenarios` includes intentional inactive and fail-open probes (INACTIVE_ASSIGNMENT / RESOLUTION_ERROR increments). Authoritative R4 counts remain `resolver_parity_during.json` / `resolver_parity_authoritative_report` (critical 0).

No fabricated evidence was added to close these gaps.

---

## Binding conclusion for R5 packaging

R4 PASS evidence is sufficient to **prepare** the R5 authorization and execution-readiness package.

It is **not** sufficient, by itself, to authorize or execute R5.
