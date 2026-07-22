# PAR-ID-001 — Role usage matrix

**Date:** 2026-07-22  
**Scope:** Discovery complete — all role-like concepts inventoried  
**Branch:** `cursor/feat-par-apr-001-foundation-governance`  
**ADR:** ADR-0014 **Proposed** (not Accepted)

## Legend

| Column | Meaning |
|---|---|
| **Scope** | `org` = organization-bound · `user` = user-global · `object` = per-record · `global` = platform |
| **Phase** | `config` = template/rule design time · `runtime` = execution/assignment · `both` |
| **Authority** | What server-side power is actually granted |
| **Canonical target** | PAR-ID-001 target concept (see `TARGET_ROLE_MODEL.md`) |
| **Risk** | Reconciliation impact: H / M / L |

---

## A. Workspace membership roles

### A1. `OrganizationMembership.Role`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py` (`OrganizationMembership.Role`) |
| **Current name** | `OWNER`, `ADMIN`, `MEMBER` |
| **Actual meaning** | Organization workspace permission — admin, configuration, elevated contract edit |
| **Scope** | `org` (per `(organization, user)`) |
| **Phase** | `runtime` (stored on membership row) |
| **Authority granted** | `OWNER`/`ADMIN`: `can_manage_organization`, configuration nav, trust accounting, approval reassign, document delete any; `MEMBER`: base member access |
| **Permissions used** | `can_manage_organization`, `can_access_contract_action` EDIT branch, `can_assign_organization_role`, `TrustAccountingPermissionMixin` |
| **Assignment** | Invite accept, admin role update, SCIM provisioning, SAML JIT |
| **Consumers** | `permissions.py`, `nav_config.py`, `approval_workflow.py`, `organization_admin.py`, API admin gates, `document_deletion.py` |
| **Overlap / conflict** | Name collision with `UserProfile.Role.ADMIN` — different semantics |
| **Canonical target** | **Workspace Role** |
| **Migration risk** | **M** — rename labels only; keep storage until mapping accepted |

### A2. `OrganizationInvitation.role`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:136` |
| **Current name** | Same enum as membership |
| **Actual meaning** | Role granted when invitation accepted |
| **Scope** | `org` |
| **Phase** | `config` → `runtime` on accept |
| **Authority** | Defers to membership role on accept |
| **Permissions** | Membership role checks after accept |
| **Assignment** | Admin invite flow |
| **Consumers** | `organization_admin.py` |
| **Overlap** | None beyond A1 |
| **Canonical target** | **Workspace Role** (pending assignment) |
| **Migration risk** | **L** |

### A3. `OrganizationSCIMGroup.role`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:327` |
| **Current name** | `OWNER`, `ADMIN`, `MEMBER` |
| **Actual meaning** | SCIM group → workspace role mapping |
| **Scope** | `org` |
| **Phase** | `config` (IdP) → `runtime` (reconcile on group sync) |
| **Authority** | Highest role from active SCIM groups wins (`scim.py:_reconcile_scim_group_membership_role`) |
| **Permissions** | Membership role only — **does not set `UserProfile.role`** |
| **Assignment** | SCIM Group PATCH/PUT |
| **Consumers** | `contracts/api/scim.py` |
| **Overlap** | SCIM workspace role only; process roles unprovisioned |
| **Canonical target** | **Workspace Role** (external provisioning) |
| **Migration risk** | **H** — IdP contracts; must not widen privileges on mapping |

### A4. SAML JIT membership role

| Field | Value |
|---|---|
| **Implementation** | `contracts/saml.py:305-321` |
| **Current name** | Assertion-mapped membership role |
| **Actual meaning** | Workspace role on first login |
| **Scope** | `org` |
| **Phase** | `runtime` |
| **Authority** | Membership role only |
| **Permissions** | Same as A1 |
| **Assignment** | SAML assertion |
| **Consumers** | SAML ACS handler |
| **Overlap** | Profile created; profile role not set from SAML |
| **Canonical target** | **Workspace Role** |
| **Migration risk** | **M** |

---

## B. Process / professional roles (interim Role Definition storage)

