# PDR-0008 Addendum 002: PayrollMinds private-contract access approval package

**Status:** Proposed approval package — no implementation or activation authority
**Date:** 2026-08-09
**Parent:** [PDR-0008](PDR-0008-object-level-read-enforcement-policy.md)
**Related business-scope record:** [PDR-0013](PDR-0013-payrollminds-expanded-production-contract-scope.md)
**Impact assessment:** [PayrollMinds private-by-default impact](../../../pilots/payrollminds/PRIVATE_BY_DEFAULT_ACCESS_CHANGE_IMPACT.md)

## Decision requested

Approve, through independent Product, Engineering, and Security GitHub reviews
on the immutable implementation SHA, the following **implementation policy**
for the expanded PayrollMinds production scope:

1. A contract must be eligible for object read before its detail, list row,
   search hit, count, suggestion, document, workflow/work-item projection,
   export, or API representation is returned.
2. Business authorization for a contract type never grants workspace-wide
   visibility. Order Confirmation and Purchase Order must consume the same
   shared contract-object policy as all future private-by-default contracts;
   no type-specific ACL or PayrollMinds identity rule is permitted.
3. The initial eligible audience is the active contract `owner`, active
   `created_by`, and the existing active organization OWNER/ADMIN roles. The
   latter preserve their existing all-contract mutation authority; their
   privileged reads and exports require audit. A null owner/creator is not an
   ordinary-member access fallback.
4. Documents, document versions, workflows, work items, approval rows and
   contract-derived exports inherit the linked contract's current eligibility.
   A work item must not be shown or assigned to an ineligible ordinary member.
   This package creates no separate sharing, participant, or break-glass grant.
5. Active membership, the object policy and related contract eligibility are
   re-evaluated at request time. Missing ownership/creator context, a tenant
   mismatch, inactive membership, unavailable policy result, or matching
   Ethical Wall fails closed without an existence signal.

The Product and Security approvers must explicitly confirm the OWNER/ADMIN
visibility decision in item 3. It is the only privileged-role decision in this
package; no new role, permission, group, status, or sharing object is proposed.

## Existing policy and reason for change

PDR-0008 remains **Proposed**. Its Addendum 001 is accepted for policy scope
only, and neither record authorizes runtime behavior. The current source of
workspace-wide access is `can_access_contract_action`: an active membership
returns `True` for VIEW, COMMENT and AI before considering `owner` or
`created_by`. OWNER/ADMIN receive EDIT; ordinary members receive EDIT only
when they are owner or creator.

No accepted decision explains workspace-wide reads as a deliberate
private-contract policy. The evidence supports only that it is the current
legacy workspace-collaboration behavior. The same shared function is used by
the MSA, NDA and DPA controlled paths; they are not a previously proven
private-by-default model that Order Confirmation or Purchase Order could reuse.

## Scope, compatibility and rollback

Affected modules include `contracts.permissions`, tenancy/query helpers,
repository and contract APIs, contract detail/list views, global and API
search, document views/download, workflow and work-item projections, exports,
analytics, AI context, and all contract-derived serializers. The implementation
must inventory each route before an enabled rollout; it must not rely on UI
hiding.

The change narrows ordinary-member visibility. Existing users may no longer
see records they previously saw unless they are owner/creator or an existing
privileged role. There is no data-schema migration proposed. A preflight must
inventory records without an accountable owner or creator and block ordinary
member exposure until a governed assignment/backfill decision is complete.

Rollback disables only the newly authorized evaluator in the approved named
non-production observation. It preserves records, versions, audits and any
data-quality report. For production, rollback behavior must be approved with
the implementation: it must never silently restore unfiltered search, counts,
or exports for a restricted object.

## Approval and evidence mechanism

This addendum must not use a manual vote table or manually entered approval
timestamp. The implementation PR must request independent submitted GitHub
reviews for Product, Engineering, and Security, retain green CI for the exact
unchanged SHA, and link the required release/operator record. The repository's
current `CODEOWNERS` maps `contracts/`, `tests/`, `config/`, and `docs/` to
`@haroonwahed`; that routing does not by itself prove the three independent
authorities required for a permission or production change.

PDR-0013 therefore remains downstream of this package: business scope →
PDR-0008 approval → access implementation → individual Order Confirmation or
Purchase Order activation evidence. Neither type is authorized to be exposed
by acceptance of this package alone.
