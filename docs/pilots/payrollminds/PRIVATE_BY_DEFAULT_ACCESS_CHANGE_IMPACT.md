# Private-by-default access impact: PayrollMinds

**Candidate:** `47174efb14ea08c22f4819c766e5dcb821882508`
**Runtime change:** None

## Current server-side trace

`request.user` → active `OrganizationMembership` → `Contract.organization` →
nullable `owner`/`created_by` → organization-only queryset or
`can_access_contract_action`.

| Surface | Current policy | Desired policy | Leakage risk |
| --- | --- | --- | --- |
| Detail/list/repository/API | Tenant-scoped Contract queryset | Policy-filtered queryset before serialization | Same-workspace title, metadata and direct-ID disclosure |
| Search/counts/suggestions | Tenant-scoped candidates and aggregates | Eligible candidates before ranking, facets and totals | Result/count/facet/autocomplete disclosure |
| Documents/versions | Tenant-scoped document query; download calls permissive contract VIEW | Inherit contract eligibility | Metadata and file-access disclosure |
| Workflow/work items | Tenant-scoped workflow/step/queue projections | Inherit linked-contract eligibility | Task/assignee/status disclosure |
| Exports | Workspace manager or document-download rules | Object eligibility plus audit | Restricted evidence disclosure |
| AI | Shared AI action check permits every active member | Same current object policy before retrieval | Contract-context disclosure |

`tests/test_permission_matrix.py` proves that every active owner, admin and
ordinary member can VIEW, COMMENT and use AI for another member's contract;
only EDIT is owner/admin/creator-limited. The PAR-SEC-002 characterization
proves an Ethical-Wall restricted member can still read. MSA/NDA/DPA have no
separate private model.

## Proposed policy, roles and data

One reusable contract evaluator and queryset helper must compose with tenant
scoping. Do not create a type-specific ACL. Proposed owner/creator access is
explicit; unrelated MEMBER access is denied. OWNER/ADMIN supervisory read and
export remains an explicit Product/Security approval decision, while their
existing all-record edit authority is preserved. Every privileged allow, export
and denial is append-only audited.

No production data was read. A local development query found zero Order
Confirmation and Purchase Order records; it cannot quantify production. Since
owner/creator are nullable, no policy rollout may occur before an immutable
preflight inventories missing/inactive accountability and an approved,
auditable transition strategy exists. No schema or data migration is authorized
here.

## Required future tests and impact

Test creator, distinct owner, unrelated member, OWNER/ADMIN, cross-workspace,
direct IDs, revoked membership, list/search/count/facet/autocomplete,
documents/versions/download, workflow/work-item/approval inheritance, APIs,
exports, AI context, append-only audit and stale-cache/query-budget behavior.

Private-by-default improves horizontal-privilege, metadata, document, workflow
and export protection but changes ordinary-member collaboration expectations.
Reassignment must preserve an accountable principal and be audited. Sharing,
workflow-participant grants and break-glass require separate approved policy.

Downstream blockers remain: shared-policy implementation, existing-data
accountability/backfill preflight and decision, five dependency vulnerabilities,
missing browser coverage for both types, and non-green full regression and
security evidence. EXC-0003 changes approval mechanics only; it waives no
runtime or security control.
