# Security-clean browser baseline

Status: **NO-GO**. Proposed evidence only; it grants no release, deployment,
merge, approval, exception, or feature activation authority.

## Source graph and dependency order

At task start, `origin/main` was
`4d194dcc0663b94accf4eb892c508fe70cf2d3a7`. It later advanced externally to
`5c73b060d28bca914d570cfc19d205a768ffb3e2`; the integration branch was not
rebased. PR #153 (`12c82a34c3d02227287dd97f56d758443082559e`) is an open
draft based on task-start main. PR #154 (`ba8be8884296cde7cda7e644a2d6086082ce4866`)
is an open draft based on PR #153. PR #155
(`acf10c36898c5dca59397af6da753458fb212efd`) is currently closed; its
validated dependency commits were integrated without merging it.

Verified logical order:

1. PR #153 runner repair;
2. PR #155 dependency remediation;
3. PR #154 governed browser and MSA repairs;
4. the two narrowly scoped MSA fixture/race repairs recorded below.

PR #154 already contained PR #153 through its base. PR #155 also based on PR
#153 and did not duplicate the MSA changes. The integration applied each unique
patch once. The only content conflict was PR #154's older documentation file;
the resolution retained the newer 90-record registry schema. The initial
runner cherry-pick conflicted because of the older main base, so its equivalent
safe runner changes and argument harness were applied once and verified.

## Integrated branch

Branch: `codex/payrollminds-browser-baseline-integration`

Frozen branch SHA: `3d1d60a34eebd8544a613e98bd204bd5acba20f1`.

| Commit | Purpose |
| --- | --- |
| `f20eec60` | Browser runner failure propagation and safe arguments |
| `312c2c06` | PostCSS and brace-expansion remediation |
| `ee81a78d` | Cryptography remediation |
| `54d200bc`, `cb0af345`, `2cead64c` | Governed browser/MSA expectation and fixture repairs |
| `54a71ddd` | 90-test registry schema |
| `3d065d92` | Production Tailwind output rebuilt after dependency update |
| `979e6f6b`, `3d1d60a3` | Threshold fixture input and reliable same-URL MSA postback waits |

GitHub pull-request CI executes a merge ref. Both final browser attempts used
`45b45a4a`, the merge of branch SHA `3d1d60a3…` into current main
`5c73b060…`; this distinction is material and is retained in the JSON evidence.

## Dependency-security evidence

| Package | Old → new | Usage and files | Advisory / outcome | Rollback |
| --- | --- | --- | --- | --- |
| PostCSS | 8.5.18 → 8.5.25 | Direct build dependency in `client` and `theme/static_src`, package files and locks | Resolves GHSA-FXQJ-RQCC-2CMP; both Node audits report 0 vulnerabilities | Revert the dependency and regenerated asset together |
| brace-expansion | 5.0.8 → 5.0.9 | Transitive theme build override and lock | Resolves GHSA-RGW5-RVV9-X895 | Revert the override/lock together |
| cryptography | 48.0.1 → 50.0.0 | Direct runtime/dev dependency in both requirements files | Remediates the reported CVE-2026-69247/69248/69249 findings | Revert both pins in one commit |

`npm ci` completed for both Node workspaces; `npm audit` reported zero
vulnerabilities for both. The production theme build completed and its committed
output was refreshed. CI `security-scans` is green on PR #157. Local
`python -m pip_audit -r requirements/runtime.txt` could not create its isolated
temporary virtual environment because the host Python `ensurepip` process
aborted; this is recorded as an environment limitation, not a passing audit.
No vulnerable alternate Node lockfile was found. Bandit completed with 50
inherited findings (0 high, 3 medium); no product-code change in this branch
introduced a new finding. Secret scanning is covered by the green repository
security scan.

## Validation results

| Check | Result |
| --- | --- |
| Django system check | pass |
| Migration drift (`migrate --check`) | pass |
| Local migration and NULL-organization audit | pass; no NULL rows |
| Cross-tenant isolation | 75 passed |
| MSA Django suite | 25 passed |
| Full affected Playwright file | 17 passed |
| Exact local CI shard 7 | 11 passed |
| Runner argument harness | pass |
| Full unit/integration suite | 2,627 run; 35 failures, 19 errors, 32 skipped — same recorded clean-main counts |
| Security scans / PR evidence / tenancy CI | green on PR #157 |

The full suite's known failures/errors remain a NO-GO baseline. This work did
not add a count regression; individual failure-signature equivalence outside
the recorded count has not been independently proven.

## Final browser evidence

CI UI Verification run
[`30910072964`](https://github.com/Technivian/CLMOne/actions/runs/30910072964)
executed every configured test twice on merge SHA `45b45a4a`:

| Attempt | Tests | Pass | Fail | Interrupted / not run / setup / teardown |
| --- | ---: | ---: | ---: | ---: |
| 1 | 90 | 42 | 48 | 0 / 0 / 0 / 0 |
| 2 | 90 | 42 | 48 | 0 / 0 / 0 / 0 |

The failing test set is identical. All 17 pilot-verification tests pass.
The 48 remaining failures each have a terminal record in
`release-baseline/browser-failures.json` and are classified **H — Unresolved**.
There are no category-G candidates and no proposed exception.

## Remaining blockers and recommendation

Infrastructure failures remaining: **0**. Confirmed repaired pilot MSA
fixture/race failures remaining: **0**. Remaining unresolved browser failures:
**48**. Potential pilot, shared-platform, security, tenancy, privacy, audit,
integrity, and dependency relevance has not been ruled out for every remaining
failure; consequently none may be deferred.

The application remains **NO-GO**. Executable UAT and release-envelope work
are not authorized. The proposed foundational merge order, once independent
reviews and green gates are available, remains PR #153 → dependency remediation
(now also present on main) → PR #154 → this integration's narrowly scoped MSA
test repair. Nothing was merged or deployed by this task.
