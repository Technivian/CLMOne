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

### Preservation and full-regression closure (2026-08-09)

The original preservation selection had three failures. All three reproduce
unchanged on the exact `e500368c6f1191909d21822a7bdd394ff0e7fa2a` baseline,
so none is a new private-access runtime regression.

| Failure | Surface | Actor | Ownership | Expected | Actual |
| --- | --- | --- | --- | --- | --- |
| `NDAWorkflowBuilderIntegrationTests.test_command_center_row_links_back_to_generated_workspace` | Dashboard Command Center projection | workflow creator / active OWNER | `created_by` is the actor; `owner` is unset | duplicated visible text `Self-serve eligible` | projection contained the field but the shell did not duplicate it as text |
| `CommandCenterKanbanProjectionTests.test_generated_dpa_workflow_row_renders_workspace_operational_fields` | Dashboard Command Center projection | workflow creator / active OWNER | `created_by` is the actor; `owner` is unset | duplicated visible text `Draft` and risk detail | projection contained operational fields but the shell did not duplicate every field |
| `DPAWorkflowBuilderViewIntegrationTests.test_intake_does_not_expose_pre_generation_governance_or_ai_controls` | DPA intake page | active OWNER before record creation | no contract exists | no `Governance` string anywhere in response | global navigation has a `Governance` section; it is not an intake control |

All three are **G. Genuine unrelated regression**: their expectations were
stale against the shared dashboard/nav presentation, not against PDR-0008.
The two workflow tests now assert the authoritative projected fields and link;
the intake test excludes actual pre-generation controls while allowing the
unrelated global navigation label. The fixture provenance is valid.

Dashboard trace: request → `dashboard` → canonical
`apply_repository_contract_policy` for contract counts and
`get_persisted_command_center_rows` for queue rows →
`filter_contract_queryset` → template response. Filtering occurs before
aggregation and before projected rows are converted for the UI. The shared
`test_private_access_dashboard` covers one owner-visible contract, one
same-workspace inaccessible contract, and a cross-workspace contract; it
asserts only the visible row/count and preserves direct-detail denial.

Results:

- the combined preservation/security regression selection (private access,
  PAR-SEC-002 search/repository, cross-tenant isolation, permission matrix,
  documents, workflow/audit, export, AI governance, and MSA/NDA/DPA) is
  **333/333 passed**;
- migration drift: clean; no migration was added;
- full Django comparison: baseline `2724` collected, `34` failures / `37`
  errors / `9` skipped; initial PR head `2726` collected, `86` failures / `40`
  errors / `9` skipped; corrected working tree `2726` collected, `31`
  failures / `36` errors / `9` skipped. The normalized delta is **0 new / 0
  mutated**; all remaining signatures reproduce on the exact baseline. See
  [`PRIVATE_ACCESS_FULL_SUITE_REGRESSION_DIFF.md`](PRIVATE_ACCESS_FULL_SUITE_REGRESSION_DIFF.md).
- authoritative browser manifest on corrected head: `94` collected, `89`
  passed, `5` failed, `0` skipped, `0` interrupted. The five failures are
  `visual-baselines.spec.js` dashboard/list/form/workspace/detail checks whose
  Darwin reference PNGs are absent from this isolated worktree. No snapshot
  was created or updated. Functional dashboard, search, contract list/detail,
  MSA, NDA, DPA, workflow, and tenant browser paths passed;
- isolated rollback drill: from implementation commit
  `27069b798160f58eb947295f0b15e084ffbed0bc`, a no-commit `git revert`
  applied cleanly in a detached worktree; `git diff --check` and Django
  `manage.py check` passed, then the temporary revert was aborted. No
  production rollback was attempted;
- production preflight: not run; no production connection was made.

Current status: **PRIVATE-BY-DEFAULT IMPLEMENTATION GREEN — PRODUCTION
PREFLIGHT PENDING**, subject to final CI/Linux browser and release-evidence
gates for the pushed SHA. No production activation is authorized by this
evidence document.
