# PAR-ID-001 — test results

**Date:** 2026-07-22  
**Branch:** `cursor/feat-par-id-001-shadow-role-sync`  
**PR #54 merge:** `58966de7`

## Slice 3 gate (shadow sync)

| Suite | Result |
|---|---|
| `tests.test_par_id_001_shadow_sync` | **10 PASS** |
| `tests.test_par_id_001_role_definition` | **PASS** |
| `tests.test_par_id_001_process_role_assignment` | **PASS** |
| `tests.test_par_id_001_characterization` | **19 PASS** |
| `tests.test_approval_authorization` + `tests.test_approval_workflow` + `tests.test_par_apr_001_approval` | **33 PASS** |
| `tests.test_par_wf_010_characterization` | **4 PASS** |
| `tests.test_cross_tenant_isolation` | **75 PASS** |
| Combined gate (incl. self-approval in extended run) | **177 PASS** |
| `make check` / governance authority script | **PASS** |

## Prior slices

| Slice | Migration | Result |
|---|---|---|
| Catalogue | 0112 forward / rollback / re-forward | PASS |
| Process-role adapter | 0113 forward / rollback / re-forward | PASS |

Production authority remains legacy resolvers. Privilege / resolver cutover **not** authorized.
No new migration in Slice 3 (0113 schema sufficient).
