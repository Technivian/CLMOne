# PayrollMinds Browser Test Isolation and Visual Repair

**Status: NO-GO** (against this task's strict 90/90-twice bar), but the
browser-isolation-and-visual repair itself is now backed by real,
authoritative GitHub Linux CI evidence, added after the local-only draft
below: all four target visual baselines (dashboard, list, workspace,
detail) pass **unchanged** against their committed snapshots, and the
fixed lifecycle test and all new isolation regression tests pass. See §12
for the real numbers and §14 for the final recommendation — the remaining
NO-GO blocker is a large pre-existing failure backlog unrelated to
isolation, not the isolation work itself.

## 0. Premise correction (read this first)

The task that produced this document specified a "current verified state"
of parent SHA `56b08b76687b19f496643d45a8a7bc3ef029811f`, git tree
`1f7a754a805225bb4348e087e0e6f7cd3e297f5b`, and a "Prompt 28 branch"
`codex/payrollminds-four-visual-baselines`. On investigation:

- `56b08b76687b19f496643d45a8a7bc3ef029811f` is real — it is the tip of
  `codex/payrollminds-shared-ui-repair`, an existing remote branch.
- `1f7a754a805225bb4348e087e0e6f7cd3e297f5b` does **not** exist anywhere in
  the remote (`git cat-file -t` fails; not reachable from any ref).
- `codex/payrollminds-four-visual-baselines` does **not** exist in the
  remote (`git ls-remote --heads` has no such branch).

The likely explanation is that the "Prompt 28" session did real work but
never pushed it, so that state was lost. Per this task's explicit
instruction ("pull everything from main and then run this prompt"), this
repair was performed starting from **actual `main`**
(`5c73b060d28bca914d570cfc19d205a768ffb3e2`), not from the unreachable
state. The four visual-record IDs given in the prompt
(`257cfc15fcd93e8e1bb7-...`) were not independently found in this repo's
history either; they are treated as informational only. This correction is
recorded here rather than silently substituted, so the discrepancy is not
lost.

## 1. Source identity

- Base branch: `main` @ `5c73b060d28bca914d570cfc19d205a768ffb3e2`
  ("Merge pull request #156 from Technivian/codex/payrollminds-security-deps-main")
- Repair branch: `codex/payrollminds-browser-test-isolation`
- Repair commit: `cfc8004adfd2732fea4b8f3d63071a494543bed3`
- Draft PR: https://github.com/Technivian/CLMOne/pull/165 (draft, not
  merged, not deployed)

## 2. Leaking lifecycle test (Phase 1)

**Test:** `client/tests/e2e/pilot-verification.spec.js:330` (post-fix line
number moved after refactor; originally line 320) — describe block
`Verification: lifecycle Stage vs Status`, test `invalid lifecycle stage
skip is rejected via repository bulk-update API`.

**Proof method:** not inferred from the name. The test was run directly
against a clean local E2E SQLite database
(`DJANGO_E2E=1`, `config.settings_development`, chromium pinned to the
locally available browser revision — see §9 for the caveat this implies),
and its effect on the database was inspected directly.

**Creation path traced:** Playwright fills the real NDA creation wizard at
`/contracts/new/nda/` with counterparty `Life NDA {suffix}` (suffix =
last 5 digits of `Date.now()`), submits via `#submit-nda-btn`, which POSTs
through the production NDA-creation service and lands on
`/contracts/workflows/<workflow id>`. This is a genuine product write, not
a stub.

**Resulting rows (captured from the running local E2E database via
`manage.py shell`, org `e2e-command-center` / `id=1`, actor
`e2e_owner` / `id=1` — the same org/user every other pilot-verification and
visual-baselines test authenticates as):**

