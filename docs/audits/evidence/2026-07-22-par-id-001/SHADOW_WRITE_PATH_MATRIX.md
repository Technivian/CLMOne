# PAR-ID-001 — Shadow write path matrix

**Date:** 2026-07-22  
**Authorization:** `SHADOW_ROLE_SYNC_IMPLEMENTATION_AUTHORIZATION.md`  
**Branch:** `cursor/feat-par-id-001-shadow-role-sync`

---

## A. Process-role writes (`UserProfile.role`) — shadow-eligible

| ID | Source | Org context | Legacy field/value | Canonical mapping | Confidence | Transaction | Actor | Audit | Failure handling | Shadow safe? |
|---|---|---|---|---|---|---|---|---|---|---|
| UP-SEED-05..08 | `seed_demo` / `seed_mvp_demo` / `seed_controlled_pilot` / `seed_payrollminds_demo` `update_or_create(defaults.role)` | Yes | `profile_role` / enum | Per PROCESS_ROLE_MAPPING_MATRIX | CERTAIN or AMBIGUOUS (ADMIN) | Same request as seed | management command | shadow create/deactivate | Legacy write wins; shadow failure audited | **Yes** (via `UserProfile.save`) |
| UP-SEED-01..04 | `seed_data` `get_or_create(defaults.role)` | Later | `profile_role` | Same | CERTAIN/AMBIGUOUS | seed txn | command | same | same | **Yes** on create |
| UP-IMP-* | `get_or_create` without role | Often yes | default `ASSOCIATE` on create | → `legal_reviewer` | CERTAIN | request/command | user/system | same | same | **Yes** on create only |
| UP-FORM | Profile form | yes | role **not in form** | n/a | n/a | n/a | user | n/a | n/a | **N/A** (no write) |
| UP-SCIM/SAML | SCIM/SAML | yes | does **not** set profile.role | n/a | n/a | n/a | IdP | n/a | n/a | **N/A** (membership only) |
| UP-QS-UPDATE | `UserProfile.objects.update(role=…)` | varies | `profile_role` | Same | varies | caller txn | system | detection + sync attempt | Legacy update completes; shadow audited | **Yes** (QuerySet hook) |

## B. Workspace membership writes — **not** shadow-written as process roles

| ID | Source | Notes |
|---|---|---|
| OM-* | `OrganizationMembership.role` create/update (admin, invite, SCIM, SAML, seeds) | Workspace Role only |
| INV-* | `OrganizationInvitation.role` | Pending workspace role |

## C. Shadow sync policy

| Rule | Behavior |
|---|---|
| Flag off | No shadow writes; legacy paths unchanged |
| Flag on | After successful `UserProfile` role persist, sync all active org memberships |
| Idempotent | Existing matching active assignment → no-op |
| Role change | Deactivate prior `profile_role`-sourced active assignments; create/activate mapped target |
| ADMIN | → `legacy_process_admin` (AMBIGUOUS); never `workspace_admin` |
| Membership ADMIN | Never creates process assignment |
| Cross-tenant | Fail closed; audit `shadow_sync_failed` |
| Shadow exception | Logged + audited; **does not** reverse legacy write |

## D. Production gap note

No production UI/API currently sets a deliberate non-default process role. Shadow sync primarily covers seeds, default create (`ASSOCIATE`), and future admin/API writers that use `UserProfile.save` / role `QuerySet.update`.
