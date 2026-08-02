# PayrollMinds RC2 integration evidence

**Status:** NO-GO. This record is not approval, merge, deployment, or activation authority. Inbound email ingestion and external AI remain disabled.

## Repository, PR, and dependency record

`origin/main` fetched on 2026-08-02: `4d194dcc0663b94accf4eb892c508fe70cf2d3a7`. RC2 was created from this clean SHA; RC1 was retained unchanged.

| PR | Base SHA | Head SHA | Dependency |
|---|---|---|---|
| #147 | `4d194dcc` | `2a1fa4d9` | Governance baseline |
| #148 | `2a1fa4d9` | `0358405e` | #147 |
| #149 | `0358405e` | `b148b17d` | #148 |
| #150 | `b148b17d` | `2e39fc68` | #149 |
| #151 | `2e39fc68` | `4102190a` | #150 |
| #152 | `4102190a` | `31ffea75` | #151 |

The remote PR bases now match `#147 -> #148 -> #149 -> #150 -> #151 -> #152`.

## Canonical decision-record registry

The registry covers `origin/main` and all unique PR ranges. Historical meeting/package artifacts that reuse an ADR number are evidence attachments to their named canonical decision, not distinct decisions.

| Type | ID | Title / file | Origin | Status | Referenced by |
|---|---|---|---|---|---|
| ADR | 0008 | Frontend design-system unification | main | historical | index |
| ADR | 0009 | Governance charter supersession | main | Accepted | Charter/index |
| ADR | 0010 | Workflow instance version pinning | main | historical | architecture docs |
| ADR | 0011 | Canonical Contract Type catalogue | main | Proposed | domain docs |
| ADR | 0012 | Workflow Definition aggregate cutover | main | historical | architecture docs |
| ADR | 0013 | Approval Requirement/Decision split | main | historical | index/acceptance artifact |
| ADR | 0014 | Role Definition reconciliation | main | Accepted | index/acceptance artifacts |
| ADR | 0015 | Exception Request/Decision model | main | Accepted | index/acceptance artifact |
| ADR | 0016 | Quarantine-first document ingestion | main | Accepted/default-off | pilot path |
| ADR | 0017 | PayrollMinds isolated pilot release topology | #147 | Proposed | PDR-0011, EXC-0001, index |
| ADR | 0018 | PayrollMinds pilot production topology | #150 | Proposed | production plan/index |
| ADR | 0019 | PayrollMinds AI provider disabled boundary | #151 | Proposed | PDR-0012, EXC-0002, index |
| PDR | 0001 | Finance approval threshold | main | historical | index |
| PDR | 0002 | Contract Stage, Status, and Document State | main | historical | index |
| PDR | 0003 | Documentation operating model | main | Accepted | canonical docs |
| PDR | 0004 | GitHub review and release evidence | main | Proposed | release evidence |
| PDR | 0005 | DPA specialist workflow gate | main | Accepted | roadmap |
| PDR | 0006 | Canonical workflow versioning | main | Approved | roadmap |
| PDR | 0007 | ApprovalRoute runtime boundary | main | Proposed | index |
| PDR | 0008 | Object-level read enforcement policy | main | Proposed | pilot governance |
| PDR | 0010 | Owner-directed release authorization | main | Accepted | index |
| PDR | 0011 | PayrollMinds controlled pilot scope | #147 | Proposed | ADR-0017, EXC-0001 |
| PDR | 0012 | PayrollMinds AI metadata-suggestion gate | #151 | Proposed | ADR-0019, EXC-0002 |
| EXC | 0001 | PayrollMinds enterprise-capability deferral | #147 | Proposed/inactive | ADR-0017, PDR-0011 |
| EXC | 0002 | PayrollMinds AI metadata-suggestions deferred | #151 | Proposed/inactive | ADR-0019, PDR-0012 |

`PDR-0008-ADDENDUM-001-policy-resolution.md` is an addendum, not a second PDR. The rebuilt tree has zero duplicate canonical headings, conflicting titles, or stale renamed-record references.

## Ownership decisions and ID mapping

The expected ownership hypothesis was confirmed. These records are materially different and were not merged:

| Old assignment | Canonical decision |
|---|---|
| #147 general topology / #150 production topology both ADR-0017 | #147 retains ADR-0017; #150 is ADR-0018 |
| #151 AI boundary ADR-0018 | ADR-0019 |
| #147 pilot scope / #151 AI gate both PDR-0011 | #147 retains PDR-0011; #151 is PDR-0012 |
| #147 broad deferral / #151 AI deferral both EXC-0001 | #147 retains EXC-0001; #151 is EXC-0002 |

