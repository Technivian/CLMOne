# PAR-SEC-002 contract-search enforcement operator runbook

**Scope:** Contract-search result serialization and contract-search facets only.
Analytics, telemetry, AI, writes, migrations, production activation, privilege
changes, repair, canonical-read cutover, and legacy retirement are excluded.

## Route-to-policy inventory

| Route | Source | Policy point | Returned derivations |
|---|---|---|---|
| `/contracts/api/search/contracts/` | `Contract` queryset | `filter_contract_queryset()` before query filters, totals, pagination, or serialization | Eligible rows and eligible-only total |
| `/contracts/api/search/facets/` | `Contract` queryset | Same evaluator before aggregation | Eligible-only status, lifecycle-stage, type, and jurisdiction buckets |

No repository list, autocomplete, saved view, export, analytics, telemetry, AI,
clause search, or document-text route is changed by this slice.

## Committed state

The implementation is disabled by default. Activation requires all three
settings:

- `PAR_SEC_002_SEARCH_ENFORCEMENT_ENABLED=true`
- `PAR_SEC_002_SEARCH_ABORT_FAIL_CLOSED=false`
- `PAR_SEC_002_SEARCH_ENFORCEMENT_ENVIRONMENTS=<current non-production environment>`
- `PAR_SEC_002_SEARCH_ENFORCEMENT_ORG_ALLOWLIST=<workspace slug>`

An empty environment or workspace allowlist activates nothing. Production is
rejected even if accidentally listed.

## Acceptance evidence

- Default-off legacy parity.
- Active and inactive membership behavior.
- Direct client, direct matter, and inherited matter-client wall matches.
- Expired and multiple-wall behavior.
- Malformed wall, evaluator outage, production, and tenant-mismatched relation
  fail-closed paths.
- Eligible-only metadata, totals, pagination source, and facet counts.
- Content-free policy-error logs and bounded search query cost.
- Existing search, characterization, and full cross-tenant regression suites.

## Observation and abort

Use only synthetic records in the named workspace. Confirm that an eligible
member sees ordinary contracts while client, matter, and inherited
matter-client wall matches affect neither results, metadata, totals, nor
facets. Abort immediately for any restricted metadata, cross-tenant result,
count mismatch, or unexpected policy error.

## Rollback

Set `PAR_SEC_002_SEARCH_ABORT_FAIL_CLOSED=true` and restart the application.
The named workspace then receives generic empty search results and facets; it
does not fall back to the unfiltered legacy path. Leave enforcement and the
allowlists unchanged while the abort is active. Recovery requires revalidation
and a separately recorded operator decision before clearing the abort switch.
No migration or business-data mutation is involved. Preserve CI and operator
evidence; do not alter Ethical Wall or contract records as part of rollback.
