# PayrollMinds RC1 integration evidence

**Status:** NO-GO — no releasable candidate SHA exists.

**Scope:** Draft PRs #147 through #152, validated on 2026-08-02. This record
does not approve, merge, deploy, or enable the pilot. Inbound email ingestion
and external AI remain disabled.

## Repository and PR evidence

Current `origin/main` at integration start was
`4d194dcc0663b94accf4eb892c508fe70cf2d3a7`.

| PR | Head SHA | Base ref / SHA | Dependency |
|---|---|---|---|
| #147 | `2a1fa4d913d29837f4b096c69e828183be184ce7` | `main` / `4d194dcc0663b94accf4eb892c508fe70cf2d3a7` | Independent governance baseline |
| #148 | `88a9bb8037bb071faab3cfc2f1eb4dd424db35eb` | `main` / `4d194dcc0663b94accf4eb892c508fe70cf2d3a7` | Product path; source release-evidence remediation is the final commit |
| #149 | `f748da3141e025a6c45ca7a4c82284f70369ae04` | `codex/payrollminds-pilot-product-path` / `fec9b205a42d976a35ccb093f68c6cf3e5371487` | #148 |
| #150 | `faf6d4e1e9b52992c38492f4ae020eae8eb81c04` | `codex/payrollminds-security-hardening` / `f748da3141e025a6c45ca7a4c82284f70369ae04` | #149 |
| #151 | `c093adad67f25969eaf9a6e928d75102a68dc7d6` | `codex/payrollminds-production-readiness` / `faf6d4e1e9b52992c38492f4ae020eae8eb81c04` | #150 |
| #152 | `621b0ac3337d672229c9b9352908fd3cb0b9f815` | `codex/payrollminds-ai-governance` / `c093adad67f25969eaf9a6e928d75102a68dc7d6` | #151 |

The intended graph is `#147` plus `#148 -> #149 -> #150 -> #151 -> #152`.
PR #152 does **not** contain #147: both descend separately from current main.

## Disposable integration assembly

The disposable branch is `codex/payrollminds-pilot-rc1-integration`, created
from the clean main SHA above. The following commits were applied exactly once
and remain as a partial, non-release-candidate assembly:

1. `ec73ca3f79e7bf03f458cee17b2c89ea4449007f` — #147 governance baseline
2. `35a5d7fbbc5fc1785326a1e5a74b69faf3735551` — #148 product path
3. `4597bcb726df5712966530ae97828429bea73c3d` — #149 security hardening
4. `f90bdc9bc8568e064af868a933b9b18f0a8e8738` — #149 secret-scan tooling
5. `1d70e6b85a0ac18af54e0474617c04e3874cd0cf` — #149 TruffleHog tooling
6. `4d4a084d07ab3d9328da36c37f1cd0bec44b45dd` — #150 readiness plan
7. `be2715ab889d1f4a6ab914a41d19819a3d756a2e` — #150 validation record
8. `5997e1f841fbb3b31abe2e0e83872acc736d9366` — #148 release-evidence remediation

Applying #151 then fails in
`docs/governance/decisions/README.md`. The cherry-pick was aborted on each
attempt; no integration-branch conflict resolution was made. #152 was not
applied.

No commits have duplicate patch IDs. The blocker is instead a duplicated
canonical decision-record namespace:

- #147 and #150 each use **ADR-0017** for different records.
- #147 and #151 each use **PDR-0011** for different records.
- #147 and #151 each use **EXC-0001** for different records.

The README conflict exposes the PDR and exception collisions; the ADR collision
is also present in the decision files. Selecting a record, renumbering one, or
combining the exception entries would alter governance records and is not a
safe integration-branch correction. A narrowly scoped source-branch governance
correction, with the required proposed-record links updated, is required first.

## PR #148 failed release-evidence check

