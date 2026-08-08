# PayrollMinds Remote Release Source Registry

All facts below were verified directly against remote Git and GitHub —
`git merge-base --is-ancestor`, `git diff`/`git patch-id` between real
SHAs, and the GitHub PR API — not from any prior session's documentation
claims. Where a PR's GitHub API `merged` field disagreed with what git
ancestry actually proves, git ancestry wins and the discrepancy is called
out explicitly (see §2).

Current `main`: `5c73b060d28bca914d570cfc19d205a768ffb3e2`.

## 1. Missing/unpushed historical references

The state handed to this task referenced a "Prompt 28 branch"
`codex/payrollminds-four-visual-baselines` and tree SHA
`1f7a754a805225bb4348e087e0e6f7cd3e297f5b`. Neither exists in the remote
(`git ls-remote --heads`, `git cat-file -t` both fail to find them). This
was already documented in
`docs/pilots/payrollminds/BROWSER_TEST_ISOLATION_AND_VISUAL_REPAIR.md`
§0 and is repeated here as the canonical record. No other undocumented
missing references were found in this pass.

## 2. Critical correction: three PRs show `merged:false` but ARE on main

The GitHub API (`list_pull_requests`) reports `merged: false, state:
closed` for PRs #147, #152, and #156. **This is misleading.** Direct git
proof:

| PR | Head SHA | Ancestor of current main? | Main's merge commit |
| -- | -- | -- | -- |
| #147 | `2a1fa4d9` | **YES** | `b047aae4` (2nd parent = exactly `2a1fa4d9`) |
| #152 | `31ffea75` | **YES** | `de40bc21` (2nd parent = exactly `31ffea75`) |
| #156 | `257c2dfc` | **YES** | `5c73b060` (2nd parent = exactly `257c2dfc`, current main tip) |

