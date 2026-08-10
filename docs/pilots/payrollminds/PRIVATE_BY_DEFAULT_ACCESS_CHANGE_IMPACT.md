# Private-by-default access-change impact: PayrollMinds

**Assessment date:** 2026-08-09
**Candidate inspected:** `47174efb14ea08c22f4819c766e5dcb821882508`
**Decision package:** [PDR-0008 Addendum 002](../../governance/decisions/pdr/PDR-0008-ADDENDUM-002-payrollminds-private-contract-access-approval-package.md)
**Runtime change in this package:** None

## 1. Exact current behavior

The shared policy is server-side and identical for Order Confirmation and
Purchase Order because both are `Contract` records. Request organization is
resolved from the active `OrganizationMembership`; `scope_queryset_for_organization`
then filters only by organization. It does not filter by `owner`, `created_by`,
workflow assignee, document linkage, or Ethical Wall.

`can_access_contract_action` first requires an active same-organization
membership. It then grants VIEW, COMMENT and AI to **every** active member.
Only EDIT looks at ownership: OWNER and ADMIN are allowed, otherwise the
contract's `owner` or `created_by` must equal the requester. This is proven by
`tests/test_permission_matrix.py`, which expects owner, admin and unrelated
ordinary member read-like access to an owner-created contract, and by
`tests/test_par_sec_002_authorization_characterization.py`, which shows a
restricted Ethical-Wall member can read and use AI on the protected record.

There is no canonical private-by-default Contract implementation already used
by the PayrollMinds MSA/NDA/DPA builders. Those paths create the same model and
call the same permission function. Their dedicated browser flows are not
object-level authorization evidence.

### Code-path trace

`request.user` → `get_user_organization` / `get_active_org_membership` →
`Contract.organization` → nullable `owner` and `created_by` →
`scope_queryset_for_organization` → surface-specific query or
`can_access_contract_action`.

| Surface | Current policy | Desired private policy | Leakage risk |
| --- | --- | --- | --- |
| Typed create/intake | Generic Contract form sets organization and `created_by`; `owner` is optional | Create records with an accountable owner/creator and route through one evaluator | A missing accountability field makes later private access ambiguous. |
| Contract detail and edit | Detail is organization-scoped; edit uses owner/admin/creator rule | Detail read uses evaluator; edit preserves approved owner/admin/creator rights | An unrelated member can load the complete record and metadata. |
| Repository/list and API list | Organization-scoped `Contract` query; totals/pagination derive from it | Filter before rows, totals, pagination, facets and serialization | Titles, counterparties, types, lifecycle, owner and counts leak. |
| Global/API search and suggestions | Organization-scoped Contract/Document candidates and search telemetry | Current evaluator before ranking, suggestions, telemetry and output | Query hits, ranking, autocomplete and result counts leak. |
| Repository counts/Command Center/analytics | Organization-wide aggregates and contract/work-item projections | Eligible-only aggregates; Addendum 001 suppression/fail-closed rules | Count, stage, risk and work-item existence leak. |
| Documents and versions | Document list/detail is organization-scoped; download delegates linked-contract VIEW | Contract evaluator applies to every linked document/version before metadata/file redirect | An unrelated member can list or inspect document metadata; linked download inherits permissive VIEW. |
| Workflow and work items | Workflow and step helpers are organization-scoped; contract-linked mutations check EDIT | Workflow/work-item list, detail and assignment inherit linked contract eligibility | Workflow title, assignee, task status and linked record existence leak. |
| Exports | Activity/report/security exports are organization-manager scoped; document download logs a view/export-like event | Export must require object eligibility and log authorized or blocked outcome | Manager-level workspace export can disclose restricted object evidence. |
| APIs | Repository/detail/version/approval/AI endpoints use tenant scoping and/or the shared policy | Every serializer applies evaluator; bearer-token audience must be separately decided | Direct numeric identifiers and API tokens can bypass a UI-only filter. |
| Cross-workspace and revoked users | Different organizations are excluded; inactive membership is denied | Preserve both; re-evaluate on each request and invalidate cached projections | Cross-tenant protection exists, but ordinary-member same-tenant access is over-broad. |

## 2. Proposed shared policy

The smallest architecture is one reusable `Contract` object-read evaluator plus
one queryset helper that composes it before every read projection. It is not a
new contract-type ACL. Order Confirmation and Purchase Order consume it only
after PDR-0008 implementation approval; PDR-0013 does not grant visibility.

Recommended initial eligibility, pending explicit approval:

- active `owner` may read, comment and edit;
- active `created_by` may read, comment and edit when distinct from owner;
- active existing organization OWNER and ADMIN may read and retain their
  existing edit authority; reads, exports and denials must be audited;
- unrelated ordinary members are denied without object-existence disclosure;
- inactive/revoked members and cross-workspace users are denied;
- no workflow assignment, participant relationship, group membership or
  future sharing behavior creates an implicit access grant in this slice.

The final bullet is deliberate. Broader collaboration needs a separately
approved explicit-sharing model; this package does not invent one.

## 3. PDR-0008 decision and privileged roles

PDR-0008 is **Proposed**. Addendum 001 is accepted only for policy scope and
does not authorize implementation. The required authority for permissions or
result visibility is independent Product, Engineering and Security GitHub
approval on the implementation SHA, green CI, reversible default-off controls,
and a release/operator record.