#150 correction `2e39fc68` updates its filename, heading, index, and infrastructure-plan reference. #151 correction `4102190a` updates filenames, headings, cross-record links, and index. Both exceptions remain Proposed and inactive.

## Corrected source branches

| Branch / PR | Corrective commit or result |
|---|---|
| #148 product path | Rebased onto #147; evidence correction retained at `0358405e`; release-evidence PR job green |
| #149 security | Rebased onto #148 at `b148b17d`; no decision-record delta |
| #150 production readiness | Rebased; distinct ADR correction `2e39fc68` |
| #151 AI governance | Rebased and amended at `4102190a` with ADR-0019/PDR-0012/EXC-0002 |
| #152 UAT | Rebased onto #151 at `31ffea75`; unique delta adds no decision record |

`--force-with-lease` was used only for these related draft branches. No product behavior, approval status, or fail-closed setting was changed by reconciliation.

## RC2 assembly

`codex/payrollminds-pilot-rc2-integration` was created from clean current main. The pre-evidence validation SHA is `798d49a1b8bb00f467f099be3ead9aad3372a981`.

| PR | Integrated commits |
|---|---|
| #147 | `8c1109c3` |
| #148 | `62a719e4`, `ed2ea988` |
| #149 | `167f62d2`, `00551357`, `e4f21e4b` |
| #150 | `b303981f`, `359bdd67`, `be916dd0` |
| #151 | `10ee9b9e` |
| #152 | `798d49a1` |

All 11 unique source commits were applied exactly once. No cherry-pick conflict or duplicate patch remains.

## Validation results

Environment: macOS arm64, Python 3.12 shared workspace virtualenv; in-memory SQLite for `make test`; local SQLite only for migration/audit.

| Check | Result | Evidence |
|---|---|---|
| Registry and references | Pass | zero duplicate canonical headings and stale renamed-record references |
| `make check` | Pass | no system-check issues |
| `manage.py makemigrations --check --dry-run` | Pass | `No changes detected` |
| `manage.py migrate --noinput` + `audit_null_organizations` | Pass | all migrations applied; no NULL-organization rows |
| `git diff --check` | Pass | exit 0 |
| `python -m pip_audit --disable-pip --no-deps -r requirements/runtime.txt` | Pass | no known vulnerabilities |
| `python -m bandit -q -r contracts config -lll` | Pass | exit 0 |
| Full suite run one | Fail | 2,639 tests; 39 failures; 19 errors; 32 skipped; 51.691s; `/tmp/payrollminds-rc2-full-run-1.log` |
| Full suite run two | Fail | 2,639 tests; 39 failures; 19 errors; 32 skipped; 50.437s; `/tmp/payrollminds-rc2-full-run-2.log` |
| UI integrity | Pass | 11 tests passed |
| Full browser entry point | Fail before Playwright | `scripts/verify_ui.sh`: `PLAYWRIGHT_ARGS[@]: unbound variable`; `/tmp/payrollminds-rc2-ui.log` |
| Secret scan | Not run locally | TruffleHog is GitHub-Action supplied and absent locally |
| Backup/restore drill | Not run | no PostgreSQL target, credentials, or backup artifact supplied; no evidence fabricated |
| Synthetic UAT | Evidence-only #152; no runnable suite found | no real data loaded |

Focused source checks passed: #148 system/migration/audit and cross-tenant checks; #150 system/migration-drift checks; #151 system/migration-drift plus four AI fail-closed tests.

## Two-run comparison

The same validation SHA produced the same 58 failure/error signatures in each run: 39 failures, 19 errors, and 32 skips. The 1.254-second duration variance is non-material. This is stable reproduction of a failed suite, not release stability proof.

Representative blockers include Contract form/status drift, role-walkthrough authorization expectations, e-sign provider tests, workflow-operation tests, and PAR-SEC-002 search-enforcement tests. No failure was hidden, skipped, or weakened.

## CI, rollback, and recommendation

#147 through #152 have green required CI on their current heads. No combined-RC PR CI exists.

No merge order is authorized while the full suite and browser gate fail. After source-branch repairs and green CI, merge #147, #148, #149, #150, #151, then #152; rebuild a fresh RC and run two complete passing suites on one SHA.

Rollback remains fail-closed: do not merge or deploy RC2; keep email and external AI disabled; preserve quarantine and repository abort controls. No production state, credentials, customer data, or public access was created.

**Final recommendation: NO-GO.** No release-candidate SHA is eligible for approval.
