# PDR-0008 private-by-default implementation evidence

## Authority and scope

Implementation begins from `origin/main` commit
`e500368c6f1191909d21822a7bdd394ff0e7fa2a`. PDR-0008 Addendum 002 is
approved for implementation under active EXC-0003, owned by Haroon Wahed,
with review/expiry on 2026-09-30 or earlier exit when independent governance
capacity is available. EXC-0003 changes approval mechanics only; no security
invariant is waived.

Implementation code commit: `27069b798160f58eb947295f0b15e084ffbed0bc`.

This change implements access policy only. It does not activate Order
Confirmation, Purchase Order, OTHER/Custom, imports, AI scope, email,
signature, portal, integration, sharing, tenant, or deployment behaviour.

## Implemented policy

For an active member in the matching workspace, Contract read, comment, and
AI access require `owner == user` or `created_by == user`. Missing ownership,
inactive provenance, tenant mismatch, an active Ethical Wall, or unavailable
policy evaluation fail closed. OWNER and ADMIN retain only the already
approved all-record edit path, subject to the same active-membership and
Ethical-Wall checks. They do not gain supervisory read, comment, AI, search,
count, autocomplete, or export access: that would require separate Product
and Security approval.

## Lifecycle trace and enforcement points

| Surface | Enforcement |
| --- | --- |
| Contract intake/create and provenance | Existing create/workflow paths record `created_by`; the new preflight identifies legacy gaps without mutation. |
| Contract detail, repository, API list, search, counts | `filter_contract_queryset` is mandatory through repository/search policy and dashboard projections. |
| Documents and DocumentVersion | Document visibility inherits the linked readable Contract; unlinked documents require their uploader. Version query support inherits its document. |
| Workflow and canonical workflow instance | Workflow lists, details, forms, dashboard, and step actions start from contract-filtered workflows. |
| Work items and command-center projections | LegalTask and persisted CommandCenterWorkItem rows inherit linked Contract visibility. |
| Comments, AI, export | `can_access_contract_action` derives COMMENT and AI from the canonical read query; contract export callers retain that boundary. |
| Audit | Existing create/action audit logging remains; this change does not add a parallel audit model. |

## Existing-data preflight and rollback

`private_access_data_preflight` is a read-only management command. It reports
only opaque record IDs, workspace/type totals, missing owner/creator totals,
inactive references, and exclusive remediation categories. It performs no
write, inferred ownership, migration, or production connection. The required
operator procedure is in `PRIVATE_ACCESS_PRODUCTION_PREFLIGHT_RUNBOOK.md`.

Rollback is a code revert of this implementation commit; no data migration or
activation flag must be reversed. Production preflight remains pending until
an authorized operator supplies a read-only production connection and stores
the restricted output outside the repository.

## Gate state

Current status: **NO-GO — regression and production preflight pending**.
The production preflight has not been run and no production activation is
authorized by this evidence document.
