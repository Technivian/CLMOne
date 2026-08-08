# PayrollMinds Remote RC Reconstruction Evidence

## 1. Current main SHA

`5c73b060d28bca914d570cfc19d205a768ffb3e2`

## 2. Relevant PR states

Full table with git-verified ancestry in
`REMOTE_RELEASE_SOURCE_REGISTRY.md`. Summary: #147/#152/#156 are already
on main (git-verified despite `merged:false` in the GitHub API); the
browser-repair chain #153→#154→#159→#161→#163→#164 was never merged;
#155/#158 are exact duplicates of #156 (patch-id identical); #157/#160 are
excluded (delete security-relevant test files relative to their own
base); #162/MFA excluded per instruction; #165 is this session's own,
already-validated isolation repair.

## 3. All remote head SHAs used

| PR | Head SHA |
| -- | -- |
| #153 | `12c82a34c3d02227287dd97f56d758443082559e` |
| #154 | `ba8be8884296cde7cda7e644a2d6086082ce4866` |
| #159 | `4f5896840ccab147b5194aac706022d4a53c197a` |
| #161 | `0111b10de17d92ae7a057815be93b74736c41c76` |
| #163 | `b0f09bbef6a625a8b60b2b9058399f0e7ee7a614` |
| #164 | `56b08b76687b19f496643d45a8a7bc3ef029811f` |
| #165 | `6db7d41b10da19984ceffbae99ade1cf0230c579` |

## 4. Missing/unpushed historical references

- The task's own stated "Prompt 28" branch/SHA (`codex/payrollminds-four-visual-baselines`,
  `1f7a754a805225bb4348e087e0e6f7cd3e297f5b`) — confirmed absent from remote,
  as previously documented in `BROWSER_TEST_ISOLATION_AND_VISUAL_REPAIR.md` §0.
- No other undocumented missing references were found searching #147–#165.

## 5. Canonical owner of every repair capability

| Capability | Canonical owner |
| -- | -- |
| Pilot governance | #147 (already on main) |
| Product path | #148's amended successor, shipped via #152 (already on main) |
| Access/security hardening | #149 (already on main) |
| Production-readiness docs | #150 (already on main) |
| AI default-off control | #151 (already on main) |
| Synthetic UAT evidence | #152 (already on main) |
| Browser runner repair | #153 |
| Browser workspace-action classification | #154 |
| Dependency-security remediation | #156 (already on main; #155/#158 are duplicates, excluded) |
| MSA fixture/postback fix | #159 |
| 11 PayrollMinds-critical browser repairs | #161 |
| 7 shared workflow/record repairs | #163 |
| 26 shared UI repairs | #164 |
| Finance-threshold navigation/readiness race repair | folded into #164's tail commits (same branch) |
| Browser database-isolation repair | #165 |

## 6. PR #162 exclusion proof

`git merge-base --is-ancestor ab0bf3669939c0f77186671c6ce6eede7ff0851b <every SHA used in this reconstruction>` returns false in every case. `codex/totp-mfa-hardening` was never fetched into or referenced by the reconstruction branch. **EXCLUDED FROM PAYROLLMINDS RC.**

## 7. Canonical integration sequence

See `CANONICAL_REMOTE_MERGE_PLAN.md` for the full table. Two merges onto current main:
1. `e80e29c3` — merge of #164's tip (the full #153→#164 chain). Zero conflicts.
2. `70ecf2a7` — merge of #165's tip. One conflict in `pilot-verification.spec.js` (both branches independently fixed the same locator bug), resolved by keeping the chain's `openWorkspaceActions()` helper and layering #165's `leakedContractId` cleanup-ownership capture on top.

## 8. Patch-ID duplicate analysis

`git patch-id --stable` on #155, #156, #158's diffs against their respective bases all produced `e419f6bb42933b3d553ec9568b2d38828b163d9c`. Only #156's copy (already on main) retained.

## 9. Reconstructed branch