### B1. `UserProfile.Role`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:169-176` |
| **Current name** | `PARTNER`, `SENIOR_ASSOCIATE`, `ASSOCIATE`, `PARALEGAL`, `LEGAL_ASSISTANT`, `ADMIN`, `CLIENT` |
| **Actual meaning** | Process/professional role for workflow assignee and approval rule matching |
| **Scope** | **`user` (global — not org-scoped)** |
| **Phase** | `runtime` |
| **Authority granted** | **None directly** — used for resolver matching only; does not gate `can_manage_organization` |
| **Permissions used** | Equality match in `resolve_assignee`, `resolve_rule_assignee` |
| **Assignment** | Seeds, manual profile update, `get_or_create` default `ASSOCIATE` |
| **Consumers** | `WorkflowTemplateStep.assignee_role`, `ApprovalRule.approver_role`, workflow routing |
| **Overlap / conflict** | **`ADMIN` name collision** with org ADMIN; user-global scope vs org membership |
| **Canonical target** | **Workflow Role Definition** (transitional storage) |
| **Migration risk** | **H** — org-scoping required for multi-org users |

### B2. `UserProfile.can_approve` / `is_attorney` properties

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:309-314` |
| **Actual meaning** | Convenience flags on profile role |
| **Scope** | `user` |
| **Phase** | `runtime` (computed) |
| **Authority** | **None enforced** — no runtime callers found |
| **Permissions** | Unused |
| **Assignment** | N/A |
| **Consumers** | Definition only |
| **Overlap** | Dead code risk if wired without authz review |
| **Canonical target** | Remove or replace with explicit Permission Set checks |
| **Migration risk** | **L** |

---

## C. Django groups and permissions

### C1. Django `Group` / `Permission` / `has_perm`

| Field | Value |
|---|---|
| **Implementation** | Not used in product code |
| **Actual meaning** | N/A |
| **Scope** | N/A |
| **Phase** | N/A |
| **Authority** | None — custom authz via `permissions.py` |
| **Permissions** | None |
| **Assignment** | N/A |
| **Consumers** | None in `contracts/` |
| **Overlap** | Future Permission Set may map here or stay custom |
| **Canonical target** | **Permission Set** (future — not Django Group today) |
| **Migration risk** | **L** (greenfield if adopted) |

### C2. `OrganizationAPIToken.scopes`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:366-411`, `api/_helpers.py` |
| **Current name** | `contracts:read`, `contracts:*`, `api:*`, etc. |
| **Actual meaning** | Token capability — not human role |
| **Scope** | `org` + token |
| **Phase** | `config` |
| **Authority** | API read/write per scope |
| **Permissions** | Scope string match |
| **Assignment** | Admin token creation |
| **Consumers** | REST API helpers |
| **Overlap** | Separate from human roles — must remain explicit |
| **Canonical target** | **Permission Set** (machine principal) |
| **Migration risk** | **M** |

---

## D. Contract accountability fields

### D1. `Contract.owner`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:990-997` |
| **Current name** | `owner` (FK User) |
| **Actual meaning** | Accountable contract owner — process role "contract owner" |
| **Scope** | `object` (per contract, org-bound via contract) |
| **Phase** | `runtime` |
| **Authority** | EDIT if `owner_id == user.id`; approval segregation of duties |
| **Permissions** | `can_access_contract_action` EDIT; `authorize_approval_actor` blocks owner self-decision |
| **Assignment** | Create/update contract, workflow, provenance |
| **Consumers** | Repository, lifecycle, approvals, MSA workflow |
| **Overlap** | Distinct from workspace ADMIN |
| **Canonical target** | **Runtime Role Assignment** (contract owner) |
| **Migration risk** | **M** |

### D2. `Contract.created_by`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:998` |
| **Actual meaning** | Provenance + requester; EDIT fallback; approval requester |
| **Scope** | `object` |
| **Phase** | `runtime` |
| **Authority** | EDIT when owner null; self-approval block uses `owner_id or created_by_id` |
| **Permissions** | Same as D1 fallback |
| **Assignment** | Record creation |
| **Consumers** | My Work "returned to me", approvals |
| **Overlap** | May differ from `owner` |
| **Canonical target** | **Runtime Role Assignment** (requester) |
| **Migration risk** | **M** |

---

## E. Workflow template configuration

### E1. `WorkflowTemplateStep.assignee_role`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:2825`, `resolve_assignee()` |
| **Current name** | `UserProfile.Role` char value |
| **Actual meaning** | Template rule: match org member by profile role |
| **Scope** | `org` template → `object` instance |
| **Phase** | `config` → resolved at `runtime` |
| **Authority** | **None** — selects assignee only |
| **Permissions** | Resolver only |
| **Assignment** | Designer UI, migrations `0110` |
| **Consumers** | `workflow_execution.create_workflow_steps_from_template` |
| **Overlap** | Uses B1 global profile role |
| **Canonical target** | **Workflow Role Definition** → **Runtime Role Assignment** |
| **Migration risk** | **H** |

