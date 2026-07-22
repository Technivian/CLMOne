# PAR-ID-001 — R5 authority transition definition (preparation)

**Status:** Preparation only — **not authorized**  
**Programme status:** R5 remains **Blocked**  
**Implementation reference (already on `main`, default off):** `contracts/services/process_role_resolver_authority.py`  
**Do not enable** `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED` under this document.

---

## Component matrix

| Component | Before R5 (current) | Proposed after R5 activation (staging-equivalent only, if voted) |
|---|---|---|
| Diagnostic comparison (`PROCESS_ROLE_RESOLVER_PARITY_ENABLED`) | Off by default; may be on only under separate diagnostic auth | **Proposed during observation:** on only if Motion set authorizes it; otherwise off |
| Canonical resolution **calculation** | May compute when comparison/authority code paths run; not returned as authority today | Calculates for allowlisted org + CERTAIN non-ADMIN role labels on approved paths |
| **Authoritative result selection** | **Legacy always** | **Canonical** only when flag on, org allowlisted, CERTAIN eligible, active PRA exists; else legacy (or `None` on cross-tenant) |
| Legacy fail-open / fallback | N/A for authority (legacy is sole authority) | On canonical error / missing / inactive / excluded → **return legacy**; never raise into caller |
| ADMIN ambiguity handling | Explicit AMBIGUOUS; non-authoritative | **Unchanged** — excluded (`cutover_excluded`); legacy returned; P2 remains rejected |
| Assignment persistence | Existing PRA rows; no auto-repair | **No writes** by authority path; no automatic repair |
| Permission enforcement | Unchanged by process-role resolvers | **Unchanged** — R5 must not expand privileges/permissions/membership/navigation |
| Audit / telemetry | Parity events when diagnostic on | Authority events: `role.resolver.canonical_used`, `legacy_fallback`, `cutover_excluded`, `canonical_failure`, `cross_tenant_anomaly` — permission-safe fields only |

---

## Approved resolver paths (implementation already present)

1. `WorkflowTemplateStep.resolve_assignee` (and launch/materialize/simulation chains that call it) — role-based only; `specific_assignee` short-circuits to legacy.
2. `workflow_routing.resolve_rule_assignee` (and plan/initiate/API/workflow-create chains) — role-based only; `specific_approver` short-circuits to legacy.

---

## Eligibility (CERTAIN only)

Canonical authority may apply only when **all** hold:

- `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED=true` in the **named** environment;
- contract/organization slug ∈ `PROCESS_ROLE_CANONICAL_RESOLVER_ORG_ALLOWLIST` (empty allowlist = **no** orgs);
- role label maps with **CERTAIN** confidence to a non-prohibited process code;
- active org-scoped `ProcessRoleAssignment` exists for that code;
- path is one of the two approved resolvers above.

---

## Hard exclusions (must remain)

- profile `ADMIN` / `legacy_process_admin` / AMBIGUOUS mappings → legacy + `cutover_excluded`
- workspace `OWNER` / `ADMIN` / `MEMBER` → legacy + excluded
- missing or inactive assignment → legacy fallback
- cross-tenant org mismatch → **fail closed** (`None`); no cross-tenant legacy adoption of foreign identity
- automatic ADMIN mapping (**P2**) → **rejected**
- privilege / permission / membership / signer / approval / navigation changes → **out of scope**

---

## Invariants that must hold under any authorized R5 run

- Tenant isolation
- Server-side authorization unchanged by this flag
- Deterministic assignment reasoning (PRA + RoleDefinition catalogue)
- Explicit ambiguity (never relabel AMBIGUOUS as MATCH)
- Non-authoritative ADMIN ambiguity
- Fail-open return to legacy on canonical failure (caller still gets a safe legacy result; cross-tenant remains fail-closed)
- Reversible flags (flag-off restores pre-cutover authority)
- Complete audit evidence (permission-safe)

---

## Explicit non-goals of R5

- Production activation
- Dual-return of both users to callers as an API contract
- ADMIN authority / PAR-ID-002
- Automatic repair of missing assignments
- Legacy retirement / removal of legacy fallback
- Permission expansion
