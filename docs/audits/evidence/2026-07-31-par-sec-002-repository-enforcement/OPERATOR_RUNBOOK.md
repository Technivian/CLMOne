# PAR-SEC-002 repository enforcement operator runbook

**Scope:** Canonical repository rows, repository metadata/counts/filter
options, authenticated contract detail/API reads, contract edit lookup, and
repository bulk lifecycle actions only. Global search, document-only routes,
analytics, telemetry, AI, external sharing, identity, migrations, production
activation, privilege changes, repair, and legacy retirement are excluded.

## Route-to-policy inventory

| Route / surface | Source | Policy point | Protected derivations |
|---|---|---|---|
| `/contracts/repository/` | `Contract` queryset | `apply_repository_contract_policy()` before page rows or aggregation | Rows, total/active/draft/awaiting/expiring counts, counterparty filter options |
| `/contracts/api/contracts/` | `DjangoRepositoryService.list()` | Same policy before query filters, count, pagination, assignee/activity lookup, and serialization | Rows, total, pages, repository search/filter results |
| `/contracts/api/contracts/<id>/` | `DjangoRepositoryService.get_by_id()` | Same policy before object lookup | Generic not-found for denied records |
| `/contracts/<id>/` | `ContractDetailView.get_queryset()` | Same policy before object lookup or attachment handling | Contract workspace and all contract-derived tabs/context |
| `/contracts/<id>/edit/` | `ContractUpdateView.get_queryset()` | Same policy before object lookup | Generic not-found for denied records |
| `/contracts/api/contracts/bulk-update/` | `DjangoRepositoryService.bulk_update()` | Same policy before lifecycle iteration | Only eligible records can reach the canonical lifecycle service |

Bearer-token API v1 routes do not establish a human membership identity. When
this gate is active for their workspace they therefore fail closed with empty
or generic not-found results; activation must not include those routes until
an accepted actor policy exists.

## Committed state

The implementation is disabled by default. A bounded non-production activation
requires all four settings:

- `PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENABLED=true`
- `PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED=false`
- `PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENVIRONMENTS=<current non-production environment>`
- `PAR_SEC_002_REPOSITORY_ENFORCEMENT_ORG_ALLOWLIST=<workspace slug>`

An empty environment or workspace allowlist activates nothing. Production
fails closed even if accidentally listed. The repository flag is independent
from the earlier search/facet flag so one authorization cannot silently expand
the other.

## Acceptance evidence

- Default-off tenant-scoped parity and cross-workspace isolation.
- Active same-workspace membership, direct-client and inherited matter-client
  Ethical-Wall behavior.
- Eligible-only page rows, API rows, totals, pagination source, KPI counts, and
  counterparty filter options.
- Generic not-found responses for denied detail and edit lookups.
- Mixed bulk action proving only eligible records reach the lifecycle service.
- Malformed wall, inactive membership, evaluator outage, production
  configuration, and abort fail-closed paths.
- Content-free policy outcomes with no title, counterparty, identifier, query,
  or exception detail in logs.
- Existing search/facet, repository, lifecycle, design-system, accessibility,
  and cross-tenant regression suites.

## Observation and abort

Use synthetic records only in the named workspace. Confirm an eligible user
can open and update an ordinary contract while the restricted user receives
generic not-found responses and cannot see protected rows, metadata, counts,
filter options, or bulk-mutate protected contracts.

Abort immediately if protected or cross-workspace data appears; a denied
object changes any count/filter option; bulk update touches a denied record; a
policy error restores tenant-only results; or logs contain protected metadata.

## Rollback

Set `PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED=true` and restart the application.
The allowlisted workspace then receives an empty repository and generic
not-found results, and bulk actions update zero records. It never falls back
to the tenant-only legacy path while the abort is active. No migration or
business-data mutation is involved.

Leave enforcement and allowlists unchanged while abort is active. Recovery
requires revalidation and a separately recorded operator decision before
clearing the abort switch. Preserve CI and operator evidence; do not alter
Ethical Walls, contracts, documents, or audit records as part of rollback.
