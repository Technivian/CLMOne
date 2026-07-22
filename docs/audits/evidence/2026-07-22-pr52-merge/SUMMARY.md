# PR #52 merge evidence — visual + E2E remediation

**Date:** 2026-07-22  
**PR:** [#52](https://github.com/Technivian/CLMOne/pull/52) — `fix(ci): PR #50 visual + E2E remediation`  
**Head before merge:** `3635c328`  
**Merge commit:** `3c5e628bfdf6f437f0f4c8bebf42de0da35b388b`  
**Merged at:** 2026-07-22T13:07:15Z  
**Base before merge:** `58966de7` (PR #54)  
**Updated `main` HEAD:** `3c5e628b`

---

## Human approval

| Item | Detail |
|---|---|
| Approver | Product / programme steward (explicit APPROVE) |
| Scope reviewed | Repository-load synchronization; corrected Darwin visual baselines; updated critical-flow E2E helpers and locators |
| Evidence reviewed | 8/8 required CI checks SUCCESS; Phase 1 visual 5/5; redesigned-e2e; quality-and-tenancy; security/brand/design/UI/release-evidence |
| Exclusions confirmed | No new product capability; no privilege change; no resolver cutover; no PAR-APR-002 |

---

## Files merged (7)

| Path | Change |
|---|---|
| `client/tests/e2e/visual-baselines.spec.js` | Wait for `#contracts-tbody` to leave `Loading contracts` before list capture |
| `client/tests/e2e/critical-flows.spec.js` | Align locators/helpers with governed form + repository navigation |
| `phase-1-dashboard-darwin.png` | Restored/corrected Darwin baseline |
| `phase-1-detail-darwin.png` | Restored/corrected Darwin baseline |
| `phase-1-form-darwin.png` | Restored/corrected Darwin baseline |
| `phase-1-list-darwin.png` | Updated from macos-14 CI capture |
| `phase-1-workspace-darwin.png` | Restored/corrected Darwin baseline |

---

## CI confirmation (pre-merge HEAD `3635c328`)

| Check | Result |
|---|---|
| Forbidden-brand scan | SUCCESS |
| Anti-drift + contrast | SUCCESS |
| pr-release-evidence | SUCCESS |
| quality-and-tenancy | SUCCESS |
| security-scans | SUCCESS |
| verify-ui | SUCCESS |
| Phase 1 visual baselines | SUCCESS (5/5) |
| redesigned-e2e | SUCCESS |

---

## Post-merge local verification (`main` @ `3c5e628b`)

| Check | Result |
|---|---|
| Repository-load wait present in `visual-baselines.spec.js` | **CONFIRMED** |
| Darwin phase-1 baselines present (5 files) | **CONFIRMED** |
| Critical-flow repository / workflow helpers present | **CONFIRMED** |
| `make check` | **PASS** |
| `scripts/check_governance_authority.sh` | **PASS** |

Playwright visual/E2E suites were confirmed green on the PR CI runners (macos-14 visual + redesigned-e2e). Local re-run of those suites is not required to record this merge.

---

## Programme impact

- Closes the Tranche-1 visual/E2E residual left after PR #50 @ `c52d699a`
- Does **not** change PAR-APR-001 (Completed via PR #51), PAR-APR-002, PAR-WF-010, or PAR-ID-001 product authority
- Next programme work continues from `main` @ `3c5e628b`