These were almost certainly merged by a direct push of a merge commit
(bypassing GitHub's merge-PR API endpoint), which lands the content but
leaves the PR object's `merged` boolean false. **Treat these three as
already integrated into main.** This directly affects the stacked chain
below: PR #148's own head (`38748588`) is genuinely *not* on main, but an
amended version of the same "product path" branch (rebased to
`0358405e`) *is* on main — its content shipped as part of #152's merge,
not #148's.

## 3. Full PR registry (#147–#165)

| PR | State (API) | Base | Head | On main? (git-verified) | Unique capability | Superseded by | Include in reconstruction? |
| -- | -- | -- | -- | -- | -- | -- | -- |
| #147 | closed, not merged (API) | `main@4d194dc` | `codex/payrollminds-pilot-governance-baseline@2a1fa4d9` | **YES** (verified ancestor) | Pilot governance baseline docs | — | Already on main; nothing to do |
| #148 | closed, not merged | `codex/...-pilot-governance-baseline@2a1fa4d9` | `codex/payrollminds-pilot-product-path@38748588` | Exact head: NO. Amended successor (`0358405e`): YES | Product path stabilization | Amended/rebased before #149 branched; final content shipped via #152 | Already effectively on main; nothing to do |
| #149 | closed, not merged | `codex/...-product-path@0358405e` | `codex/payrollminds-security-hardening@b148b17d` | **YES** | Access/security hardening (metadata access, secret scanning) | — | Already on main; nothing to do |
| #150 | closed, not merged | `codex/...-security-hardening@b148b17d` | `codex/payrollminds-production-readiness@2e39fc68` | **YES** | Production-readiness docs | — | Already on main; nothing to do |
| #151 | closed, not merged | `codex/...-production-readiness@2e39fc68` | `codex/payrollminds-ai-governance@4102190a` | **YES** | AI default-off control | — | Already on main; nothing to do |
| #152 | closed, not merged (API) | `main@b047aae4` | `codex/payrollminds-uat-evidence@31ffea75` | **YES** (verified ancestor, merge commit `de40bc21`) | Synthetic UAT evidence; carries #148–#151's amended chain into main | — | Already on main; nothing to do |
| #153 | open, draft | `main@4d194dc` (**stale** — pre-dates #147/#152/#156) | `codex/payrollminds-release-baseline-repair@12c82a34` | NO | Browser runner repair: removes `continue-on-error: true`, adds Playwright-args tests, strict failure propagation | — | **Yes** — root of the real browser-repair chain |
| #154 | open, draft | `codex/...-release-baseline-repair@12c82a34` (= #153 head, exact) | `codex/payrollminds-browser-baseline-repair@ba8be888` | NO | Introduces `openWorkspaceActions()` helper; classifies/fixes governed workspace action expectations across the file | — | **Yes** |
| #155 | closed, not merged | `codex/...-release-baseline-repair@12c82a34` (= #153 head) | `codex/payrollminds-browser-shared-repair@acf10c36` | NO | Dependency-security remediation | **#156** — confirmed byte-identical via `git patch-id` (`e419f6bb...`) | **No — exact duplicate of #156, already on main** |
| #156 | closed, not merged (API) | `main@de40bc21` | `codex/payrollminds-security-deps-main@257c2dfc` | **YES** (current main tip) | Dependency-security remediation, promoted directly to main | — | Already on main; nothing to do |
| #157 | open, draft | `main@de40bc21` | `codex/payrollminds-browser-baseline-integration@368c879e` | NO | Attempted whole-stack integration | Not part of the verified #153→#164 chain | **No** — see §4, deletes security-relevant test files relative to its own base; excluded |
| #158 | open, draft | `codex/...-release-baseline-repair@12c82a34` (= #153 head) | `codex/payrollminds-security-remediation-v2@25585c0b` | NO | Dependency-security remediation | **#156** — confirmed byte-identical via `git patch-id` (`e419f6bb...`) | **No — exact duplicate of #156, already on main** |
| #159 | open, draft | `codex/...-browser-baseline-repair@ba8be888` (= #154 head, exact) | `codex/payrollminds-browser-postback-repair@4f589684` | NO | MSA browser postback stabilization | — | **Yes** |
| #160 | open, draft | `main@5c73b060` (current) | `codex/payrollminds-browser-final-attribution@da2c7cc6` | NO | Evidence/attribution docs only (claims) | Not part of the verified #153→#164 chain | **No** — see §4, deletes the same security-relevant test files relative to current main; excluded |
| #161 | open, draft | `codex/...-browser-postback-repair@4f589684` (= #159 head, exact) | `codex/payrollminds-browser-critical-repair@0111b10d` | NO | 11 PayrollMinds-critical browser journey repairs | — | **Yes** |
| #162 | open, not draft | `main@5c73b060` | `codex/totp-mfa-hardening@ab0bf366` | NO | Default-off authenticator MFA | — | **EXCLUDED FROM PAYROLLMINDS RC** (explicit instruction) |
| #163 | open, draft | `codex/...-browser-critical-repair@0111b10d` (= #161 head, exact) | `codex/payrollminds-shared-workflow-repair@b0f09bbe` | NO | 7 shared workflow/Contract Record repairs | — | **Yes** |
| #164 | open, draft | `codex/...-shared-workflow-repair@b0f09bbe` (= #163 head, exact) | `codex/payrollminds-shared-ui-repair@56b08b76` | NO | 26 shared UI repairs + finance-threshold readiness race repair (folded into the same branch's later commits) | — | **Yes** — tip of the real browser-repair chain |
| #165 | open, draft | `main@5c73b060` (current) | `codex/payrollminds-browser-test-isolation@6db7d41b` | NO (this session's own PR) | Browser database-isolation repair (Life NDA leak), 4 regression tests, locator fix | — | **Yes** — validated independently on main-derived code (see `BROWSER_TEST_ISOLATION_AND_VISUAL_REPAIR.md`) |

## 4. Excluded branches: rationale in detail

**#155 and #158** — both branch directly off #153's head and both claim
to remediate dependency advisories. `git diff` against their shared base
shows **identical files with identical line counts** as #156's diff
against its own base; `git patch-id --stable` on all three produces the
**same patch-id** (`e419f6bb42933b3d553ec9568b2d38828b163d9c`). These are
the same patch, and #156's copy is already on main. Applying #155 or #158
would violate the "every unique patch applied exactly once" rule.

**#157 and #160** — both, independently, delete relative to their own
base:
- `tests/test_document_ingestion_security.py` (full removal, ~111 lines)
- `tests/test_organization_invitations.py` (partial removal)
- `tests/test_payrollminds_ai_governance_gate.py` (full removal, ~103 lines)
- `tests/test_payrollminds_pilot_product_path.py` (full removal, ~212 lines)
- `tests/test_upload_ocr_pipeline.py` (partial removal)
- Several `docs/pilots/payrollminds/UAT_*.md` files

Neither #157 nor #160 is an ancestor of #164's tip (`git merge-base
--is-ancestor` confirms both `NO`), so the verified #153→#164 chain does
not carry these deletions — confirmed directly: a scoped `git diff`
between #153's head and #164's tip on exactly these five test files is
empty, and all four test files exist on current main. #157/#160 were
independent, separate integration attempts (likely from an earlier
session) that are not part of the chain this task reconstructs from, and
their deletions are exactly the kind of change rule 8 ("do not alter
product behavior") and this project's audit/security posture prohibit
applying blindly. They are excluded. If their large
`docs/pilots/payrollminds/release-baseline/browser-failures.json`
evidence dumps are wanted for historical reference, they should be pulled
in as a separate, reviewed, evidence-only change — not as part of this
reconstruction.

## 5. PR #162 / MFA exclusion proof

`git merge-base --is-ancestor ab0bf3669939c0f77186671c6ce6eede7ff0851b
<any commit used in this reconstruction>` was checked and #162's head is
not an ancestor of, and was never merged into, `main`,
`codex/payrollminds-browser-test-isolation` (#165), or the #153→#164
chain. #162's branch (`codex/totp-mfa-hardening`) was never fetched into
or referenced by the reconstruction branch. **EXCLUDED FROM PAYROLLMINDS
RC.**
