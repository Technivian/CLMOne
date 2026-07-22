# Implementation authorization — PAR-ID-001 Slice 3 shadow role sync

**Programme:** PAR-ID-001  
**ADR:** ADR-0014 **Accepted**  
**Prerequisite:** PR [#54](https://github.com/Technivian/CLMOne/pull/54) merged to `main` @ `58966de7`  
**Request timestamp:** 2026-07-22T11:40:00Z  
**Status:** **Requested** — votes not invented; record approvals on this PR / in a follow-up meeting record

---

## Motion — Authorize feature-flagged shadow synchronization

**Text:** Authorize feature-flagged shadow synchronization from selected legacy process-role writes into `ProcessRoleAssignment`, deterministic parity reporting, drift detection and audit evidence, management-command diagnostics, and staging activation — **without** making canonical assignments authoritative for permissions or runtime routing.

| Approver | GitHub identity | Governance capacity | Authority basis | Vote | Consent |
|---|---|---|---|---|---|
| Haroon Wahed | @haroonwahed | Product governance | CODEOWNERS `/docs/`; Charter v2.0 | **Requested** | Pending |
| Technivian | @Technivian | Engineering governance | CODEOWNERS `/contracts/`; PDR-0003 | **Requested** | Pending |
| Security & privacy (advisory) | @Technivian | Security review capacity | SECURITY_PRIVACY_ACCESS_AND_AUDIT; Charter §7 | **Requested (advisory, with conditions)** | Pending |

**Result:** **Not yet authorized by recorded vote** — implementation lands as draft PR for the required approvers; do not treat this file as fabricated consent.

---

## Requested scope

| Item | Requested |
|---|---|
| Feature flags `PROCESS_ROLE_SHADOW_WRITE_ENABLED`, `PROCESS_ROLE_PARITY_REPORTING_ENABLED` (default off) | **Yes** |
| Shadow sync from `UserProfile.role` writes into org-scoped `ProcessRoleAssignment` | **Yes** |
| Deterministic parity reporting command | **Yes** |
| Drift detection + audit evidence | **Yes** |
| Staging activation of flags | **Yes** |
| Management-command diagnostics | **Yes** |

---

## Explicitly excluded

| Item | Authorized |
|---|---|
| Production resolver flip | **No** |
| Permission or privilege changes | **No** |
| `OrganizationMembership` authority changes | **No** |
| `UserProfile.role` removal | **No** |
| Authorization-gate changes | **No** |
| Approval or signer resolver changes | **No** |
| Navigation changes | **No** |
| Workflow assignment cutover | **No** |
| PAR-APR-002 / PAR-WF-010 | **No** |

---

## Security advisory conditions (proposed)

1. Legacy `UserProfile.role` remains authoritative while flags are off or on.
2. Shadow failure must not roll back or corrupt the legacy write; fail closed on cross-tenant violations; audit `role.assignment.shadow_sync_failed`.
3. `profile_role` ADMIN → `legacy_process_admin` only; workspace ADMIN/OWNER/MEMBER never shadow-written as process roles.
4. Parity output must not drive authorization, approval, signer, or workflow routing.
5. Flags default **off** in all environments until staging activation is deliberate.

---

## Next slice (not requested here)

Production resolver dual-read consumption / privilege cutover — requires new authorization.
