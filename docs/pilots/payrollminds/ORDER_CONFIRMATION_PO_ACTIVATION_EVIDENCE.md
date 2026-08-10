# Order Confirmation and Purchase Order activation readiness

**Starting main SHA:** `a329b805952befefa7924ddc943badca9ed8ed4b`
**Assessment date:** 2026-08-10
**PR #181 head:** `1f11e622d6bcf1b8e14950e9442fa05419fe6c48`
**Environment status:** **OC/PO EXECUTION ENVIRONMENT GREEN — ACTIVATION IMPLEMENTATION MAY CONTINUE**
**Production-activation status:** **NO-GO**

## Reproducible execution-environment repair and baseline

The original local virtual environment was not a safe source of release
evidence. Its `bin/python` target was the valid repository-supported
CPython 3.12.13 installation, but its generated `pip`, `pip-audit`, and
`bandit` console scripts had a stale shebang pointing to the removed
`/Users/haroonwahed/Documents/Projects/CMS-Aegis/.venv/bin/python`.
This was a machine-local virtual-environment corruption, not an application
or dependency defect. It was not patched or symlinked.

The broken `.venv` was moved to the recoverable temporary location
`/tmp/clmone-broken-venv.IdE78T/venv`, then recreated with the existing
CPython 3.12.13 toolchain. The new environment installed successfully from
the committed dependency source `requirements.txt` → `requirements/dev.txt`
→ `requirements/runtime.txt`; this repository has no lockfile. No dependency
was upgraded outside those committed pins, and no virtual-environment or
machine-local file is tracked.

| Item | Result |
| --- | --- |
| Rebuilt interpreter | CPython 3.12.13 |
| pip | 25.0.1 |
| Django | 5.2.16 |
| `python manage.py check` | pass (0 issues) |
| `python manage.py makemigrations --check --dry-run` | pass; no changes detected |
| Baseline worktrees | clean detached worktrees at main `a329b805952befefa7924ddc943badca9ed8ed4b` and PR head `1f11e622d6bcf1b8e14950e9442fa05419fe6c48` |

### Django baseline comparison

The same command and test environment were used in both clean worktrees:
`DJANGO_SETTINGS_MODULE=config.settings_test .venv/bin/python manage.py test --verbosity 0`.

| Result | Main (`a329b805`) | PR #181 (`1f11e622`) |
| --- | ---: | ---: |
| Collected | 2,651 | 2,651 |
| Passed | 2,574 | 2,574 |
| Failed | 31 | 31 |
| Errors | 38 | 38 |
| Skipped | 8 | 8 |
| Exit status | 1 | 1 |

The normalized set of all 69 failing/error test identifiers is identical on
both revisions: **INHERITED: 69; RESOLVED: 0; NEW: 0; MUTATED: 0**. It includes
the documented missing-`pytest` imports and the existing lifecycle/status,
storage-integration, e-sign, and UI-contract drift. No PR #181 signature has
an OC/PO test ID, because this branch contains evidence only and does not add
OC/PO implementation coverage.

### Security, migration, and UAT baseline

All of the following were run against both main and PR #181 with the rebuilt
environment. The PR result matched the main result.

| Gate | Invocation/scope | Main | PR #181 |
| --- | --- | --- | --- |
| Python dependency audit | `pip-audit --disable-pip --no-deps -r requirements/runtime.txt` | pass; no known vulnerabilities | pass; no known vulnerabilities |
| Static security | `bandit -q -r contracts config -lll` | pass | pass |
| Migration drift | `manage.py makemigrations --check --dry-run` | zero | zero |
| PayrollMinds UAT | `manage.py test tests.test_payrollminds_executable_uat -v 1` | 24/24 pass | 24/24 pass |
| npm baseline | CI-equivalent `scripts/check_npm_audit_baseline.py --base-ref a329… --verify-github-approvals` | current dependency tree unchanged | pass; no new, worsened, or unexcepted findings |

The TruffleHog result is deliberately limited to the repository-supported PR
range rather than a raw filesystem/history sweep. Version 3.96.0 was run with
the documented CI-compatible scope: `git file:///…/CLMOne --since-commit
a329b805… --branch 1f11e622… --fail --no-update
--results=verified,unverified,unknown`. It completed successfully with four
chunks / 5,284 bytes and **0 verified, 0 unverified secrets**. There is no
secret finding, fixture exception, or new suppression in this PR range.

### Historical dependency-finding reconciliation

The earlier generic count of five did not itself preserve a five-row advisory
list. The rows below are the five historical remediation groups recoverable
from committed dependency history; current authoritative scans find no
remaining known vulnerability in the committed runtime resolution or npm
baseline.

