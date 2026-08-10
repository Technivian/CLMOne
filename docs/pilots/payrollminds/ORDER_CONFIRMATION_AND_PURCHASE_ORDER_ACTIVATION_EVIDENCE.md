# Order Confirmation and Purchase Order activation evidence

**Assessment date:** 2026-08-09
**Candidate:** local `47174efb14ea08c22f4819c766e5dcb821882508`
**Business-scope record:** [PDR-0013](../../governance/decisions/pdr/PDR-0013-payrollminds-expanded-production-contract-scope.md)
**Disposition:** **NO-GO** for Order Confirmation and Purchase Order

## Authority boundary

PDR-0013 records the Product Owner's business-scope direction for this first
Batch 2 cohort. It does not supply the independent GitHub Product,
Engineering, and Security approvals, unchanged-SHA CI, or named-environment
release/operator evidence required for a production activation.

The mandatory private-by-default requirement cannot be repaired in this
assessment. `PDR-0008` remains Proposed and explicitly prohibits changing a
permission, read result, filtering, or runtime authorization without that
separate authorization. A type-specific bypass would create an unapproved new
access policy and would not meet the reusable access-control boundary required
by the canonical Security and Data/AI documentation.

The required approval package is now prepared in
[PDR-0008 Addendum 002](../../governance/decisions/pdr/PDR-0008-ADDENDUM-002-payrollminds-private-contract-access-approval-package.md),
with the server-side trace and future acceptance matrix in the
[private-by-default impact assessment](PRIVATE_BY_DEFAULT_ACCESS_CHANGE_IMPACT.md).

## End-to-end trace and gap register

| Control | Order Confirmation | Purchase Order | Current evidence / gap |
| --- | --- | --- | --- |
| Typed intake/create | Procurement card resolves to generic `/contracts/new/?type=ORDER_CONFIRMATION` | Procurement card resolves to generic `/contracts/new/?type=PURCHASE_ORDER` | No dedicated typed endpoint; generic create accepts the full active catalogue. |
| Pilot restriction | Not in middleware builder allowlist | Not in middleware builder allowlist | `ControlledPilotScopeMiddleware` redirects both generic paths when controlled-pilot mode is enabled. |
| Contract and catalogue | `Contract.contract_type` and catalogue exist | Same | Generic form can create the contract but does not establish a type-specific activation path. |
| Document/version and provenance | Generic form records contract provenance | Same | It creates neither `Document` nor immutable `DocumentVersion`; legacy upload/import paths must remain excluded. |
| Private authorization | Workspace membership grants view/comment/AI | Same | `can_access_contract_action` allows every active workspace member to read the record. This fails private-by-default. |
| Search/repository | Tenant-scoped results include readable workspace records | Same | Repository totals and global search do not apply object-level eligibility; restricted existence can disclose. |
| Workflow | Commercial launch-copy metadata only | Same | No type-specific published immutable workflow launch is created by generic create. |
| Audit | Contract creation/provenance audit exists | Same | No complete per-type create → document → workflow → export evidence chain. |
| Controlled export | Workspace activity export is owner/admin controlled and logged | Same | It is not a type-specific contract/document export gate. Document download is not reached by generic create because no document exists. |
| Browser journey | No type-specific browser specification | Same | Existing browser suite covers MSA/NDA/DPA/pilot flows, not either target type. |
| Invalid transitions / cleanup | Generic workflow-step model has transition rules | Same | No type-specific workflow instance or isolated acceptance/cleanup coverage. |

## Restrictions retained

- `OTHER`/Custom remains excluded.
- Generic `/contracts/new/`, legacy Upload & Review, bulk upload/import,
  quarantine release, CSV/inbound/integration import, email, AI, signatures,
  portal/sharing, tenant, and access scope remain unchanged.
- MSA, NDA, and DPA code paths were not changed.

## Required next authorization and remediation

1. Obtain the independent GitHub approvals required by PDR-0008 for a reusable
   object-level read policy, including repository/search/count/document/export
   enforcement and non-disclosure tests.
2. Obtain the individual technical activation authorization for each target on
   the immutable reviewed SHA.
3. Only then add two dedicated default-off typed intake paths, each with a
   published immutable workflow version, canonical document/version creation,
   typed export, and the complete isolated acceptance/security/browser pack.
4. Attach green full regression, browser, security, deployment and operator
   evidence to each type before exposing it in a named production environment.

## Per-type gate

| Type | Business direction | Technical gate | Production classification |
| --- | --- | --- | --- |
| Order Confirmation | First proposed Batch 2 cohort | Red: authorization, typed lifecycle, workflow, document/version, export, tests, browser, and release evidence incomplete | **NO-GO** |
| Purchase Order | First proposed Batch 2 cohort | Red: authorization, typed lifecycle, workflow, document/version, export, tests, browser, and release evidence incomplete | **NO-GO** |

No feature flag, route, configuration, deployment, merge, or production
activation was performed. This report stops the activation work at the
governance and security gate.

## Validation run on the candidate

| Gate | Result | Consequence |
| --- | --- | --- |
| `git diff --check` | Pass | Documentation changes have no whitespace error. |
| `make check` | Pass | Django system checks report no issues. |
| `make test` | Not green | The 2,563-test preservation suite reports existing failures/errors, including the documented in-progress contract status/lifecycle refactor drift; it is not a release-quality result. |
| `npm --prefix client run test:e2e` | Run | The 90-test browser suite was executed, but contains no Order Confirmation or Purchase Order acceptance specification. It cannot evidence either type. |
| Bandit high-severity scan | Pass | No high-severity finding was emitted by `.venv/bin/python -m bandit -q -r contracts config -lll`. |
| `pip_audit` runtime dependency scan | Fail | Five known vulnerabilities: three in `cryptography 48.0.1` and two in `pypdf 6.14.2`; a clean security gate is absent. |