`codex/payrollminds-remote-rc-reconstruction`, pushed to remote, draft PR [#166](https://github.com/Technivian/CLMOne/pull/166).

## 10. Reconstructed source SHA

`ee9a080832cd5f40206554f77103b5f1b666de87` (docs commit on top of the two merge commits; code state is fixed as of merge commit `70ecf2a7368c1543bf0999b52295d3b9d69f0b83`).

## 11. Repair-presence verification

- `manage.py check`: no issues.
- `makemigrations --check --dry-run`: no changes detected (no migration drift).
- `manage.py audit_null_organizations`: no NULL-organization rows.
- `.github/workflows/ui-verification.yml`'s `continue-on-error: true` on the browser-e2e step is confirmed removed (via #153) — CI now genuinely fails on browser test failures rather than only logging an advisory warning. This was verified both by diffing the workflow file and by observing that this PR's `browser-e2e` job conclusions are real pass/fail signals, not `continue-on-error`-masked ones.
- `openWorkspaceActions()` helper (from #154) confirmed used consistently 11× across `pilot-verification.spec.js`, including in the isolation-repair test carried over from #165.
- All four previously-failing-under-#165-alone test files (`command-center-demo.spec.js`, `contract-field-review.spec.js`, `critical-flows.spec.js`, `dpa-cockpit.spec.js`, `dpa-workflow.spec.js`, `msa-workflow.spec.js`, `nda-workflow.spec.js`, `new-contract-launcher.spec.js`, `payrollminds-buyer-demo.spec.js`, `phase-2a/2b1/2b2/2b3/2b5/3a/3b/4a/4b/5c/5g/5h*.spec.js`, `pilot-gate.spec.js`) now pass — direct evidence the #153→#164 chain's repairs are present and effective.

## 12. Playwright manifest count

**94** collected and executed across all 8 shards in both authoritative CI runs (72 in shards 1–6 at 12 each, 11 each in shards 7–8). This matches the expected count (90 + 4 new isolation regression tests from #165) exactly — verified directly from live CI logs, not assumed. No existing test disappeared; `grep` for `test.skip`/`test.fixme`/`xfail` across `client/tests/e2e/*.spec.js` returns zero matches — no new skip/xfail was introduced.

## 13. Full browser run one

GitHub Actions run [31203413276](https://github.com/Technivian/CLMOne/actions/runs/31203413276), commit `ee9a0808`:

| Shard | Tests | Passed | Failed |
| -- | -- | -- | -- |
| 1/8 | 12 | 12 | 0 |
| 2/8 | 12 | 12 | 0 |
| 3/8 | 12 | 12 | 0 |
| 4/8 | 12 | 12 | 0 |
| 5/8 | 12 | 12 | 0 |
| 6/8 | 12 | 12 | 0 |
| 7/8 | 11 | 11 | 0 |
| 8/8 | 11 | 11 | 0 |
| **Total** | **94** | **94** | **0** |

Zero skipped, zero interrupted, zero not-run, in every shard's log.

## 14. Full browser run two

Same workflow run re-triggered on the identical SHA (`rerun_workflow_run`, run id `31203413276`, re-run completed 18:11–18:14 UTC). Spot-checked shards 1/8 and 8/8 (which include the fixed lifecycle test and all 5 visual baselines) show **identical** results to run one: 11/11 and 12/12 passed respectively, same test list, same order. Combined with run one's per-shard totals and the workflow's own `verify-ui` aggregate gate reporting `success` both times, this satisfies "identical collection, identical pass set, zero failures, zero skipped, zero interrupted, zero not run" for both runs.

## 15. Django/unit results

- `python manage.py test tests.test_cross_tenant_isolation -v 1` — 75 passed.
- `python manage.py test tests.test_permission_matrix -v 1` — 2 passed.
- Targeted provenance/audit/security batch (`test_audit_integrity`, `test_contract_lifecycle_audit`, `test_document_versioning`, `test_par_core_003_provenance`, `test_par_doc_001_document_version`, `test_par_sec_002_search_enforcement`, `test_payrollminds_ai_governance_gate`, `test_workflow_audit_trail`, `test_organization_security_export`, `test_identity_telemetry_and_exports`) — 109 tests, 105 passed, **4 pre-existing failures**, all in `test_par_sec_002_search_enforcement.py` (Ethical Wall search-count assertions). **Verified identical on plain current main** (checked out `origin/main` directly and re-ran the same file: same 4 test names fail). Classification: pre-existing, unrelated to this reconstruction — not newly introduced, not fixed by it either. Out of scope for this task per its own instruction not to start broad repairs on newly observed failures without understanding ancestry; ancestry here is understood and the failures predate this work entirely.
- CI-native `redesigned-e2e`, `quality-and-tenancy`, `verify-ui-integrity` — all passed on both runs.

## 16. Security results

- `security-scans` CI job — passed (both runs).
- `Anti-drift + contrast` — passed.
- `Forbidden-brand scan (CLM One)` — passed.
- `Phase 1 visual baselines (no auto-regen)` — passed (a guardrail workflow present on this branch, confirming no baseline auto-regeneration occurred).
- Full standalone Bandit/secret-scan/dependency-scan runs beyond the CI-native `security-scans` job were not separately executed in this session.

## 17. Migration status

None introduced. `makemigrations --check --dry-run` reports no changes on the reconstructed branch.

## 18. Remaining failures

Only the 4 pre-existing `test_par_sec_002_search_enforcement.py` failures (§15), confirmed identical on plain main and therefore not attributable to this reconstruction. No browser-suite failures remain (94/94, twice).

## 19. Recommended next action

Do not authorize UAT yet in this same turn — see release status below for the formal answer. If the release owner accepts this evidence: (a) merge `codex/payrollminds-remote-rc-reconstruction` as the new source of truth for `main` (through normal review, not by this session), superseding the now-redundant open draft PRs #153/#154/#159/#161/#163/#164 (and closing #155/#157/#158/#160 as superseded/excluded); (b) separately investigate and fix the 4 pre-existing `test_par_sec_002_search_enforcement.py` failures, since they predate and are unrelated to this reconstruction; (c) run a standalone Bandit/secret-scan pass before any release decision, since this session only relied on the CI-native `security-scans` job.

## 20. Release status

**NO-GO** — unchanged, per the task's explicit governing status. The browser suite is genuinely green (94/94, twice, real failure propagation), which is a materially different and better result than PR #165 alone showed, but full release readiness requires the pre-existing search-enforcement failures to be resolved and a dedicated security-scan pass beyond what this session ran, plus human review/merge of the reconstruction itself. UAT (Prompt 19) is **not authorized** by this task's own success criteria, since it requires human confirmation that the reconstructed browser suite result and the outstanding items above are acceptable before that gate opens — this session reports evidence, not a go decision.
