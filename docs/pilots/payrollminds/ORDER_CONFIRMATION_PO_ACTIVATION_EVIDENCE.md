# Order Confirmation and Purchase Order activation readiness

**Starting main SHA:** `a329b805952befefa7924ddc943badca9ed8ed4b`
**Assessment date:** 2026-08-10
**Status:** **NO-GO**

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

`npm audit --omit=dev --json` for `client/` reported zero vulnerabilities.
The local Python toolchain cannot run `pip-audit` or Bandit because the checked
out `.venv` console scripts reference a removed interpreter. The raw
TruffleHog invocation completed but is not release evidence: it scanned Git
object history and local development certificate fixtures, yielding historical
and fixture findings outside the authoritative CI scope. The previously
reported five dependency findings therefore cannot yet be reconciled as
resolved, present, or replaced.

No OC/PO lifecycle test, browser test, complete browser manifest, full Django
regression comparison, accessibility run, or migration-drift run has been
completed for this readiness branch. No migration has been added by this
assessment.

## Remaining gaps and recommendation

1. Add a default-off, server-side controlled-pilot OC/PO intake gate that
   permits only the two candidate types and continues to deny SOW, Vendor,
   Employment, SaaS, Lease, OTHER/Custom, generic upload/import, and every
   other inactive type.
2. Add and run separate deterministic OC and PO lifecycle/access/export/audit
   coverage, including private-access and non-disclosure cases.
3. Add and run authoritative browser coverage for both types.
4. Repair or recreate the local Python test environment and rerun pip-audit,
   Bandit, the scoped TruffleHog gate, full regression, UAT, browser,
   accessibility, and migration-drift checks. Reconcile all five previous
   dependency findings without suppressing results.

**Recommendation: NO-GO.** Order Confirmation and Purchase Order remain
**BUSINESS SCOPE APPROVED / TECHNICAL IMPLEMENTATION GATE OPEN / PRODUCTION
ACTIVATION NO-GO**. Nothing in this readiness assessment deployed, changed a
production flag or environment, created production data, or activated a
contract type.
