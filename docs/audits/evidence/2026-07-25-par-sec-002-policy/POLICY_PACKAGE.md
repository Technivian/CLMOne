# PAR-SEC-002 Product/Security policy package

**Scope:** Planning and decision documentation only.
**Runtime authorization:** Unchanged.
**Implementation authority:** None.
**Related decision:** [PDR-0008](../../../governance/decisions/pdr/PDR-0008-object-level-read-enforcement-policy.md) (policy scope accepted; implementation remains blocked)
**Addendum:** [PDR-0008 Addendum 001](../../../governance/decisions/pdr/PDR-0008-ADDENDUM-001-policy-resolution.md)

## Verified inputs

- [Baseline audit](../2026-07-24-par-sec-002/BASELINE_AUDIT.md): tenant
  isolation is present in inventoried paths, while the object-level policy is
  missing or unproven.
- [Characterization matrix](../2026-07-25-par-sec-002-characterization/ROUTE_MATRIX.md): Ethical-Wall non-enforcement, raw telemetry, and
  membership-only AI/search/analytics observations are recorded without
  changing them.
- PR #119 merged the characterization at `809b576043f1aecef2d22da2d89d7df625b6eb89`.

## Proposed enforcement boundary

PDR-0008 proposes one reusable server-side object-read policy evaluated before
search serialization, facet aggregation, analytics aggregation, telemetry
response, and AI context retrieval.  It proposes additive Ethical-Wall denial,
manager-gated analytics, eligible-only aggregates, content-free operations
telemetry, and deny-without-context for wall-restricted or indeterminate AI
requests.

The proposal is not active.  No flag has been added or enabled; no result,
permission, authority, migration, production, repair, ADMIN, canonical-read,
or legacy behaviour changed.

## Decision and implementation gates

PDR-0008 Addendum 001 records **Accept for policy scope only**.  Before any
implementation, it still needs a separately authorized scope, exact-SHA green
CI, and the required independent reviews for a permission or result-visibility
change.  Before any non-production observation or release, the implementation
needs documented abort/rollback controls and the appropriate operator or
release record.  Feature flags control exposure only; they do not provide
authority.

## Smallest proposed slice

The first potential implementation is limited to contract search results and
contract-search facets, behind a committed-default-off control in a named
non-production environment and explicit allowlist.  It must use the proposed
shared policy, filter before result/facet derivation, provide generic
content-free denial/empty outcomes, and retain a flag-off legacy fallback.
Analytics, telemetry, AI, writes, migrations, and every other surface remain
outside that slice.

## Stop conditions

Do not implement or activate if the PDR is not accepted; Ethical-Wall relation
evaluation is not deterministic; the required independent reviews or CI are
missing; a test shows a restricted metadata leak; or rollback cannot restore
the legacy read path.  Any such result blocks the slice rather than broadening
scope or inferring a policy.