### E2. `WorkflowTemplateStep.specific_assignee`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:2826-2832` |
| **Actual meaning** | Fixed user assignee — overrides role match |
| **Scope** | `org` template |
| **Phase** | `config` |
| **Authority** | None — assignment only |
| **Permissions** | N/A |
| **Assignment** | Designer |
| **Consumers** | `resolve_assignee` (prefers specific) |
| **Overlap** | Direct user vs role-based |
| **Canonical target** | **Runtime Role Assignment** (explicit user) |
| **Migration risk** | **L** |

### E3. `WorkflowTemplate.fallback_signer`

| Field | Value |
|---|---|
| **Implementation** | Referenced in `workflow_execution.py` |
| **Actual meaning** | Signature step fallback user |
| **Scope** | `org` template |
| **Phase** | `config` |
| **Authority** | Signer assignment only |
| **Permissions** | Signature `can_actor_transition` |
| **Assignment** | Template config |
| **Consumers** | Signature step materialization |
| **Overlap** | Signer vs generic assignee |
| **Canonical target** | **Runtime Role Assignment** (signer) |
| **Migration risk** | **M** |

### E4. `ApprovalRoute` (`role_label`)

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:3050-3068` |
| **Current name** | `name`, `role_label` (display strings) |
| **Actual meaning** | **UI preview only** — does not gate runtime approvals |
| **Scope** | `org` template |
| **Phase** | `config` (display) |
| **Authority** | **None** |
| **Permissions** | None |
| **Assignment** | Designer, seeds `0071`/`0075`/`0077` |
| **Consumers** | Cockpit previews, NDA/DPA/MSA workflow UIs |
| **Overlap** | Confused with `ApprovalRule` — different authority |
| **Canonical target** | **Workflow Role Definition** (label only) or deprecate |
| **Migration risk** | **M** |

### E5. `ApprovalRule.approval_step` + `approver_role`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:4255-4263`, `workflow_routing.py` |
| **Current name** | Steps: `LEGAL`, `FINANCE`, `PRIVACY`, `EXECUTIVE`, `COMPLIANCE` |
| **Actual meaning** | Configured approval chain step + profile role resolver |
| **Scope** | `org` rule → `object` approval |
| **Phase** | `config` → `runtime` |
| **Authority** | Creates `ApprovalRequest` assignee; decision via `authorize_approval_actor` |
| **Permissions** | Approval actor authz |
| **Assignment** | Admin rule CRUD, seeds |
| **Consumers** | `build_approval_request_plan_for_contract`, MSA workflow |
| **Overlap** | Step name vs profile role vs specific approver |
| **Canonical target** | **Workflow Role Definition** + **Runtime Role Assignment** |
| **Migration risk** | **H** |

### E6. `ApprovalRule.specific_approver`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:4263` |
| **Actual meaning** | Fixed approver — overrides `approver_role` |
| **Scope** | `org` |
| **Phase** | `config` |
| **Authority** | Assignment to `ApprovalRequest.assigned_to` |
| **Permissions** | Approval authz on assignee |
| **Assignment** | Rule config |
| **Consumers** | `resolve_rule_assignee` |
| **Overlap** | Same pattern as E2 |
| **Canonical target** | **Runtime Role Assignment** |
| **Migration risk** | **L** |

---

## F. Workflow runtime assignments

### F1. `WorkflowStep.assigned_to`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:2909` |
| **Actual meaning** | Runtime step executor |
| **Scope** | `object` (per workflow instance) |
| **Phase** | `runtime` |
| **Authority** | Task completion via `can_actor_complete_task` (contract EDIT) |
| **Permissions** | Contract action checks |
| **Assignment** | Template resolution or manual |
| **Consumers** | Cockpits, My Work, assignments service |
| **Overlap** | Independent of profile role after assignment |
| **Canonical target** | **Runtime Role Assignment** |
| **Migration risk** | **M** |

