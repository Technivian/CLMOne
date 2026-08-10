# Order Confirmation and Purchase Order activation readiness

**Starting main SHA:** `a329b805952befefa7924ddc943badca9ed8ed4b`
**Assessment date:** 2026-08-10
**Baseline subject PR #181 head:** `1f11e622d6bcf1b8e14950e9442fa05419fe6c48`
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

## Default-off activation implementation — 2026-08-10

**Implementation starting SHA:** `d9f106d29f8a010991fdf9355a994814f9164f16`
**Implementation final SHA:** commit containing this evidence (reported in the PR handoff).

### One canonical authority path

`Contract.ContractType` and the `ContractType` catalogue remain classification
authorities only. New controlled-pilot launch authority is centralized in
`contracts.services.contract_type_activation`:

1. `CONTROLLED_PILOT_ENABLED` activates the pre-existing pilot boundary.
2. `PAYROLLMINDS_ENABLED_CONTRACT_TYPES` is the explicit, valid-code allowlist.
   Its production-equivalent default is exactly `MSA,NDA,DPA`.
3. The same policy filters the New Contract cards and form choices; validates
   direct standard-intake requests and form POSTs; filters template selection;
   gates CSV preview/commit; and gates API upload-created Contract records.
4. The controlled-pilot middleware delegates standard-intake eligibility to
   that service, while generic creation, legacy upload/review, and CSV UI
   exposure retain their existing fail-closed restrictions.

Order Confirmation and Purchase Order are absent from the default allowlist.
They require a future, separately authorized environment configuration. An
active catalogue row, a route, a template, or a merged code change cannot
activate either type. Unknown values are discarded from the allowlist and
fail closed. No OC/PO-specific authorization branch was added: PDR-0008
remains the object-level authority after a type passes launch eligibility.

MSA, NDA, and DPA retain their existing dedicated builder routes. SOW and all
other cards now use the type-scoped standard route rather than the legacy
generic `?type=` route, so no active or future type can bypass the same server
policy. This is a routing correction only; it does not activate SOW or broaden
the configured cohort.

### Executable OC and PO evidence

`tests.test_oc_po_activation_policy` uses production-equivalent pilot settings
and deterministic test-only allowlisting. It proves separately for
`ORDER_CONFIRMATION` and `PURCHASE_ORDER`:

- default OFF: no card/form discoverability; standard route, direct generic
  create, legacy upload/review, CSV UI, CSV preview token, and upload-created
  Contract API cannot create an inactive type;
- test-only ON: real canonical form creation with correct organization, type,
  owner, `created_by`, catalogue mapping, private provenance lock, audit, and
  reopen/detail;
- canonical document attachment and immutable `DocumentVersion` linkage,
  version lock, and document audit;
- owner discovery/detail and unrelated same-workspace plus cross-workspace
  direct-ID denial; private repository/search/facet count non-disclosure;
- document, DocumentVersion, workflow and work-item inheritance; AI action
  eligibility no broader than Contract read; and immediate membership
  revocation;
- template selection stays on the type-scoped governed route.

The generic standard Contract path has no OC/PO-specific workflow definition
or automatic workflow instance. The evidence therefore does not invent one;
it proves the existing linked-workflow/work-item inheritance boundary. Export
inherits the same PDR-0008 Contract read rule and remains covered by the
existing canonical export authorization suite; no export surface was changed.

Negative coverage blocks `SOW`, `VENDOR`, `EMPLOYMENT`, `SAAS`, `LEASE`, and
`OTHER`, in addition to OC/PO when default-off. No `OTHER`/Custom, import,
upload, AI, signature, inbound-email, portal, or integration feature was
enabled.

### Browser and isolation evidence

`client/tests/e2e/oc-po-activation-readiness.spec.js` runs only against its
own disposable SQLite E2E server(s), with unique synthetic titles and cleanup
by database disposal; it never touches the shared E2E fixture or production
data. The local result is **3 passed / 0 failed / 0 skipped / 0 timed out**:

- default-off server: OC, PO, and representative inactive direct intake URLs
  are absent or redirected through the normal pilot convention;
- test-only-on server: Order Confirmation real browser intake, repository,
  detail/reopen, and unrelated-member direct detail/list denial;
- test-only-on server: the equivalent independent Purchase Order path.

The manifest moved from **94 tests / 29 files** to **97 tests / 30 files**.
The complete authoritative Linux browser manifest remains a PR CI gate; no
visual baseline was updated locally.

### Regression, quality, and security evidence

| Gate | Result |
| --- | --- |
| Focused OC/PO policy + template + changed DPA routing | 5 passed |
| Focused private-access / export / AI / tenant slices | 98 passed |
| Broader targeted set | 252 run; 3 failures + 1 error reproduce unrelated pre-existing launch-setup drift; all OC/PO, PDR-0008, document, tenant, UAT, MSA/NDA/DPA, workflow, and security slices passed |
| Full Django | 2,654 run; 31 failures, 38 errors, 8 skipped |
| Normalized comparison to main baseline | inherited 69; resolved 0; **new 0; mutated 0**. The three additional collected tests are green. |
| Django check / migration drift | pass / zero; **no schema migration required** |
| `pip-audit` | pass; no known vulnerabilities |
| Bandit (`contracts`, `config`, high severity) | pass |
| TruffleHog PR-range scan | pass; 0 verified, 0 unverified secrets |
| Local npm audit (`client`, production dependencies) | pass; 0 vulnerabilities |
| Design-system anti-drift | pass |
| Browser activation suite | 3 passed |

The implementation does not change production configuration, production
records, deployment configuration, Render, or a production contract-type
activation. The production/default configuration remains MSA/NDA/DPA only.

## Recommendation and remaining release gates

**OC + PO TECHNICAL ACTIVATION READY — DEFAULT OFF** is the engineering
recommendation for this draft once the exact committed PR SHA has the required
Linux CI evidence. This is not production activation.

Order Confirmation and Purchase Order remain **BUSINESS SCOPE APPROVED /
TECHNICAL IMPLEMENTATION GATE OPEN / PRODUCTION ACTIVATION NO-GO**. Remaining
release gates are the required PR CI results for the exact final SHA, including
the full authoritative Linux browser manifest and standard release-evidence,
quality/tenancy, secret, whitespace/diff, dependency, and accessibility
checks. The CI-only npm baseline approval verification could not be executed
locally because `GITHUB_REPOSITORY` and `GITHUB_TOKEN` are not available; the
plain local npm audit is green. No deployment, production data change, or
contract-type activation is authorized by this implementation evidence.
