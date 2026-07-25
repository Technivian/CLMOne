# PAR-SEC-002 search and facets enforcement authorization package

**Status:** Requested — planning and authorization evidence only.
**Implementation:** Not included and not authorized.
**Policy:** PDR-0008 and Addendum 001, accepted for policy scope only.
**Proposed implementation SHA:** TBD until a separate implementation PR is
created and its final scope is reviewed.

## Exact first-slice scope

The proposed implementation is limited to:

- one named non-production environment;
- one explicit allowlisted workspace;
- committed-default-off, reversible controls;
- contract-search result serialization and contract-search facet calculation;
- current tenant and object-policy evaluation before either result rows or
  facet/totals are produced;
- active Ethical-Wall evaluation under the accepted client/matter relation
  rule;
- generic, content-free deny/empty responses;
- stale or unverifiable index state failing closed or using a policy-safe
  authoritative fallback;
- an operator record containing the deployed SHA, flags, allowlist, counters,
  abort observations, and rollback result.

The slice excludes analytics enforcement, AI filtering/redaction, break-glass,
telemetry remediation, permission changes, migrations, writes, production
activation, repair, ADMIN authority, canonical reads, and legacy retirement.

No implementation files, settings, flags, migrations, or runtime behavior are
changed by this package.

## Required independent approvals

Before implementation or activation, the following approvals are required on
the exact final implementation SHA.  No approval is recorded by this package;
missing approvals remain blockers.

| Gate | Required evidence | Status |
|---|---|---|
| Product | Submitted GitHub approval confirming the exact scope, object-policy behavior, generic denial semantics, and no out-of-scope surface | Missing — must be obtained on the final implementation SHA |
| Engineering | Submitted GitHub approval confirming policy-before-serialization/facets, safe index fallback, tests, and reversible design | Missing — must be obtained on the final implementation SHA |
| Security | Submitted GitHub approval confirming Ethical-Wall enforcement, fail-closed behavior, non-leakage, abort criteria, and rollback | Missing — must be obtained on the final implementation SHA |
| CI | All required repository checks green for the unchanged reviewed SHA | Required before merge |
| Operator | Named-environment record with flags off/before, allowlist, during/after values, observations, and rollback | Required before activation |

The sole-maintainer bootstrap can authorize planning-only documentation, but it
does not replace these independent approvals for a permission or result-
visibility change. No feature flag grants authority.

## Required tests and evidence

The implementation PR must provide exact-SHA evidence for:

- authenticated eligible contract search and facets;
- inactive membership and cross-tenant denial;
- active client wall and matter wall denial;
- inherited matter-client wall behavior;
- expired and multiple-wall cases;
- malformed wall configuration and unavailable policy evaluation;
- no restricted title, identifier, URL, count, facet, ranking signal, or empty
  state leakage;
- stale/unverifiable index fail-closed behavior and policy-safe fallback;
- flag-off parity with the legacy path;
- tenant isolation and permission regression suites;
- Django checks, required CI, and rollback drill;
- operator evidence for the named non-production environment.

## Abort conditions

Abort immediately and leave the slice disabled if any of the following occurs:

- a cross-tenant or wall-protected result, facet, count, URL, or existence
  signal reaches the requester;
- index freshness or policy evaluation is unavailable and the system cannot
  prove a policy-safe fallback;
- a denied response contains protected metadata;
- flag-off does not restore the exact pre-slice behavior;
- an allow/deny mismatch, tenant-isolation regression, or permission bypass is
  observed;
- audit/operator evidence contains content or cannot be written;
- any out-of-scope analytics, AI, telemetry, permission, migration, production,
  repair, ADMIN, canonical-read, or legacy-retirement change appears.

## Rollback

Rollback is flag-off plus allowlist emptying, followed by restoration of the
policy-safe legacy read path.  If the legacy path cannot be shown safe for the
affected scope, return a generic unavailable response instead of an
unfiltered result.  Preserve content-free audit and operator evidence; do not
repair or mutate business data.

## Authorization disposition

**Not authorized.** The package defines the exact requested scope and evidence
gate only. Implementation and activation require the three independent GitHub
approvals, green CI on the exact final SHA, and the named-environment operator
record described above.
