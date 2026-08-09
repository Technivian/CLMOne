# PDR-0008 Addendum 002: private-by-default contract access approval package

**Status:** Proposed approval package — no runtime implementation or activation authority
**Date:** 2026-08-09
**Parent:** [PDR-0008](PDR-0008-object-level-read-enforcement-policy.md)
**Related scope:** [PDR-0013](PDR-0013-payrollminds-expanded-production-contract-scope.md)

## Approval requested

Authorize a future implementation of one canonical, server-side contract
object-access policy. This PR does **not** implement private-by-default access.
It requests authority to replace the current policy:

> same-workspace VIEW / COMMENT / AI + owner/creator-limited EDIT

with the proposed private-by-default policy:

- active `owner` and active `created_by` may read/comment/edit;
- existing active organization OWNER and ADMIN retain their existing all-record
  edit authority and, if Product and Security explicitly approve, supervisory
  read/export access with append-only audit;
- unrelated ordinary members are denied without object-existence disclosure;
- documents, document versions, workflows, work items, lists, search, counts,
  autocomplete, exports, APIs and otherwise-enabled AI inherit the current
  contract policy;
- missing ownership/creator data, tenant mismatch, inactive membership,
  Ethical-Wall match or unavailable policy evaluation fails closed.

This is a shared policy, not a PayrollMinds-specific ACL or username/ID rule.
No type becomes technically active if this package is merged.

## Current baseline retained

`can_access_contract_action` requires active same-workspace membership, then
returns true for VIEW, COMMENT and AI before considering `owner` or
`created_by`; ownership constrains EDIT only. `tests/test_permission_matrix.py`
expects an unrelated active member to have the read-like actions. The
PAR-SEC-002 characterization separately proves that an Ethical-Wall restricted
member may still read and use AI. MSA/NDA/DPA use this same shared policy; they
are not a canonical private model.

## Existing-data transition decision

`Contract.owner` and `Contract.created_by` are nullable. This approval does
not authorize a migration or backfill. The implementation PR must first create
an immutable, read-only preflight inventory by workspace/type of missing or
inactive owner/creator fields, then obtain approval for any assignment,
backfill, archival or access-review transition. It must not infer ownership
from audit logs or silently make existing ordinary-member records inaccessible.

## Required governance evidence

No manual vote table or hand-entered approval timestamp is allowed. GitHub
must show submitted **Approve** reviews from independent Product, Engineering
and Security authorities, green CI for the unchanged reviewed SHA, and the
required release/operator record. `CODEOWNERS` routing alone does not prove
three independent authorities. If they are unavailable, this package remains
unmerged and implementation is not authorized.

## Scope boundary and rollback

This approval does not activate Order Confirmation, Purchase Order, any other
type, AI, email, signatures, portal, integration, sharing, or production data.
Future rollout is default-off and reversible; it retains business records,
document versions and audit evidence. It may never roll back restricted search,
counts or exports to an unfiltered result path.
