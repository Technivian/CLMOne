# PAR-ID-001 — ADMIN role mapping decision (Product + Security)

**Baseline `main`:** `8316a756`  
**Status:** **Proposed — pending Product / Security / Engineering votes**  
**Hard rule:** Workspace administrator privileges (`OrganizationMembership.Role.ADMIN` / OWNER) are **not** process-role assignments and must never be silently merged with `UserProfile.Role.ADMIN`.

Related: [`REMEDIATION_ANALYSIS.md`](REMEDIATION_ANALYSIS.md), [`THREAT_REVIEW.md`](THREAT_REVIEW.md), [`../2026-07-22-par-id-001/PROCESS_ROLE_MAPPING_MATRIX.md`](../2026-07-22-par-id-001/PROCESS_ROLE_MAPPING_MATRIX.md)

---

## Separation of concerns

| Concept | Source of truth today | Grants |
|---|---|---|
| Workspace administrator | `OrganizationMembership.role` ∈ {OWNER, ADMIN} | Org management, many authz gates (`can_manage_organization`, approval admin paths, etc.) |
| Legacy process label “ADMIN” | `UserProfile.role == ADMIN` | Used by **legacy** workflow/approval **role resolvers** as a process label (first matching member) — **not** the same as workspace ADMIN |
| Canonical process role | `ProcessRoleAssignment` + `RoleDefinition` | Diagnostic / future routing only; **not** authoritative today |

**Collision example:** `pilot_admin` may be workspace ADMIN **and** profile ADMIN — meanings must remain distinct in evidence and policy.

---

## Options (implementation must not choose implicitly)

| ID | Policy | Catalogue / confidence | Shadow / backfill | Resolver parity | Cutover implication |
|---|---|---|---|---|---|
| **P1** | Map to `legacy_process_admin` | Keep AMBIGUOUS | May create diagnostic PRA only when write flags authorized | Always classify **AMBIGUOUS** (never auto-MATCH for readiness) | Forbidden to route on this mapping alone |
| **P2** | Map to a specific canonical process role (e.g. `partner_reviewer`) | Would require CERTAIN (or new code) | Would create real process PRA | Could become MATCH | **High privilege-confusion risk** — not recommended |
| **P3** | No automatic process role | Do not create PRA from profile ADMIN | Skip ADMIN in backfill/shadow | LEGACY_ONLY or AMBIGUOUS with empty canonical | Legacy still resolves ADMIN label; canonical ignores |
| **P4** | Explicit per-workspace mapping | Org setting: profile ADMIN → chosen RoleDefinition **or** none | Only create PRA when org config present | MATCH only if explicit assignment exists | Safest for multi-tenant variance; more product complexity |

### Recommended option (for vote)

**Recommend P1 for catalogue continuity + P3 semantics for authority:**

- Keep catalogue code `legacy_process_admin` with **AMBIGUOUS** confidence (P1 labels).  
- Treat profile ADMIN as **non-authoritative for any future canonical routing** (P3 authority posture).  
- Any org that needs an ADMIN-profile user in a process lane must receive an **explicit** CERTAIN process role assignment (legal_reviewer / partner_reviewer / …) under managed assignment APIs — not via automatic ADMIN mapping.  
- Optionally evolve to **P4** later via PDR if tenants need configurable ADMIN→process maps.

**Do not recommend P2.**

---

## Security consequences

| Topic | Under recommended posture |
|---|---|
| Privilege escalation | Workspace ADMIN does not gain process PRA automatically; process PRA does not grant workspace admin |
| Role confusion | AMBIGUOUS label preserved; dual-read continues to flag membership×profile ADMIN coexistence |
| Fallback abuse | Legacy resolvers may still pick profile ADMIN users for `assignee_role=ADMIN` / `approver_role=ADMIN` — **unchanged** until separate resolver cutover; document as residual |
| Audit | Mapping confidence AMBIGUOUS; events must not claim CERTAIN; evidence stays org-scoped |

---

## Fallback behaviour

| Mode | Behaviour |
|---|---|
| Flags off (current) | Legacy resolvers only; PRA unused |
| Resolver parity on (not authorized to enable) | Compare; return legacy; ADMIN → AMBIGUOUS |
| After P1+P3 acceptance | Same runtime; policy forbids treating ADMIN mapping as cutover-ready |
| After explicit CERTAIN assignment | That assignment may MATCH for the **non-ADMIN** process code only |

---

## Audit requirements

1. Never log workspace and process ADMIN as interchangeable.  
2. Dual-read / parity reports must emit `ambiguous_mapping` / `AMBIGUOUS` for profile ADMIN.  
3. Any future write that creates `legacy_process_admin` PRA must record `mapping_confidence=AMBIGUOUS` and `authoritative_for_runtime=false`.  
4. Remediation exports: org_id, user_id, role codes, classification — no credentials/contract content.

---

## REM-03 — Reclassification of ambiguous results against proposed policy

Programme target: **13** AMBIGUOUS ADMIN mappings (**unverified** until inventory).  
Illustrative seed set: **8** profile-ADMIN membership rows.

| Policy | MATCH | Remain AMBIGUOUS | Require explicit assignment | Notes |
|---|---|---|---|---|
| **P1** (status quo labels) | 0 | 13 (or N) | 0 for mapping; optional explicit CERTAIN roles later | Parity stays AMBIGUOUS even if PRA exists |
| **P2** (specific CERTAIN role) | up to N if PRA created | 0 | 0 | Rejected — conflates meanings |
| **P3** (no automatic process role) | 0 | N (or LEGACY_ONLY if no PRA) | **N** if process coverage required | Preferred authority posture |
| **P4** (per-workspace) | only where org config + PRA | remainder | remainder without config | Future PDR |
| **Recommended P1 labels + P3 authority** | 0 from ADMIN map | **all N** | **all N** that need process coverage via non-ADMIN codes | Safe default |

**Do not mutate data** while classifying.

---

## Product vote block

```text
PAR-ID-001 ADMIN ROLE MAPPING DECISION — 2026-07-22
Baseline main: 8316a756

@haroonwahed Product: Approve | Reject
Timestamp: <actual ISO-8601 UTC>

Selected option: P1 | P2 | P3 | P4 | P1+P3 (recommended)
Workspace ADMIN remains separate from process ADMIN: yes | no
No staging activation / cutover by this vote: yes | no
```

## Security advisory vote block

```text
@Technivian Security advisory: Approve with conditions | Reject
Timestamp: <actual ISO-8601 UTC>

Selected option acknowledged: <option>
Conditions:
1. Never merge workspace ADMIN with process ADMIN
2. No automatic privilege grant via legacy_process_admin
3. AMBIGUOUS retained in diagnostics until explicit CERTAIN assignment
4. Threat review THREAT_REVIEW.md accepted
Conditions acknowledged: yes | no
```

## Engineering vote block

```text
@Technivian Engineering: Approve | Reject
Timestamp: <actual ISO-8601 UTC>

Engineering will not implement ADMIN→CERTAIN auto-mapping without Product+Security acceptance.
Separate implementation authorization required before any PRA writes.
```
