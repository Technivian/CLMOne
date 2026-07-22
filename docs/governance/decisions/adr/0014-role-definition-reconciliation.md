# ADR-0014: Role Definition reconciliation

- Status: **Proposed**
- Date: 2026-07-22
- Deciders: Pending ratification — @haroonwahed (Product) · @Technivian (Engineering)
- Related: PAR-ID-001, CANONICAL_DOMAIN_MODEL §2.5, SECURITY_PRIVACY_ACCESS_AND_AUDIT, WORKFLOW_ENGINE_AND_DESIGNER, PAR-APR-001
- Decision package: [`0014-governance-decision-package-2026-07-22.md`](0014-governance-decision-package-2026-07-22.md)
- Evidence: `docs/audits/evidence/2026-07-22-par-id-001/`

## Approval metadata

| Field | Value |
|---|---|
| **Submitted for ratification** | Pending |
| **Ratification status** | **Proposed** — discovery complete; awaiting governance vote |
| **Required before Accepted** | Named approvers; authority basis; written consent; vote timestamp |
| **Acceptance scope (if ratified)** | Terminology, target model, mapping registry design, compatibility period. **Would not authorize** privilege cutover until PAR-SEC-003 disposed and implementation authorization recorded. |
| **Evidence** | `ROLE_USAGE_MATRIX.md`, `TARGET_ROLE_MODEL.md`, `CUTOVER_PLAN.md` |

## Problem

Accepted domain documentation defines **Role Definition** (CANONICAL_DOMAIN_MODEL §2.5) as a canonical process responsibility — requester, contract owner, legal reviewer, finance approver, privacy reviewer, signer, archiver — **distinct from workspace permissions**.

CLM One maintains **two incompatible role systems**:

| System | Storage | Scope | Primary use |
|---|---|---|---|
| Workspace permission | `OrganizationMembership.role` | Org-scoped | Admin, configuration, elevated edit |
| Process role (interim) | `UserProfile.role` | **User-global** | Workflow assignee matching, approval rules |

**Conflicts identified (PAR-ID-001 discovery):**

- **C-ID-01:** `ADMIN` exists in both enums with different semantics.
- **C-ID-02:** `UserProfile.role` is user-global; membership is org-scoped — multi-org users ambiguous.
- **C-ID-03:** `ApprovalRoute.role_label` is display-only; `ApprovalRule` is runtime authority — easily conflated.
- **C-ID-04:** SCIM provisions workspace role only; profile role not provisioned.

Gap audit G-DOM rates this **Conflicting / High**. Pilot seeds intentionally set both layers; removal without mapping breaks workflow routing.

## Terminology (proposed canonical)

| Term | Meaning | Interim storage |
|---|---|---|
| **Workspace Role** | Organization membership permission | `OrganizationMembership.role` |
| **Permission Set** | Concrete server-evaluated capabilities | `permissions.py` (implicit today) |
| **Workflow Role Definition** | Stable process responsibility label | `UserProfile.role` on templates/rules (transitional) |
| **Runtime Role Assignment** | User/resolver bound to instance | `assigned_to`, `owner`, `reviewer`, `signer_email` |
| **Delegation** | Temporary acting authority | `delegated_to`, canonical approval delegation fields |

UI and documentation must label which layer applies. **UI visibility is not authorization.**

## Decision (proposed — not Accepted)

### 1. Five-concept separation

Adopt the target model in `TARGET_ROLE_MODEL.md`:

1. Workspace Role — org admin authority
2. Permission Set — server-side capability evaluation
3. Workflow Role Definition — configuration-time process labels
4. Runtime Role Assignment — execution-time user/resolver binding
5. Delegation — governed temporary authority

### 2. Mapping registry (additive)

Introduce governed `RoleDefinition` catalogue + `LegacyRoleMapping` table (see `CUTOVER_PLAN.md` §2–3):

- Document every legacy value → canonical Definition or explicit `legacy_unknown`.
- **`UserProfile.ADMIN` maps to `legacy_process_admin` (unknown bucket)** — never to Workspace ADMIN.
- No mapping row may grant permissions not already enforced today.

### 3. Org-scoped process roles (target)

Replace user-global `UserProfile.role` as resolver input with org-scoped `OrganizationUserRole` during compatibility period. Dual-read until verification gates pass.

