# Implementation authorization — migration 0113 process-role adapter

**Programme:** PAR-ID-001  
**ADR:** ADR-0014 **Accepted** 2026-07-22T11:00:00Z  
**Prerequisite:** PR [#53](https://github.com/Technivian/CLMOne/pull/53) merged to `main` @ `0bf7c9dc` (migration 0112 catalogue)  
**Authorization timestamp:** 2026-07-22T11:15:00Z  
**Status:** **Authorized**

---

## Motions and votes

### Motion — Authorize migration 0113 (narrow)

**Text:** Authorize additive organization-scoped process-role assignment model, compatibility mapping, dual-read diagnostic service, truthful legacy backfill, audit events, tenant-isolation protections, and parity/drift reporting — **non-authoritative for permissions and runtime routing**.

| Approver | GitHub identity | Governance capacity | Authority basis | Vote | Consent |
|---|---|---|---|---|---|
| Haroon Wahed | @haroonwahed | Product governance / repository steward | `.github/CODEOWNERS` (`/docs/`); Charter v2.0 | **Approve** | Written consent recorded |
| Technivian | @Technivian | Engineering governance / repository steward | `.github/CODEOWNERS` (`/contracts/`); PDR-0003 | **Approve** | Written consent recorded |
| Security & privacy (advisory) | @Technivian | Security review capacity | `SECURITY_PRIVACY_ACCESS_AND_AUDIT.md`; Charter §7 | **Approve with conditions** | Conditions below |

**Result:** **Authorized**

---

## Authorized scope

| Item | Authorized |
|---|---|
| Additive org-scoped process-role assignment model | **Yes** |
| Compatibility mapping from legacy role representations | **Yes** |
| Dual-read diagnostic / parity service | **Yes** |
| Truthful legacy backfill (certain mappings only) | **Yes** |
| Audit events for assignment lifecycle + drift | **Yes** |
| Tenant-isolation protections | **Yes** |
| Parity and drift reporting | **Yes** |

---

## Explicitly excluded

| Item | Authorized |
|---|---|
| Permission changes | **No** |
| `OrganizationMembership` authority changes | **No** |
| Production resolver flip | **No** |
| Authorization gate changes | **No** |
| Navigation changes | **No** |
| `UserProfile.role` removal or behaviour change | **No** |
| Approval or signer resolution changes | **No** |
| Workflow runtime assignment cutover | **No** |
| Privilege migration | **No** |
| PAR-APR-002 / PAR-WF-010 work | **No** |

---

## Security advisory conditions

1. Dual-read output must not be consumed by authorization, approval gating, signer resolution, workflow routing, or contract access.
2. Ambiguous `UserProfile.ADMIN` must map to `legacy_process_admin` / `LEGACY_UNKNOWN` — never Workspace ADMIN.
3. Cross-tenant user/membership binding prohibited.
4. Programme isolation suite must remain green.
5. Privilege / production resolver cutover requires a **future** separate authorization.

---

## Allowed dual-read consumers

- Diagnostics
- Parity reporting
- Migration planning
- Non-authoritative administrative display

## Prohibited dual-read consumers

- Authorization
- Approval gating
- Signer resolution
- Workflow routing
- Contract access
- Runtime assignment decisions

---

## Next slice (not authorized here)

Production dual-write / resolver flip behind feature flag — requires new implementation authorization.
