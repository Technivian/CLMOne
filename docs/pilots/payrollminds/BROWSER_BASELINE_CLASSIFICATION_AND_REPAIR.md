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

## Current blocker and next required evidence

The branch cannot be declared ready for UAT/envelope work until all 90 tests
reach terminal states in two equivalent runs and every failure is individually
classified. Mandatory browser infrastructure, PayrollMinds-critical, shared
platform, or security/tenancy failures must be repaired. Only deterministic,
isolated, inherited non-pilot assertion failures may later be considered for a
separate proposed exception; no exception has been created here.
