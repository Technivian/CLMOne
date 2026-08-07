# Browser baseline classification and repair

Status: **NO-GO**. This is a working evidence record, not release approval.
No merge, deployment, real customer data, live credentials, inbound email,
external AI, signatures, or external portals were enabled.

## Runner assessment

`origin/main` is `4d194dcc0663b94accf4eb892c508fe70cf2d3a7`.
The runner repair is PR #153, currently at
`12c82a34c3d02227287dd97f56d758443082559e`. Its runner-specific validation
passes on supported local Bash 3.2:

* unset and explicitly empty argument paths run the configured suite;
* one argument, multiple arguments, and an argument containing a space retain
  their boundaries;
* invalid shards fail with exit code 2;
* no `eval` or unsafe word splitting is used;
* the Playwright command exit status is returned;
* `.github/workflows/ui-verification.yml` contains no `continue-on-error`.

The PR evidence, security, integrity, and runner-specific checks are distinct
from Playwright assertions. Browser-shard failures therefore indicate
substantive tests, not the former empty-array runner defect.

## Authoritative browser collection

The locked Playwright manifest contains **90 tests in 28 files**:

```sh
npm --prefix client exec -- playwright test --config=client/playwright.config.js --list
```

The previous local diagnostic was interrupted by its outer session after 61
tests. That is not accepted as a terminal baseline. CI's eight isolated shards
continue to collect and execute their assigned tests; their assertion failures
remain visible because masking was removed. The first terminal CI run is
`30767778512` for PR #153 SHA `12c82a34c3d02227287dd97f56d758443082559e`:
**38 passed and 52 failed**. The complete two-run browser baseline and
`release-baseline/browser-failures.json` are not yet complete.

## Repairs in PR #154

PR #154 (`9ffe2b67f7946c0aef340bb5b1490306832b7da7`, pending remote CI) corrects
three stale browser expectations in `pilot-verification.spec.js`:

| Original failure | Classification | Repair | Validation |
| --- | --- | --- | --- |
| Legal-review blocker count checked while a `<details>` actions menu was closed | D — stale expectation | Open menu, then require no visible blocked action after resolution | Preserves blocked-state assertion |
| NDA legal-review explanation expected while actions menu was closed | D — stale expectation | Open menu before asserting the disabled explanation | Disabled feature remains disabled |
| Contract-record action selected as a link despite `role="menuitem"` | D — stale expectation | Assert/click the canonical `menuitem` role | Focused lifecycle test: 1 passed |

The focused `pilot-verification.spec.js` run produced **14 passed and 3
failed** before the final lifecycle-role repair. The corrected lifecycle test
then passed. The remaining two failures are MSA finance/legal workflow journeys:
their actions remain disabled because drafting sections are incomplete. They are
currently classified **F — unresolved** pending scope and workflow-state root
cause analysis; no blocked action was forced clickable and no assertion was
weakened.

The second terminal browser run is `30768405771` for PR #154 SHA
`8fa8be5b51fbaeb10ba379ecc44827ef7409b640`: **40 passed and 50 failed**.
The two repaired pilot expectations account for the two-test improvement from
the PR #153 runner baseline; the remaining MSA journeys are still failures.
This is not a stable two-run pass result: the two runs used different SHAs and
both retain unresolved failures.

## MSA finance and legal journey repair

Both remaining MSA failures were **A — incomplete happy-path fixture**. The
browser helper created the canonical MSA with an empty `special_conditions`
field. The generated document has a Special Conditions drafting section, whose
canonical rule reports `Needs input` when that field is empty. Human
confirmation only resolves `Needs review` sections, so the governed submission
actions correctly remained disabled.

The repair supplies the ordinary `special_conditions` input, keeps the initial
blocked-action and visible-reason assertions, resolves the recorded exception,
confirms each AI-assisted section through its server-side endpoint, and then
submits through the existing Finance or Legal route. It does not mutate a
workflow state in the browser, change permissions, or bypass a disabled
action. The audit route is now opened through the canonical Actions menu after
submission, rather than a non-existent header button.

Focused evidence on the repaired fresh worktree:

```text
PLAYWRIGHT_TEST_TIMEOUT_MS=30000 npm --prefix client run test:e2e -- \
  client/tests/e2e/pilot-verification.spec.js --grep 'MSA finance threshold matrix'

2 passed (29.6s)
```

The affected file is `client/tests/e2e/pilot-verification.spec.js`. This is a
test-fixture and governed-expectation correction only: migration impact is
none; security, tenancy, and authorization behavior are unchanged; submission
continues to create the existing approval and immutable audit evidence.

## Registry status

`release-baseline/browser-test-manifest.json` records the exact 90-test
Playwright collection, including stable IDs, source locations, titles, and
project. `release-baseline/browser-failures.json` has one schema-complete
record for each of those 90 tests. Its run-result and classification fields are
explicitly `pending`; it must not be used for exception analysis until two
same-SHA clean runs and two same-SHA repaired runs provide the required
terminal evidence.

## Current blocker and next required evidence

The branch cannot be declared ready for UAT/envelope work until all 90 tests
reach terminal states in two equivalent runs and every failure is individually
classified. Mandatory browser infrastructure, PayrollMinds-critical, shared
platform, or security/tenancy failures must be repaired. Only deterministic,
isolated, inherited non-pilot assertion failures may later be considered for a
separate proposed exception; no exception has been created here.

## Prompt 21 and Prompt 22 repair evidence

The historical runner observations above remain retained for traceability.
They are superseded as the current local source-SHA result by the focused
repair evidence below; they are not release approval or CI evidence.

On implementation SHA `50aae7d4f090e36eff08a1a0b19ad747373185c6`, the
Prompt 21 category-B collection passed **16/16** and the Prompt 22 exact
shared workflow/Contract Record selection passed **7/7**. A subsequent
unfiltered local collection completed **90/90** tests: **59 passed, 31 failed,
0 skipped, 0 interrupted**. No category-B or `D-SHARED-WORKFLOW` stable
identifier failed, and no new stable identifier appeared.

The residual 31 records are the already-classified shared-UI and visual
baseline records. Their source, classification, and proposed repair ownership
remain in `release-baseline/browser-failures.json` and
`release-baseline/browser-root-cause-clusters.json`; this task did not alter
them, create an exception, or normalize any failure as a pass. The current
release posture remains **NO-GO** until the remaining browser failures,
full-unit baseline comparison, security scans, CI, and required independent
release approvals are complete.

## Prompt 23 shared UI repair evidence

Implementation commit `3f5bb5c3ee65367a2bcd9c86810bad1a3235719a`
repairs exactly the 26 `D-SHARED-UI` records. The exact registry selection is
26 passed and the 13 complete affected files are 34 passed. Corrections cover
mobile table containment, repository error semantics, Contract Record dialog
focus return, owned Command Center navigation, approved current terminology,
retired route assertions, deterministic populated/empty list state, and
semantic coverage replacing non-governed file-local screenshots.

The visual-baseline spec and all five committed Linux assets are unchanged.
No test was removed, skipped, retried, excluded, or broadly accepted. PR #161
preservation is 16 passed; PR #163 exact/affected preservation is 7/7 and
11/11; PayrollMinds verification is 17 passed. Full Linux browser and Django
signature evidence remain required before registry closure; the release remains
**NO-GO**. Detailed traceability is in `SHARED_UI_REPAIR.md`.
