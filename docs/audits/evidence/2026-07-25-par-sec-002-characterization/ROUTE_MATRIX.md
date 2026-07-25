# PAR-SEC-002 characterization — route, role, and metadata matrix

**Baseline:** `main` at `10177cc5d2233156d7844cd65ea034aacbef3f09`  
**Scope:** Tests, route evidence, and default-off observation only.  
**Runtime authority:** Unchanged. This record does not select or implement an
object-level policy.

## Current route evidence

| Surface | Current server gate | Owner / active member evidence | Cross-tenant evidence | Ethical-Wall / restricted-metadata result |
|---|---|---|---|---|
| `/contracts/search/` | Login plus tenant-scoped query helper | Active member can invoke; no distinct object policy | Existing cross-tenant global-search tests exclude the other workspace | No `EthicalWall` evaluation in the path; result metadata is only tenant-scoped |
| `/contracts/api/search/contracts/` | Login plus active-organization filter | Characterization test shows owner and active member receive their workspace rows | Other-workspace contract is excluded | No object/ethical-wall filter before result rows are serialized |
| `/contracts/api/search/clauses/`, `/facets/` | Login plus active-organization filter | Existing endpoint/service coverage | Tenant filtering is service-level | Clause rows and facet counts have no common restricted-record policy |
| `/contracts/api/search/telemetry/` | Login plus active-organization filter | Characterization test shows active member receives workspace telemetry | Organization filter excludes other workspace events | Raw query strings are returned to every active workspace member; minimization/audience policy is missing |
| `/contracts/api/analytics/executive/` | Login plus active organization | Characterization test shows active member can read; preset mutation is separately manager-gated | Existing analytics test proves owner workspace scope | Aggregate reads have no verified role/object restriction |
| `/contracts/api/clause-analytics/*` | Login plus active-organization service query | Existing service coverage | Tenant filters in service queries | No verified object-level aggregate suppression |
| Contract AI APIs | Login, tenant-scoped contract lookup, contract action, org AI policy/provider checks | `AI` action currently accepts an active member | Existing extraction test returns 404 for another workspace | No Ethical-Wall/context-redaction evaluation in the inventoried resolver |
| `/<contract>/ai-assistant/` | Login, tenant-scoped contract lookup, `COMMENT` action, prompt policy | Current `COMMENT` action accepts an active member | Characterization test returns 404 for another workspace | No Ethical-Wall evaluation; this PR does not change that behavior |

## Ethical-Wall observation

`EthicalWall` has workspace, client/matter, restricted-user, active-state, and
expiry data. The characterization test creates an active wall that restricts a
member and confirms the current `VIEW` and `AI` contract actions still allow
that member. This is evidence of a missing enforcement policy, not an accepted
decision about the future meaning of a wall.

## Restricted metadata and telemetry inventory

- Contract search serializes identifiers, title, status, lifecycle, type,
  counterparty, and timestamps after tenant filtering.
- Facets expose status, lifecycle, type, and jurisdiction counts after tenant
  filtering.
- Executive and clause analytics expose organization-scoped aggregates.
- Search telemetry exposes up to 50 raw query strings, result counts, type,
  and time to any active workspace member.
- AI routes receive a tenant-scoped contract but do not demonstrate a
  restricted-record, Ethical-Wall, or field-redaction decision.

No production data was inspected or exported for this inventory.

## Default-off content-free counters

`PAR_SEC_002_OBSERVATION_ENABLED` is committed **false**. When explicitly
enabled in a controlled future observation, `contracts.services.par_sec_002_observation`
only increments process-local counters keyed by route surface and actor class
(`manager`, `member`, or `no_workspace`) and logs those two values. It does not
store or log user IDs, organization IDs, contract IDs, titles, queries, result
counts, prompts, decisions, or response content. It has no HTTP endpoint.

Instrumented characterization surfaces are global and API search, executive
and clause analytics, and the internal contract AI assistant. The counter is
not authorization, does not filter or modify output, and is off by default.

## Stop conditions and next gate

Do not enable observation or implement enforcement until a separately
authorized Product/Security decision defines: Ethical-Wall applicability to
contract/client/matter relations; role and object eligibility; aggregate/facet
suppression; telemetry audience and minimization; and AI-context redaction.
Any proposed code that changes a visible result, permission, or authority is
outside this characterization scope.
