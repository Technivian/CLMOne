# MSA finance-threshold determinism repair

Status: **FINANCE-THRESHOLD BLOCKER REPAIRED**.

This record covers the single unexpected functional failure in the PayrollMinds
Linux browser gate. It is not a release approval, merge instruction, deployment
authorization, snapshot acceptance, or MFA activation.

## Immutable source and tree comparison

| Evidence | Value |
| --- | --- |
| PR | `#164` |
| Initial source SHA | `d0af8f45f238be94977160969934aec5a9af56f7` |
| Initial source tree | `2f5cdedc7ac46bfe0c3ab6d07f064776170c1e82` |
| Base SHA | `b0f09bbef6a625a8b60b2b9058399f0e7ee7a614` |
| GitHub checkout merge SHA | `088077f251d02f3fcb87ba362e0a84cbcf416f1e` |
| GitHub merge tree | `2f5cdedc7ac46bfe0c3ab6d07f064776170c1e82` |
| Repair SHA | `07e63917074d31c1a8bbc43ef2ac678b5c307609` |

The source and GitHub merge trees are identical. `git diff --stat` and
`git diff --name-status` between the two commits are empty. The original
contingency runs and GitHub therefore exercised identical file content; this is
not root-cause class A.

## Original GitHub failure and contingency comparison

Authoritative workflow `UI Verification`, run `31163790174`, attempt 1,
collected and executed all 90 tests: 85 passed and five failed. Four failures
were the established visual-baseline records. The only unexpected functional
record was:

- stable ID `85a61e5caf109bed6bc0-1536b35a836e87581f42`;
- scenario `MSA finance-threshold workflow`;
- expected `0 exceptions · 0 need review`;
- observed `1 exceptions · 1 need review`;
- stack: `clearDraftingBlockers`, invoked for the above-threshold MSA at
  `client/tests/e2e/pilot-verification.spec.js:230`.

Two independent Ubuntu 24.04 contingency matrices on the same source tree each
executed 90/90 and produced 86 passes plus only the four known visual failures.
Shard 7 passed 11/11 in both.

## Canonical finance inputs and policy

PDR 0001 is the governing rule. The threshold is exactly `Decimal('100000')`
in the stated contract currency during the pilot, with no FX conversion.
`total_contract_value` takes precedence over recurring value and headline
value. Unknown value does not trigger Finance by value alone. A value at or
above the threshold, or explicit operator confirmation, triggers the canonical
Finance review route.

The browser fixture explicitly supplies:

| Case | Value | Currency | Confirmation | Payment terms | Expected finance signal |
| --- | ---: | --- | --- | --- | --- |
| Below | `99999` | `EUR` | false | `Net 30` | none |
| Boundary | `100000` | `EUR` | true | `Net 30` | one, then explicit resolution |
| Above | `100001` | `EUR` | true | `Net 30` | one, then explicit resolution |

Other material inputs are deterministic: Netherlands governing law, manual
renewal, standard liability wording, normal special-conditions text, and the
same pinned MSA workflow template/version.

## Browser-to-domain trace

1. `generateMsa` submits `/contracts/new/msa/`.
2. `MSAWorkflowBuilderView.post` validates the seeded field definitions.
3. `create_msa_workflow_instance` creates the tenant-owned Contract, pinned
   Workflow, FieldValues, DraftDocument, RiskSignals, Command Center item and
   append-only audit rows in one transaction.
4. `finance_threshold_from_field_values` calls `requires_finance_approval`
   using exact Decimal coercion and the PDR threshold.
5. `detect_msa_risk_signals` creates `finance_approval_required` only for the
   boundary and above-threshold cases.
6. The workflow detail view projects unresolved RiskSignals into exception
   cards and maps their section to the document overview.
7. `clearDraftingBlockers` posts the existing `use_approved_wording` action,
   then posts human section confirmation. Both actions emit existing audit
   events and are server-authorized.

For every successful isolated run the pre-scenario fixture was stable: three
organizations, nine contracts, three workflows, seven seeded RiskSignals,
96 FieldValues, 25 audit events, MSA template ID 2/version 1, 39 MSA fields and
threshold `100000`. Post-scenario state was also stable:

- below: no finance RiskSignal and no exception-resolution event;
- boundary: one resolved `finance_approval_required` signal, one
  `risksignal.msa_exception_use_approved_wording` event, and the services
  section confirmation;
- above: the same governed signal/resolution/confirmation shape;
- all three records remained in organization ID 1 and on template ID 2.

## Environment comparison

| Input | GitHub attempt 1 | Contingency/focused Ubuntu |
| --- | --- | --- |
| OS | Ubuntu 24.04.4 GitHub image | Ubuntu 24.04.4 Playwright image |
| Architecture | x86_64 | x86_64 under isolated amd64 execution |
| Python | 3.12.13 | 3.12.3 |
| Node | 20.20.2 | 20.20.2 |
| Playwright | 1.59.1 | 1.59.1 |
| Chromium revision | 1217 | 1217 |
| Django | 5.2.16 | 5.2.16 |
| Database | fresh per-shard SQLite | fresh per-execution SQLite 3.45.1 |
| Locale/timezone | runner defaults / application UTC | `C.UTF-8` / application UTC |
| Workers | one worker in shard 7 | one worker |
| Retry | zero | zero |

The source tree, locked dependency inputs, feature flags, policy seed, currency,
threshold, worker count and test order are the same. The Python patch and local
SQLite differences cannot change the pure Decimal policy result and are now
covered below the browser under Dutch locale and a non-UTC timezone.

## Focused pre-fix reproduction

