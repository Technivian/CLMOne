# PAR-ID-001 evidence summary — 2026-07-22

## Status: In progress — discovery complete

**Programme:** Role Definition reconciliation (Milestone 3)  
**ADR:** ADR-0014 **Proposed** — decision package ready, not ratified  
**Next gate:** ADR-0014 ratification vote (@haroonwahed + @Technivian)

### Problem
Dual role systems conflict with canonical Role Definition (CANONICAL_DOMAIN_MODEL §2.5). Six primary conflicts documented (C-ID-01 through C-ID-06) in `ROLE_USAGE_MATRIX.md`.

### Discovery deliverables (complete)
- Full role usage matrix — 30+ role-like concepts inventoried
- Target five-concept model (`TARGET_ROLE_MODEL.md`)
- Cutover plan with additive migration sequence (`CUTOVER_PLAN.md`) — **not authorized**
- ADR-0014 updated with authorization boundaries
- Governance decision package (motions drafted, votes not recorded)
- Characterization tests — **19 tests** (`tests/test_par_id_001_characterization.py`)

### Primary conflicts
| ID | Conflict | Severity |
|---|---|---|
| C-ID-01 | `ADMIN` in membership vs profile | High |
| C-ID-02 | User-global profile vs org membership | High |
| C-ID-03 | ApprovalRoute display vs ApprovalRule runtime | Medium |
| C-ID-04 | SCIM workspace-only provisioning | Medium |

### Explicit non-goals (unchanged)
- No schema changes in this slice
- No privilege model changes
- No enum removal
- No SCIM / RBAC redesign

### Tenant isolation
- Programme suite: **75/75 PASS** (`tests.test_cross_tenant_isolation`)
- PAR-SEC-003: roadmap **not formally closed** — privilege cutover **blocked**

### Next implementation step (after ADR-0014 Accepted + authorization)
Migration `0112_role_definition_registry` on dedicated branch — additive catalogue only; no resolver flip.