| Historical finding | Current status | Package | Installed version | Fixed version | Release blocking? |
| --- | --- | --- | --- | --- | --- |
| `CVE-2026-71852` | resolved before current main | pypdf | 6.15.0 | 6.15.0 | no |
| `GHSA-2v37-7h3g-55p8` | resolved before current main | nanoid (client lock) | 3.3.18 | 3.3.18 | no |
| `GHSA-MH99-V99M-4GVG` | resolved before current main | brace-expansion (theme lock) | 5.0.9 | 5.0.8, later 5.0.9 | no |
| historical cryptography advisories | resolved before current main | cryptography | 50.0.0 | 50.0.0 | no |
| historical PostCSS build advisory | resolved before current main | postcss (client/theme locks) | 8.5.25 | 8.5.25 | no |

No stale count has been used as a current finding, and no dependency update
was made during this baseline task.

### Browser-runner capability

`npm --prefix client ci`, `npm --prefix client exec playwright install
chromium`, and `npm --prefix client exec playwright test -- --list` completed
successfully. The browser runner collected a manifest of **94 tests in 29
files**. The deterministic isolated E2E server then started with a local
SQLite `e2e.sqlite3` and returned HTTP 200 from `/login/`; it was stopped
immediately after readiness was proved. No browser tests, screenshots, or
snapshot updates were run in this task.

## PDR-0008 production closure

PDR-0008 is recorded as **PDR-0008 PRODUCTION DEPLOYMENT GREEN** in
`PRIVATE_BY_DEFAULT_ACCESS_IMPLEMENTATION.md`. The deployment SHA, rollback
SHA, health, login/application smoke result, and Auto-Deploy OFF state are
operator-attested; this assessment does not claim independent Render-provider
observation. No contract type was activated by that deployment.

## Current implementation trace

Both candidate types are canonical values in `Contract.ContractType` and the
ContractType catalogue migration: `ORDER_CONFIRMATION` and `PURCHASE_ORDER`.
Both have required fields (`counterparty`, `governing_law`, `jurisdiction`) and
Commercial Counsel launch metadata. They use the ordinary Contract Record,
Document/DocumentVersion, audit, export, search, dashboard, deadline, and
workflow inheritance paths; no type-specific private-access branch exists.

The blocked intake path is concrete. `contract_template_picker` renders both
types as procurement cards and points them at the generic Contract create
route with a `type` query parameter. In a controlled pilot,
`ControlledPilotScopeMiddleware` allows only MSA, NDA, and DPA builder
prefixes and rejects the generic create path. Consequently neither candidate
can be created through the controlled-pilot intake flow. This is intentional
current scope enforcement, not a broken enum or template mapping.

## Private-access inheritance

PDR-0008 authorization is contract-object based, not contract-type based.
Its documented enforcement covers Contract reads, direct detail, repository,
search/counts/autocomplete, documents and versions, workflow/work items,
exports, comments, and AI. Thus OC and PO would inherit owner/creator
visibility, same-workspace unrelated-member denial, cross-workspace denial,
revocation, and non-disclosure automatically once a governed Contract Record
exists. No type-specific authorization logic is proposed.

This assessment does not count that generic proof as the required per-type
executable coverage: OC and PO lifecycle/access tests have not yet been added
or executed.

## Security and regression status

The execution environment, security scans, migration state, UAT, full-suite
baseline, normalized comparison, vulnerability reconciliation, and browser
manifest are now recorded above. The full Django suite remains non-green, but
its complete 31-failure / 38-error result is inherited unchanged from approved
main and is not attributed to PR #181.

No OC/PO lifecycle test or browser test has been added or executed, no
accessibility run has been performed, and no migration has been added by this
assessment.

## Remaining gaps and recommendation

1. Add a default-off, server-side controlled-pilot OC/PO intake gate that
   permits only the two candidate types and continues to deny SOW, Vendor,
   Employment, SaaS, Lease, OTHER/Custom, generic upload/import, and every
   other inactive type.
2. Add and run separate deterministic OC and PO lifecycle/access/export/audit
   coverage, including private-access and non-disclosure cases.
3. Add and run authoritative browser coverage for both types.
4. Add and execute the remaining per-type browser and accessibility evidence
   after the narrowly scoped activation implementation exists.

**Recommendation: NO-GO.** Order Confirmation and Purchase Order remain
**BUSINESS SCOPE APPROVED / TECHNICAL IMPLEMENTATION GATE OPEN / PRODUCTION
ACTIVATION NO-GO**. Nothing in this readiness assessment deployed, changed a
production flag or environment, created production data, or activated a
contract type.