### F2. `ApprovalRequest.assigned_to` / `delegated_to`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:4285+`, `approval_workflow.py` |
| **Actual meaning** | Primary approver + temporary delegate |
| **Scope** | `object` |
| **Phase** | `runtime` |
| **Authority** | `authorize_approval_actor` — assignee or delegate or org admin |
| **Permissions** | Approval service |
| **Assignment** | Rule plan, delegate, reassign (admin) |
| **Consumers** | Approvals UI/API, My Work |
| **Overlap** | Delegation vs reassignment semantics |
| **Canonical target** | **Runtime Role Assignment** + **Delegation** |
| **Migration risk** | **M** — canonical `ApprovalRequirement` mirrors |

### F3. `LegalTask.assigned_to` / `Deadline.assigned_to`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:2039`, `2376` |
| **Actual meaning** | Task/deadline executor |
| **Scope** | `object` |
| **Phase** | `runtime` |
| **Authority** | Task completion checks |
| **Permissions** | `can_actor_complete_task` |
| **Assignment** | Manual / workflow |
| **Consumers** | My Work, matter ops |
| **Canonical target** | **Runtime Role Assignment** |
| **Migration risk** | **L** |

---

## G. Reviewer and signer surfaces

### G1. `DPAReviewPack.reviewer`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:3963-3969`, `dpa_review.py:_can_review_pack` |
| **Actual meaning** | Privacy reviewer assignee |
| **Scope** | `object` |
| **Phase** | `runtime` |
| **Authority** | Review pack mutation if reviewer or org admin |
| **Permissions** | `_can_review_pack` — not `UserProfile.Role` |
| **Assignment** | Pack create/update |
| **Consumers** | Privacy Reviews queue, DPA API |
| **Overlap** | Functional assignee vs profile PRIVACY step |
| **Canonical target** | **Runtime Role Assignment** (privacy reviewer) |
| **Migration risk** | **M** |

### G2. `SignatureRequest.signer_email` / `signer_role`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:3589-3590`, `can_actor_transition` |
| **Actual meaning** | `signer_email` = auth; `signer_role` = **display label only** |
| **Scope** | `object` |
| **Phase** | `runtime` |
| **Authority** | Email match for SIGN/VIEW/DECLINE; creator/admin manage |
| **Permissions** | `can_actor_transition` |
| **Assignment** | Signature packet create |
| **Consumers** | E-sign workspace |
| **Overlap** | Role label does not grant access |
| **Canonical target** | **Runtime Role Assignment** (signer) + display label |
| **Migration risk** | **L** |