The exact initial source was run 20 times in isolation in fresh Ubuntu 24.04
containers. Result: **20 passed / 0 failed**. Each execution recorded the
environment, pre-state, canonical inputs, RiskSignals, FieldValues and audit
events. Four-container batches intentionally exercised loaded-host timing but
did not change the governed result.

Shard 7 contains 11 tests and the finance scenario is first, so there are no
preceding shard-7 tests. Exact-order shard 7 was run twice on the initial source
with one worker: **11/11 passed** both times. This rules out a preceding test in
that shard as the input.

The single permitted native GitHub diagnostic rerun was run as attempt 2 of
`31163790174`. Shard 7 passed **11/11** and the finance scenario passed in
15.8 seconds. The original failed attempt remains preserved. The pass on rerun
proves nondeterminism but is not release evidence.

## Root cause: F — asynchronous race

The governed finance policy and persisted state are deterministic. The failed
screen contained both the original unresolved finance exception and the
unconfirmed drafting section (`1/1`). Therefore neither loop in
`clearDraftingBlockers` performed a mutation. Both loops used immediate
`count()` probes; the only relevant rendered surface containing neither action
is the outgoing MSA builder form. The test waited for a workflow URL, but did
not establish that the redirected governed-workspace DOM was visible before
probing its actions. Under the original GitHub timing those probes ran against
the outgoing DOM; the later overview assertion then resolved against the loaded
workspace and exposed the untouched canonical `1/1` state.

This is not stale policy expectation: PDR 0001 requires the Finance route at
and above the boundary, while explicit exception resolution and section
confirmation are valid prerequisites before review submission. It is not
state leakage: the test is first in the shard and uses a fresh database. It is
not numeric, locale, timezone, random-order, cache or merge-tree drift.

## Correction and ownership

The correction is owned by PR #164 as shared browser/UI synchronization. The
MSA generator now waits concurrently for the workflow navigation through
`domcontentloaded`, then requires the canonical `[data-workspace-drafting]`
root and document overview to be visible before blocker discovery begins.

No threshold, exception, review count, permission, workflow state, domain
service or final Contract state was changed. No sleep, retry, skip, xfail,
snapshot update or direct state assignment was added.

Lower-level coverage now:

- uses exact Decimal values below, at and above the threshold;
- proves zero finance RiskSignals below the threshold;
- proves one canonical Finance RiskSignal at and above the threshold;
- proves no RiskSignal leakage between workflows;
- repeats the same sequence under Dutch locale and Pacific/Kiritimati timezone;
- proves prior above-threshold evaluation does not change later below-threshold
  evaluation and repeated evaluation is identical.

## Post-fix focused evidence

| Selection | Result |
| --- | --- |
| Finance policy + MSA workflow unit/domain tests | 35 passed |
| Exact finance browser scenario, fresh Ubuntu executions | 20/20 passed |
| Exact shard 7, two Ubuntu executions | 11/11 passed twice |
| Finance + Legal MSA journeys | 2/2 passed |
| Duplicate-submit stress | 20/20 passed |
| PayrollMinds verification | 17/17 passed |
| PR #161 preservation | 16/16 passed |
| PR #163 preservation | 7/7 exact records; 11/11 affected files passed |
| PR #164 exact shared-UI cohort | 26/26 passed |

## Authoritative browser and unit/security comparison

Fresh corrected GitHub `UI Verification` run `31168635206` executed PR #164
head `2796eda498ff3e9049e926d15a882fe04717cbf5`. It collected and executed all
90 tests: **86 passed, exactly four failed, zero skipped, zero interrupted and
zero not run**. Shard 7 passed 11/11 and the finance-threshold scenario passed
in 16.4 seconds. The only failures were the unchanged visual-baseline records:

- `257cfc15fcd93e8e1bb7-ad625d5c6d0960d42c47` — dashboard;
- `257cfc15fcd93e8e1bb7-f0db563020cdc84ca2c5` — list;
- `257cfc15fcd93e8e1bb7-4abae29fec94da448a20` — workspace;
- `257cfc15fcd93e8e1bb7-0c224bb7c0472c6e22ca` — detail.

The separate governed Phase 1 visual-baseline job passed without regenerating
assets. Anti-drift/contrast, redesigned E2E, quality/tenancy, release evidence,
security scans and brand checks all passed. The aggregate `verify-ui` job is
red only because it correctly propagates the four known shard-8 visual
failures.

The focused workflow/approval, tenant isolation, authorization, provenance,
audit and search/count selection ran 378 tests. Its four failures reproduce
identically on untouched `d0af8f45`; there is no new or mutated signature.
Finance policy and MSA tests pass 35/35. Dependency scans report no known Python
or runtime npm vulnerabilities, Bandit high severity passes, system and deploy
checks pass, and migration drift is empty.

The full Django run executed 2,629 tests. Because Docker Desktop was available,
22 live-MinIO tests ran and failed their external fixture setup instead of being
skipped as in the inherited comparison. Removing only those environment-only
MinIO signatures produces **34 failures / 13 errors**, exactly matching the
inherited `d0af8f45` baseline: no added, missing or mutated failure/error
signature. The two added passing regression tests account for the collection
increase from 2,627 to 2,629. The focused 378-test selection's four failures
also reproduce identically on untouched `d0af8f45`.

## Migration, rollback and recommendation

No model or migration changes are required. The repair is test synchronization
plus lower-level regression evidence. Rollback is a normal revert of the repair
commit; it has no data migration or product-state rollback step.

Recommendation: **FINANCE-THRESHOLD BLOCKER REPAIRED**. This closes only the
unexpected functional finance-threshold browser blocker. The four established
visual records remain separately open and release posture outside this bounded
repair is unchanged.

The four governed visual baselines are unchanged. Nothing is merged or
deployed. PR #162 and all MFA/authentication code remain excluded and MFA is
not activated.