### 4. Resolver contract

Centralize in `role_resolution.py` (future):

- Tenant-scoped resolution only.
- `specific_assignee` / `specific_approver` precedence.
- `fail_closed=True` for unresolved assignments — no admin fallback.
- Historical decisions and audit rows immutable on role change.

### 5. Server-side authority unchanged until cutover authorization

Until implementation authorization after Acceptance:

- `OrganizationMembership.Role` gates org admin surfaces.
- `UserProfile.Role` gates workflow/approval matching.
- **No privilege widening.**

### 6. Explicit non-goals

- SCIM / IdP process role sync redesign
- Django Group / `has_perm` adoption
- Client portal role overhaul
- Removal of legacy enums before dual-read verification
- PAR-SEC-003 bypass

## Alternatives considered

| Alternative | Outcome |
|---|---|
| **Collapse to single role enum** | **Rejected** — conflates workspace admin with process responsibilities; violates §2.5 |
| **Rename only (no mapping table)** | **Rejected** — insufficient for `ADMIN` ambiguity, audit, backfill |
| **Immediate `UserProfile.role` removal** | **Rejected** — breaks resolvers, seeds, pilot |
| **Django Groups RBAC** | **Deferred** — large scope; Permission Set may remain custom functions initially |
| **Keep status quo indefinitely** | **Rejected** — gap audit High; multi-org and SCIM gaps worsen |

## Authorization implications

| Area | Implication |
|---|---|
| Contract EDIT | Remains: admin OR owner/creator — not profile role |
| Approval decisions | Remains: `authorize_approval_actor` — assignee/delegate/admin; owner self-block |
| Configuration nav | Remains: `can_manage_organization` |
| Workflow assignee | Resolver uses Role Definition → Runtime Assignment; no hidden permission grant |
| API tokens | Unchanged — separate machine Permission Set |
| Background jobs | System actor explicit — no human role inheritance |

**Acceptance does not authorize changing these rules** — only the mapping architecture and terminology.

## Migration strategy

See `CUTOVER_PLAN.md`. Summary:

1. Additive `RoleDefinition` registry (0112)
2. Legacy mapping table with unknown flags (0113)
3. Optional FK on template/rule rows (0114)
4. Org-scoped role table dual-read (0115)
5. Verification gates + feature flag
6. Single-write cutover (0117)
7. Legacy deprecation (0118) — only after removal criteria met

## Compatibility period

- Dual-write: new config writes legacy + canonical.
- Dual-read: resolvers prefer canonical, fallback mapping.
- Pilot seeds continue dual-set until backfill verified.
- Minimum one release cycle dual-read before single-write.

## Consequences

- Characterization tests lock interim semantics (`tests/test_par_id_001_characterization.py` — 19 tests).
- UX copy audit required across My Work, Approvals, Admin.
- SCIM gap documented — workspace-only provisioning until separate decision.
- PAR-ID-001 remains **In progress** until Accepted + implementation slices delivered.

## Rollback approach

Feature flag `ROLE_DEFINITION_CANONICAL_READ` (proposed, default off). Migration reverse checkpoints CP-1 through CP-4 in `CUTOVER_PLAN.md`. Legacy write path preserved until ID-7 criteria met.

## Tenant-isolation requirements

- All resolvers must scope to contract organization.
- Cross-tenant assignment attempts return None/404.
- Programme isolation suite must be green.
- **PAR-SEC-003 must be formally disposed before privilege cutover** — even if technical test passes.

**Current programme state:** `tests.test_cross_tenant_isolation` **75/75 PASS** on branch; PAR-SEC-003 roadmap closure **pending** — cutover **blocked**.

## Implementation authorization boundary

| ADR-0014 Accepted authorizes | Does **not** authorize |
|---|---|
| Planning, mapping design, ID-1 branch prep | Schema migrations without implementation vote |
| Characterization test maintenance | Permission widening |
| UX copy audit | Single-write cutover |
| | Legacy enum removal |
| | PAR-SEC-003 waiver |

Separate **implementation authorization** vote required before migration 0112+.

## Approval

**Proposed only.** See decision package for motions, approvers, and conditions. Acceptance required before mapping implementation, backfill, or role enum changes.