### G3. `ContractReviewFinding.assigned_reviewer`

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:1779-1781` |
| **Actual meaning** | AI review finding assignee |
| **Scope** | `object` |
| **Phase** | `runtime` |
| **Authority** | Finding workflow (contract-scoped) |
| **Permissions** | Contract access |
| **Assignment** | Review flow |
| **Consumers** | Document review |
| **Canonical target** | **Runtime Role Assignment** |
| **Migration risk** | **L** |

### G4. `DPARiskItem.owner` (functional codes)

| Field | Value |
|---|---|
| **Implementation** | `contracts/models.py:4087-4093` |
| **Current name** | `LEGAL`, `FINANCE`, `DPO_SECURITY`, etc. |
| **Actual meaning** | Risk item functional owner code — not user FK |
| **Scope** | `object` |
| **Phase** | `runtime` metadata |
| **Authority** | **None** — classification only |
| **Permissions** | None |
| **Assignment** | Manual / checklist |
| **Consumers** | DPA review UI |
| **Overlap** | Name overlap with approval steps |
| **Canonical target** | **Workflow Role Definition** (functional code) |
| **Migration risk** | **L** |

---

## H. Delegation and reassignment

### H1. Approval delegation (`delegated_to`, canonical mirror)

| Field | Value |
|---|---|
| **Implementation** | `ApprovalRequest`, `ApprovalRequirement`, `ApprovalDecision.acting_under_delegation` |
| **Actual meaning** | Temporary acting authority; original assignee preserved |
| **Scope** | `object` |
| **Phase** | `runtime` |
| **Authority** | Delegate may decide; audit records delegation holder |
| **Permissions** | `authorize_approval_actor`, `ApprovalWorkflowService.delegate` |
| **Assignment** | Assignee or admin delegates |
| **Consumers** | Approvals, audit `approval.delegated` |
| **Overlap** | Distinct from reassign |
| **Canonical target** | **Delegation** |
| **Migration risk** | **M** |

### H2. Approval reassignment (admin-only)

| Field | Value |
|---|---|
| **Implementation** | `ApprovalWorkflowService.reassign` |
| **Actual meaning** | Admin transfers assignee; clears delegation |
| **Scope** | `object` |
| **Phase** | `runtime` |
| **Authority** | OWNER/ADMIN only |
| **Permissions** | Org membership role check |
| **Assignment** | Admin action |
| **Consumers** | My Work, Approvals; audit `approval.reassigned` |
| **Canonical target** | **Runtime Role Assignment** change (governed) |
| **Migration risk** | **M** |

---

## I. Navigation visibility (not authorization)

### I1. Nav visibility predicates

| Symbol | Path | Visible when | Auth re-check |
|---|---|---|---|
| `_always` | `nav_config.py:71-72` | Active member | Membership on views |
| `_configuration_visible` | `nav_config.py:87-92` | Member + not pilot + `can_manage_organization` | Yes on config views |
| `_reviews_approvals_visible` | `nav_config.py:95-97` | Any member | `authorize_approval_actor` on actions |
| `_governance_visible` | `nav_config.py:83-84` | Member + not pilot | DPA/obligation view checks |

**Rule:** UI visibility ≠ authorization. Documented in characterization tests.

---

## J. Object-level authorization (server-side)

| Symbol | Path | Authority | Canonical target |
|---|---|---|---|
| `can_access_contract_action` | `permissions.py:70-87` | VIEW/COMMENT/AI: member; EDIT: admin or owner/creator | **Permission Set** + **Runtime Assignment** |
| `authorize_approval_actor` | `approval_workflow.py:89-130` | Tenant + assignee/delegate/admin; blocks owner self-decision | **Permission Set** + **Delegation** |
| `_can_review_pack` | `dpa_review.py:42-43` | Reviewer or org admin | **Runtime Assignment** |
| `can_delete_document` | `document_deletion.py:41-48` | Admin any; member own upload | **Permission Set** |
| `TenantScopedQuerysetMixin` | `view_support.py:43-49` | Tenant isolation | Platform invariant |
| `SignatureRequest.can_actor_transition` | `models.py:3646-3662` | Creator, admin, signer email | **Runtime Assignment** |

---

## K. Background jobs and system actors

| Symbol | Authority | Notes |
|---|---|---|
| `BackgroundJob` processors | **No per-user role check** | Jobs run in trusted worker context |
| `BackgroundJob.created_by` | Audit only | Not authorization |
| Lifecycle / reminder commands | Org-scoped queries | No membership role in processor |

**Canonical target:** **System Role** — explicit service principal; human roles must not apply to job execution.

---

## L. Seeds and fixtures

| Seed | Pattern | Risk |
|---|---|---|
| `seed_controlled_pilot` | Explicit `(org_role, profile_role)` pairs | Intentional dual-set |
| `seed_demo`, `seed_mvp_demo`, `seed_payrollminds_demo` | Same | Must preserve on backfill |
| `seed_data` | Profile only (legacy) | Incomplete dual-set |
| Migrations `0071`/`0075`/`0077`, `0110` | Template `assignee_role` backfill | Config-time |

---

## M. Audit events

| Event | Role relevance |
|---|---|
| `role_updated` | Organization membership role change |
| `approval.delegated` / `approval.reassigned` | Assignment/delegation changes |
| `scim_user_provisioned` / `scim_group_*` | Workspace role from IdP |
| Approval decisions | Immutable — role changes must not rewrite |

---

## Summary: primary conflicts

| ID | Conflict | Severity |
|---|---|---|
| **C-ID-01** | `ADMIN` in both `OrganizationMembership` and `UserProfile` | **High** |
| **C-ID-02** | `UserProfile.role` user-global vs org-scoped membership | **High** |
| **C-ID-03** | `ApprovalRoute.role_label` vs `ApprovalRule` runtime authority | **Medium** |
| **C-ID-04** | SCIM provisions workspace role only — profile role gap | **Medium** |
| **C-ID-05** | Nav visibility broader than mutation authority (by design) | **Low** (documented) |
| **C-ID-06** | `UserProfile.can_approve` defined but unused | **Low** |

---

## Tenant boundary statement

All runtime resolvers (`resolve_assignee`, `resolve_rule_assignee`, `authorize_approval_actor`) scope to contract organization. Cross-tenant access returns 404/403. Programme isolation suite: **75/75 PASS** on branch (see `TEST_RESULTS.md`). Formal PAR-SEC-003 roadmap closure remains **pending disposition** despite test fix on `main`.