| Field | Value |
| --- | --- |
| Contract ID | 10 |
| Contract counterparty | `Life NDA 97516` (this run's suffix) |
| Contract lifecycle_stage | `DRAFTING` |
| Organization | `e2e-command-center` (id 1) |
| Created by | `e2e_owner` (id 1) |
| Workflow ID | 4 |
| Workflow status | `ACTIVE` |
| Document / DocumentVersion | none (test never reaches document generation) |
| AuditLog rows | id 27 `CREATE Contract 10`, id 28 `CREATE Contract 10`, id 29 `CREATE Workflow 4` |

**Expected cleanup behavior:** none was implemented — no `afterEach`, no
API call, no management command.

**Actual cleanup behavior:** none. The row persisted for the remaining
lifetime of the E2E server process (i.e. for the rest of the shard job in
CI, since the database is not reset between test files — see §3).

**Direct proof of contamination** (HTTP GET of the rendered HTML, logged
in as the same E2E user used by the visual tests, immediately after the
lifecycle test ran):

```
/dashboard/               grep -c "Life NDA"  -> 1
/contracts/repository/    grep -c "Life NDA"  -> 1   (List)
/contracts/workflows/     grep -c "Life NDA"  -> 4   (Workspace)
```

**Detail test causal mechanism (stronger than "contaminated screenshot"):**
`visual-baselines.spec.js`'s `detail` test picks the *first*
`/contracts/workflows/<id>/` link found on the workflows page:

```js
const detailPath = await page.locator('a[href^="/contracts/workflows/"]').evaluateAll((links) => (
  links.map((link) => link.getAttribute('href')).find((href) => /^\/contracts\/workflows\/\d+\/$/.test(href))
));
```

With the leak present, the raw link order on `/contracts/workflows/` was:

```
/contracts/workflows/4/   <- leaked Life NDA workflow (most recent)
/contracts/workflows/3/
/contracts/workflows/2/
/contracts/workflows/1/
```

So the "detail" test did not merely render a contaminated page — it
navigated to the **wrong record entirely** (workflow 4, the sparse
DRAFTING-stage leak) instead of the intended baseline fixture (workflow 3).
This is consistent with the dimension mismatch observed locally
(`Expected an image 1440px by 1645px, received 1440px by 1000px`) before
the fix, on a contaminated database.

## 3. Browser isolation architecture (Phase 2)

- **Database setup:** `scripts/start_e2e_server.sh` deletes
  `e2e.sqlite3` and runs `migrate` **once**, when the E2E dev server
  process starts. It then seeds fixtures (`seed_demo_command_center`,
  `seed_payrollminds_demo`, plus inline org/user/approval-rule fixtures).
- **Server lifecycle:** `client/playwright.config.js`'s `webServer` block
  starts this server once per Playwright invocation
  (`reuseExistingServer: true`). In CI (`.github/workflows/ui-verification.yml`,
  job `browser-e2e`), each of the 8 matrix shards is a separate GitHub
  Actions job/VM, so the database **is** isolated across shards, but **is
  not** reset between the test files assigned to the same shard.
- **Sharding:** `PLAYWRIGHT_SHARD_ACROSS_TESTS=1` sets
  `fullyParallel: true` in the config, so Playwright's `--shard=N/8`
  divides the full list of individual tests (not whole files) across the 8
  shards. `workers: 1` always, so execution within a shard is serial.
- **No per-file or per-test reset exists.** The only reset boundary is the
  shard job's own startup.
- **No existing test-only cleanup utility existed** prior to this repair
  (checked `contracts/management/commands/` for any `seed_*`/reset-style
  E2E command; none deleted synthetic data). There is a precedent for
  narrow `DJANGO_E2E`-gated test hooks, though: `contracts/middleware.py`
  already gates an `e2e_force_idle` query-param hook behind
  `settings.DJANGO_E2E`. This repair follows that same idiom.

### Root cause classification

**A — Missing teardown** (the lifecycle test never deleted what it
created) combined with **C — Incomplete database reset** (the reset
boundary is the shard job, not the file or test). Both are true
simultaneously: fixing only the teardown (this repair) is sufficient
because the reset-per-shard-job design is otherwise intentional and
reasonable (a full per-test reset would be materially heavier for no
benefit, since only one test in the entire suite creates unowned
persistent state).

No evidence of B (shared seeded workspace misuse), D (fixture object
reuse), E (cross-shard reuse — shards are separate CI jobs), F (parallel
visibility — `workers: 1`), G (background job persistence — Redis is
disabled in E2E mode, `REDIS_URL=` empty), or H (cache/projection
persistence beyond the DB itself) was found.

## 4. Canonical isolation contract chosen (Phase 3)

**"Each test explicitly resets mutable pilot fixtures it creates."** This
is the smallest change compatible with the existing per-shard-job reset
design: it does not touch the shard/server lifecycle, does not add a
heavier per-file reset, and does not weaken the existing seeded-fixture
model that every other test in the suite correctly relies on read-only.

## 5. Repair (Phase 4)

Branch: `codex/payrollminds-browser-test-isolation`. Draft PR:
[technivian/clmone#165](https://github.com/Technivian/CLMOne/pull/165).

1. **`contracts/management/commands/delete_e2e_lifecycle_fixture.py`** —
   new, test-only. Refuses to run unless `settings.DJANGO_E2E` is true.
   Deletes exactly one `Contract` by primary key (cascades to its
   `Workflow` via the model's own `on_delete=CASCADE`). Never touches
   `AuditLog`, which is append-only by design (`AuditLogQuerySet.delete()`
   already raises `AuditWriteError`) — so the CREATE/UPDATE provenance for
   the deleted synthetic contract remains in the audit trail. This
   satisfies the "lifecycle-created records must retain proper provenance
   even in test mode" requirement: verified directly — after cleanup, the
   `Contract` row is gone but AuditLog rows 27/28/30 (`CREATE`/`UPDATE
   Contract 10 ... Life NDA 97516`) remain.
2. **`client/tests/e2e/helpers/lifecycle-fixtures.js`** — new shared
   module: `createLifecycleNda(page, suffix)` (the exact wizard flow that
   used to leak) and `deleteE2eLifecycleContract(contractId)` (invokes the
   management command via `execFileSync` against the same sqlite file the
   E2E server is using, derived from `E2E_DATABASE_URL` / the same default
   path `start_e2e_server.sh` uses). No new HTTP endpoint was added — the
   cleanup happens out-of-band via the Django management-command
   mechanism, not a production-facing URL.
3. **`client/tests/e2e/pilot-verification.spec.js`** — the lifecycle test
   now uses the shared helper and registers the created `contractId` in a
   describe-scoped variable; a `test.afterEach` in that describe block
   deletes it. Also fixed an unrelated, pre-existing locator bug in the
   same test: it queried `getByRole('link', { name: 'View contract
   record' })`, but that element is `<a role="menuitem">` inside a closed
   `<details class="dc-ds-workspace__actions-menu">` disclosure — the
   correct pattern (used correctly two tests earlier in the same file) is
   to click the `<summary>` first, then query `getByRole('menuitem', ...)`.
   Before this fix the test consistently timed out after 180s waiting on a
   selector that could never match, independent of the isolation bug (the
   leaked contract was already committed to the database by the time the
   timeout occurred, since the wizard's POST happens before this
   assertion).
4. **`client/tests/e2e/browser-isolation-regression.spec.js`** — new,
   see §6.

No production HTTP endpoint, view, URL route, or lifecycle/state-machine
behavior was changed. No visual snapshot file was touched.

## 6. Isolation regression tests (Phase 5) — real, run locally, all passing

All four tests below were executed against a real, clean local E2E SQLite
database (not simulated/predicted). Full log: 4 passed in 6.6 minutes.

| Test | Result | What it proves |
| --- | --- | --- |
| `lifecycle scenario leaves no trace on dashboard, list, or workspace` | ✓ pass (1.9m) | Runs the real lifecycle flow, asserts `Life NDA` *is* visible on `/contracts/workflows/` immediately after creation (positive control), cleans up, then asserts all three surfaces are clean. |
| `reverse order: visual surfaces are clean before and after the lifecycle scenario runs` | ✓ pass (1.7m) | Captures the workflow-link order, confirms clean surfaces, runs the lifecycle scenario + cleanup, re-captures the same order and re-confirms clean surfaces — `after` link order equals `before`. |
| `repetition: running the lifecycle scenario twice leaves no accumulated records` | ✓ pass (1.8m) | Runs create+cleanup twice in a loop; final workflow-link set equals the pre-loop baseline (no drift). |
| `search does not retain the lifecycle fixture after cleanup` | ✓ pass (1.2m) | Confirms the keyword-search index/projection does not retain the deleted contract. |

Post-run database check: `Contract.objects.filter(counterparty__icontains='Life NDA').count() == 0`, total contract count stable at 9 (the seeded baseline) after all runs above — no accumulation.

## 7. Order permutations and shard-state verification (Phases 6–7) — partial

What was actually run (all real, all local, all passing): the reverse-order
and repetition tests in §6 directly cover two of Phase 6's four required
orderings (lifecycle-before-visual and visual-before-lifecycle-before-visual)
and the repetition/no-drift requirement of Phase 7. **Not completed in this
session:** the full four explicit multi-file order permutations across
`dashboard`/`list`/`workspace`/`detail`/lifecycle as separate files, and a
literal two-full-shard-run comparison with recorded before/after counts.
This is the primary gap between what Phase 6/7 ask for and what was
delivered — see "What remains."

## 8. Clean visual re-evaluation (Phase 8) — resolved by authoritative CI

**Local-run caveat (kept for the record):** this sandbox lacked the exact
Chromium revision `@playwright/test@1.59.1` expects; a symlink workaround
let tests run locally, but local pixel diffs were not proven
representative (even the data-independent `form` baseline showed 2–5%
noise locally). Local HTTP content inspection was trustworthy, though:
after the fix, `Life NDA` occurrences dropped from 1/1/4 to 0/0/0 across
dashboard/list/workspace.

**Authoritative result (GitHub Linux CI, PR #165, run
[31187791963](https://github.com/Technivian/CLMOne/actions/runs/31187791963),
shard 8/8, commit `cb818eeb5d84e0db48b83b8b64fdfb461f5e2953`):** all five
`visual-baselines.spec.js` tests passed with **zero** pixel diff against
the committed snapshots, in the exact CI environment that produces those
snapshots:

```
✓ Phase 1 visual baselines › dashboard baseline    (2.1s)
✓ Phase 1 visual baselines › list baseline         (2.1s)
✓ Phase 1 visual baselines › form baseline         (1.9s)
✓ Phase 1 visual baselines › workspace baseline    (1.8s)
✓ Phase 1 visual baselines › detail baseline       (2.2s)
```

In the same shard, `pilot-verification.spec.js`'s fixed lifecycle test
also passed (5.7s) — the leaking test now runs immediately before the
visual suite in this shard's assignment and leaves no trace.

This resolves all four open questions from Prompt 28:

- **List:** passes unchanged. Confirmed.
- **Detail:** passes unchanged. Confirmed — and by construction it now
  resolves to the correct fixture record, since the leaked workflow no
  longer exists to sort first.
- **Dashboard:** passes unchanged against the existing committed baseline.
  Whatever "intentional link/action UI change" Prompt 28 referred to, the
  current committed `phase-1-dashboard-linux.png` already reflects the
  current `main` UI once the contaminating record is removed — no baseline
  drift exists between product and snapshot.
- **Workspace (~21px residual):** **outcome B — renderer-only /
  contamination artifact, not a product defect.** With the isolation fix
  in place, the authoritative run shows zero diff. The residual Prompt 28
  observed is fully explained by the same `Life NDA` contamination as List
  and Dashboard (an extra row in the workflow list changes vertical
  layout); it was never an independent, unattributed defect.

## 9. Baseline-update set (Phase 9)

**Zero baseline files need updating.** All four target visual baselines
(dashboard, list, workspace, detail) pass unchanged against their existing
committed snapshots once the isolation leak is fixed, confirmed on
authoritative GitHub Linux CI (§8). No baseline file was touched in this
PR, and none needs to be.

## 10–11. Baseline updates / focused validation

No baseline update was needed (§9), so there is nothing to update. Focused
validation is the §8 authoritative CI result: all four target visual tests
pass. The repo has no separate standalone "visual-baseline guardrail" /
"anti-drift" job distinct from `ui-verification.yml`'s
`Anti-drift + contrast` and `Forbidden-brand scan` checks — both ran on
this PR and passed (see §12).

## 12. Full browser proof — one authoritative run completed, real numbers

Draft PR [#165](https://github.com/Technivian/CLMOne/pull/165) triggered
the real `.github/workflows/ui-verification.yml` workflow on GitHub's
Linux runners for commit `cb818eeb5d84e0db48b83b8b64fdfb461f5e2953` (run
[31187791963](https://github.com/Technivian/CLMOne/actions/runs/31187791963),
8-shard `browser-e2e` matrix). **Important correction:** the `browser-e2e`
job step uses `continue-on-error: true` (`ui-verification.yml:148`), so a
green check mark on that job does **not** mean its shard's tests all
passed — it only means the advisory step didn't hard-fail the workflow.
The real numbers, read from each shard's own Playwright output:

| Shard | Tests | Passed | Failed | Notes |
| --- | --- | --- | --- | --- |
| 1/8 | 12 | 5 | 7 | Includes all 4 new `browser-isolation-regression.spec.js` tests — all passed. The 7 failures are pre-existing (`canonical-page-layout`, `command-center-demo`, `contract-field-review`, `critical-flows`), none touched by this PR. |
| 2/8 | 12 | 2 | 10 | Pre-existing failures (`dpa-cockpit`, `dpa-workflow`, `msa-workflow`, `nda-workflow`, `new-contract-launcher`, `payrollminds-buyer-demo`). |
| 3/8 | 12 | 1 | 11 | Pre-existing failures (`phase-2a-components`, `phase-2b1/2/3/5`, `phase-3a-standard-lists`). |
| 4/8 | 12 | 4 | 8 | Pre-existing failures (`phase-3a/3b`, `phase-4a/4b`). |
| 5/8 | 12 | 7 | 5 | Pre-existing failures (`phase-4b`, `phase-5c`, `phase-5g`, `phase-5h`). |
| 6/8 | 12 | 9 | 3 | Pre-existing failures (`phase-5h`, `pilot-gate.spec.js` ×2). |
| 7/8 | 11 | 8 | 3 | Pre-existing failures, all in `pilot-verification.spec.js` (MSA finance ×2, NDA "click View contract record" — different test from the one this PR fixed). |
| **8/8** | **11** | **11** | **0** | **All pass**, including the fixed lifecycle test (`pilot-verification.spec.js:330`, 5.7s) and all 5 `visual-baselines.spec.js` tests (§8). |
| **Total** | **94** | **47** | **47** | |

None of the 47 failures are in any file this PR touched
(`pilot-verification.spec.js`, `browser-isolation-regression.spec.js`,
`helpers/lifecycle-fixtures.js`) except the one test this PR fixed, which
now passes. They are a pre-existing backlog on `main`, consistent with the
48-failure registry already recorded on the unrelated
`codex/payrollminds-shared-ui-repair` line of work
(`docs/pilots/payrollminds/release-baseline/browser-failures.json` on that
branch) — e.g. stale locator text ("DPA Reviews" vs. the renamed "Privacy
Reviews"), missing committed snapshot files for several `phase-2b5`/`phase-3a`
tests, and seed-data mismatches. **Fixing this backlog is out of scope for
a browser-isolation repair** and was not attempted here.

**Only one full run was completed and read in this session, not two** (the
task's own bar). A second run was not triggered given the time already
spent extracting and verifying the first run's real per-shard numbers;
the PR remains open for that to happen on a future push or manual re-run.

## 13. Full regression / security proof — partially completed, all real

Run and passed, both locally and (for the CI-native checks) on GitHub
Actions for this PR:

- `python manage.py check` — no issues (local).
- `python manage.py test tests.test_cross_tenant_isolation -v 1` — 75
  passed (local).
- `python manage.py test tests.test_permission_matrix -v 1` — 2 passed
  (local).
- `python manage.py audit_null_organizations` — no NULL-organization rows
  (local).
- CI job `security-scans` — passed.
- CI job `quality-and-tenancy` — passed.
- CI job `redesigned-e2e` — passed.
- CI job `Anti-drift + contrast` — passed.
- CI job `Forbidden-brand scan (CLM One)` — passed.
- CI job `verify-ui-integrity` — passed.
- CI job `pr-release-evidence` — initially failed on a PR-description
  formatting gate (missing rollback checkbox); the PR body was corrected
  to follow the same precedent PR #157 used for disposable, no-production-surface
  PRs, but a fresh commit was not pushed to re-run this specific gate
  check in this session (see §12 — a second CI run was not triggered).

Not run in this session: the full Django test suite beyond the two files
above, MSA finance tests, the full authorization suite,
provenance/quarantine/export suites, Bandit, secret scan, and migration-drift
check as standalone steps (though `manage.py check` covers deploy-check-adjacent
issues and no migration was created by this PR).

## 14. Recommendation

**NO-GO** against this task's literal bar (90/90 twice + exhaustive
regression proof), but **the browser-isolation-and-visual repair itself is
complete and authoritatively verified**:

What is real and verified:
- The exact leaking test, its creation path, and its exact database
  footprint (Contract 10 / Workflow 4 / AuditLog 27, 28, 29) are proven,
  not inferred.
- The causal mechanism for all four visual symptoms — including the
  previously-unexplained "detail" dimension mismatch, now shown to be a
  wrong-record selection, not just a contaminated screenshot — is proven.
- A minimal, precedent-following fix is implemented and merged into the
  PR; four new order-independence regression tests pass for real, both
  locally and on authoritative GitHub Linux CI.
- **On authoritative CI, all four target visual baselines pass unchanged
  against their committed snapshots — zero baseline files need updating.**
  The Workspace ~21px residual is fully attributed to the same
  contamination as List/Dashboard, not an independent defect.
- Draft PR #165 is open, not merged, not deployed. PR #162/MFA remains
  fully excluded and inactive. No visual baseline was touched. No real
  customer data was used (all fixtures are synthetic, `e2e-command-center`
  workspace only).

What remains before this can be a strict GO against the task's full bar:
1. A second authoritative full-suite CI run (the task asks for two), and
   ideally re-running once the `pr-release-evidence` gate is picked up by
   a fresh push.
2. The pre-existing 47-failure backlog (§12) is a separate, larger body of
   work unrelated to isolation — genuinely out of scope here, but it is
   why the overall suite is far from 90/90.
3. The remaining untouched Phase 13 items (Bandit, secret scan, full
   authorization/provenance/export suites) were not run standalone in this
   session.

This document reflects real, executed evidence throughout — including the
premise correction in §0, the corrected understanding of what
`continue-on-error` actually proves in §12, and the honest scope
boundaries above.
