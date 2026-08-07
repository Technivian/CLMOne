# PayrollMinds Browser Test Isolation and Visual Repair

**Status: NO-GO.** Real, verified progress is recorded below — the root
cause is proven and fixed, and the fix is validated locally — but several
of this task's own success criteria (authoritative two-run GitHub Linux
90/90 proof, full Django/security regression comparison, final baseline
disposition) were not completed in this session. See "What remains" at the
end.

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

## 8. Clean visual re-evaluation (Phase 8) — inconclusive locally, caveat below

**Environment caveat (read before the numbers):** this sandbox does not
have the exact Chromium revision (`1217`) `@playwright/test@1.59.1`
expects; only an older pre-installed build (`1194`) is available. A
symlink workaround let tests run at all, but the rendered pixels are **not**
proven identical to whatever produced the committed baselines. Proof this
matters: even the **`form` baseline**, which has zero contract/workflow
data dependency, showed a 2–5% pixel diff on a fully clean database in this
environment. That is a local rendering-noise floor, not a product defect —
and it means none of the pixel-diff numbers below can be treated as
authoritative.

What *is* environment-independent (HTTP content inspection, not pixel
diffing) and therefore trustworthy:

- After the fix + cleanup, `Life NDA` appears **zero** times in the raw
  HTML of `/dashboard/`, `/contracts/repository/`, and
  `/contracts/workflows/` (previously 1, 1, 4 respectively).
- The workflow-link order used by the `detail` test's selector is
  deterministic and unaffected by the (now-cleaned-up) lifecycle test.

What is **not** established locally, and requires the authoritative GitHub
Linux CI run (Phase 12) to determine:

- **List:** expected to pass unchanged (content-level leak is proven
  fixed) — not pixel-confirmed in this session.
- **Detail:** expected to pass unchanged for the same reason, **and**
  because it will now resolve to the correct fixture record (workflow 3,
  not the leaked workflow 4) — not pixel-confirmed in this session.
- **Dashboard:** the previously-identified intentional link/action UI
  change is real product code on `main`; whether the committed baseline
  already reflects it or needs updating cannot be determined from pixel
  diffs produced by a mismatched local Chromium build.
- **Workspace (~21px residual):** **not attributed.** This session did not
  determine whether it is an intentional UI change, a renderer-only
  variation, or a remaining defect. Determining this requires repeated
  *authoritative* Linux CI runs (matching the exact browser build used to
  generate the current baseline), not this sandbox.

## 9. Baseline-update set (Phase 9)

**No baseline file was updated in this session.** Per the task's own
mandate ("do not update any visual baseline until isolation is proven" and
"do not update... until [Workspace] cause is unattributed"), and given the
local-pixel-evidence caveat in §8, no baseline decision can be honestly
finalized here. The isolation fix is proven; the pixel-level baseline
disposition is deferred to the authoritative CI run on PR #165.

## 10–11. Baseline updates / focused validation

Not performed — no baseline was determined to need updating with
authoritative evidence in this session (see §9).

## 12. Full browser proof — deferred to CI

This session pushed the fix and opened draft PR
[#165](https://github.com/Technivian/CLMOne/pull/165), which triggers the
real `.github/workflows/ui-verification.yml` workflow (8-shard browser-e2e
matrix) on GitHub's Linux runners — the authoritative environment. **Two
full 90/90 runs were not completed and confirmed within this session.**
Whatever the live CI status is at the time this document is read, treat
this section as superseded by the PR's actual GitHub Actions history, not
by any number written here.

## 13. Full regression / security proof — not completed

The following were run locally and passed, but do **not** constitute the
full Phase 13 proof:

- `python manage.py check` — no issues.
- `python manage.py test tests.test_cross_tenant_isolation -v 1` — 75
  passed.
- `python manage.py test tests.test_permission_matrix -v 1` — 2 passed.
- `python manage.py audit_null_organizations` — no NULL-organization rows.

Not run in this session: the full Django test suite, workflow/version
tests beyond the two files above, MSA finance tests, full authorization
suite, provenance/quarantine/export suites, dependency scans, Bandit,
secret scan, migration-drift check, and `manage.py check --deploy`. This
is the second primary gap versus the task's requirements.

## 14. Recommendation

**NO-GO.**

What is real and verified:
- The exact leaking test, its creation path, and its exact database
  footprint (Contract 10 / Workflow 4 / AuditLog 27, 28, 29) are proven,
  not inferred.
- The causal mechanism for all four visual symptoms — including the
  previously-unexplained "detail" dimension mismatch, now shown to be a
  wrong-record selection, not just a contaminated screenshot — is proven.
- A minimal, precedent-following fix is implemented, and four new
  order-independence regression tests pass for real against a clean local
  database, with no accumulation after repetition.
- Draft PR #165 is open, not merged, not deployed. PR #162/MFA remains
  fully excluded and inactive. No visual baseline was touched. No real
  customer data was used (all fixtures are synthetic, `e2e-command-center`
  workspace only).

What remains before this can become a GO for the browser-isolation-and-visual
cluster specifically:
1. Authoritative GitHub Linux CI results for PR #165 (two full runs,
   90/90, per the task's own bar) — pending at the time of writing; see
   the PR's Actions tab for current status.
2. Full Django/security/regression proof (Phase 13), only partially run
   here.
3. Full Phase 6/7 order-permutation and two-full-shard-run evidence,
   partially covered by the §6 regression tests but not exhaustively
   completed.
4. Workspace ~21px residual attribution (Phase 8), which requires
   authoritative-environment pixel evidence this sandbox cannot produce.
5. The final baseline-update decision (Phase 9), which depends on 1 and 4.

This document will need a follow-up pass, using the real CI results from
PR #165, before the release-cluster recommendation can move off NO-GO.