| Existing role | Proposed visibility decision | Mutation rights | Audit requirement |
| --- | --- | --- | --- |
| MEMBER | Owner/creator only; no unrelated-record visibility | Existing owner/creator edit only | Creation, denial and any export event retained append-only. |
| ADMIN | Proposed all-record supervisory visibility; explicit Product/Security decision point | Existing all-record EDIT remains | Read/export/denial events must be logged without restricted content. |
| OWNER | Proposed all-record governance visibility; explicit Product/Security decision point | Existing all-record EDIT remains | Read/export/denial events must be logged without restricted content. |

There is no existing separate PayrollMinds privileged role, named-user rule or
break-glass mechanism. Addendum 001 says break-glass is unavailable by default.

## 4. Data and migration impact

`Contract.owner` and `Contract.created_by` are nullable. No production data was
read. A read-only local-development query found zero Order Confirmation and zero
Purchase Order rows (and therefore zero missing-accountability rows); it cannot
quantify a production estate.

No schema migration is proposed. Before any enabled rollout, an immutable
preflight report must count, by workspace and type, records with: no owner; no
creator; neither; inactive owner; inactive creator; and cross-workspace links.
It must contain opaque IDs only. If any affected row lacks a current eligible
ordinary-member principal, do not switch the policy for that row until an
approved, auditable owner/creator backfill or archival decision exists. Never
infer an owner from an audit log or silently add an access grant.

Rollback never deletes records, versions, or audit events. It disables the new
read evaluator only under the implementation's approved fail-closed plan and
preserves the preflight/denial evidence.

## 5. Product impact

Private-by-default changes an ordinary member's expectation from “all workspace
contracts are visible” to “only accountable contracts are visible.” It improves
confidentiality but can hide a record from a colleague who previously relied on
ambient access. Reassignment must therefore maintain an accountable owner and
be audited. Administrator support remains a decision point described above.

This package adds no collaboration, delegation, group-sharing, portal, email,
or external-user capability. If a future workflow needs a reviewer who is not
owner, creator, OWNER or ADMIN, the product needs an explicit sharing/participant
policy and separate approval rather than a hidden access exception.

## 6. Engineering impact

Expected implementation boundary:

- one policy service/evaluator in the access-control boundary, not view-local
  conditions;
- composable eligible-contract and eligible-document/workflow/work-item query
  helpers;
- updates to `permissions.py`, tenancy/query services, repository service and
  APIs, contract detail/list, global/API search, document views/download,
  workflow/work-item/approval projections, exports, analytics and AI-context
  retrieval;
- route inventory and serializer audit, including direct IDs, cached responses,
  saved views, autocomplete and API bearer-token paths;
- query-budget tests proving no per-row authorization queries and a current
  policy recheck before response serialization.

The existing `scope_queryset_for_organization` remains the tenant boundary; it
is insufficient as the object boundary. The future helper must compose with it,
not replace it. No migration is expected unless the preflight identifies
missing accountable principals that receive separate authorization.

## 7. Security impact

The proposal reduces horizontal same-workspace privilege escalation, metadata,
search/count, document, workflow and export leakage. It preserves existing
tenant isolation and immediate membership-revocation checks. It redistributes
risk to correctness of the shared evaluator, cache/index invalidation, nullable
accountability fields, privileged OWNER/ADMIN behavior, and any later sharing
model. These must fail closed; a stale projection must not authorize a read.

Particular adversarial risks are direct numeric identifiers, API tokens,
autocomplete, pagination totals, facets, saved views, semantic index lag,
document-version inheritance, audit summaries, bulk/export endpoints, and
workflow tasks assigned to an ineligible user.

## 8. Mandatory future acceptance matrix

| Scenario | Required assertion |
| --- | --- |
| Creator / distinct owner | Each can access all approved linked surfaces. |
| Unrelated MEMBER | Detail, direct ID, list, repository API, search, suggestions, counts, documents, workflow/work items and export disclose nothing. |
| OWNER / ADMIN | Behavior matches the explicitly approved privileged-role decision; each access/export is audited. |
| Cross-workspace user | 404/generic denial and no audit content leak in the actor workspace. |
| Revocation | Membership/owner/creator revocation takes effect on next request and invalidates cached/projection eligibility. |
| Documents/versioning | Linked documents, versions, OCR/review metadata and signed download inherit current contract eligibility. |
| Workflow/work item | Contract-linked steps, approvals, tasks, queue and Command Center projections inherit eligibility; no ineligible assignment is rendered. |
| Search / counts | Keyword, semantic, autocomplete, facets, pagination, repository totals and analytics use eligible-only candidates; Addendum 001 suppression applies. |
| APIs / exports | Authenticated and bearer-token APIs, CSV/report/evidence exports and document download enforce eligibility and append audit outcomes. |
| Integrity / performance | Audit is append-only; policy errors fail closed; query-count/load tests prevent N+1 and stale-cache bypass. |

Tests must cover Order Confirmation and Purchase Order independently once their
typed lifecycle exists, alongside MSA/NDA/DPA preservation tests. Browser tests
are a downstream requirement, not evidence of an authorization model by
themselves.

## 9. Downstream blockers and recommendation

The current full regression is not green. The dependency scan reports five
known vulnerabilities (three `cryptography 48.0.1`, two `pypdf 6.14.2`), and
neither Order Confirmation nor Purchase Order has a browser acceptance flow.
These are recorded only; this package does not repair them.

**Recommendation:** approve the PDR-0008 implementation policy only through
the governed GitHub mechanism, resolve the OWNER/ADMIN bypass decision there,
then implement and test the one shared evaluator in a default-off,
non-production slice. PDR-0013 remains business scope only. Order Confirmation
and Purchase Order remain **BUSINESS SCOPE APPROVED / TECHNICAL ACTIVATION
BLOCKED** until the access implementation and their individual gates are green.