| Item | Evidence |
|---|---|
| Classification | Release-evidence defect; not a product, test, configuration, or flaky failure |
| Exact check | `Platform Guardrails / pr-release-evidence` (run `30741165088`) |
| Exact error | Missing all three required checked command entries, smoke choice, rollback checkbox, and non-empty smoke/rollback evidence in the PR body |
| Affected surface | PR #148 body; matcher in `.github/workflows/platform-guardrails.yml` |
| Local reproduction | Yes. The pre-correction body did not match each required regular expression. |
| Smallest safe correction | Add truthful checklist/evidence fields to #148's PR body, then trigger a fresh `pull_request` event using a documentation-only evidence commit. GitHub re-run attempt 2 retained the old event payload and therefore correctly remained failed. |
| Correct source | #148 / `codex/payrollminds-pilot-product-path` |

Corrective commit `88a9bb8037bb071faab3cfc2f1eb4dd424db35eb`
adds only source-SHA validation evidence. The PR body now records the matching
required checks and the automated fail-closed rollback drill. The fresh
`pr-release-evidence` job is green; the remaining CI status is recorded below.

## Command inventory and results

The combined candidate was not assembled, so the commands below must not be
misrepresented as combined-candidate results.

| Required validation | Result |
|---|---|
| Django system check | #148 source SHA: passed, no issues. Combined candidate: not run. |
| Migration drift / migration application | #148 source SHA: `migrate --noinput` and `migrate --check` passed. Combined candidate: not run. |
| Tenant-integrity audit | #148 source SHA: `audit_null_organizations` exited 0 with no violations. Combined candidate: not run. |
| Formatting / whitespace | #148 source SHA: `git diff --check` passed. Combined candidate: not run. |
| Full unit and integration suite (`make test`) | Not run: no assembled candidate SHA. |
| Browser / critical end-to-end suite | Not run: no assembled candidate SHA. |
| Release-evidence workflow | #148 source PR: green after the corrective source commit. Combined candidate: not run. |
| Security, dependency, and secret scans | #148 source PR: `security-scans` green on the corrective SHA. Combined candidate: not run. |
| Tenant isolation | #148 source SHA: `tests.test_cross_tenant_isolation`, 75 passed. Combined candidate: not run. |
| Object authorization, revocation, search/export, append-only audit, quarantine path, backup/restore, synthetic UAT, AI fail-closed/non-authority | Not run as a combined release suite: no assembled candidate SHA. |
| Rollback drill | #148 source SHA: document-ingestion, repository-enforcement, and private-document suites, 45 passed. Combined candidate: not run. |

Source-only executed total: **120 test executions passed** (75 tenant-isolation
plus 45 rollback-drill tests). This is not a full-suite total and does not
satisfy the RC validation requirement.

## CI, migration, and stability

At the time of this record, PRs #147 and #149–#152 have completed green CI from
their recorded heads. For the corrected #148 head, `pr-release-evidence` and
`security-scans` are green; normal quality/UI jobs are still running. No CI run
exists for an assembled RC1 SHA.

There is no combined-candidate migration result, tenant-integrity result, or
security-scan result, and there are **zero** full-suite runs on the same
candidate SHA. Consequently there is no two-run stability comparison.

## Unresolved failures, merge order, and rollback

The open critical release blocker is the decision-record identifier collision.
The open high release blocker is absence of an assembled candidate and hence
the required full-suite, security, tenant, migration, and two-run evidence.
The original pilot readiness NO-GO conditions remain unaltered by this record.

No merge order is currently valid. After the source governance correction is
reviewed and CI is green, the proposed order is:

1. #147 governance baseline (or a narrow governing correction that reconciles
   its record identifiers with #150/#151);
2. #148 product path including `88a9bb80`;
3. #149 security hardening;
4. #150 production-readiness documentation;
5. #151 AI fail-closed governance after its reconciled decision records;
6. #152 synthetic UAT evidence;
7. recreate the integration branch from then-current main and perform the full
   suite twice on one exact SHA.

Until then, rollback is limited to retaining the existing default-off posture:
do not merge or deploy this branch, keep inbound email and external AI disabled,
and preserve the documented fail-closed quarantine and repository abort
controls. No production data, access, migration, or customer state has been
created by this integration work.

## Recommendation

**NO-GO.** There is no exact release-candidate SHA. Do not merge, deploy, or
activate any PayrollMinds capability from this stack.
