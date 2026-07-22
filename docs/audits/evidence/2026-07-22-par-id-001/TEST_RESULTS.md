# PAR-ID-001 — test results

**Date:** 2026-07-22  
**Branch:** `cursor/feat-par-apr-001-foundation-governance`  
**Settings:** `config.settings_test` (in-memory SQLite)

---

## PAR-ID characterization suite

| Module | Result |
|---|---|
| `tests.test_par_id_001_characterization` | **19 PASS** |

### Coverage areas

- Workspace role authority (`can_manage_organization`, contract EDIT)
- Workflow role definition resolution (`resolve_assignee`, `resolve_rule_assignee`)
- Runtime assignment independence from profile role
- Delegation (delegate may act; assignee preserved)
- Signer email vs display role label
- Navigation visibility vs configuration authorization
- Cross-tenant approval denial (404)
- Org-scoped assignee resolution

---

## Programme tenant isolation

| Module | Result |
|---|---|
| `tests.test_cross_tenant_isolation` | **75 PASS** |

Includes `ContractIsolationTest.test_list_shows_only_own_org` (PAR-SEC-003 technical fix on `main`).

---

## PAR-SEC-003 disposition

| Check | Status |
|---|---|
| Isolation test passes | **Yes** |
| Roadmap PAR-SEC-003 formally closed | **No** |
| Privilege cutover authorized | **No** — blocked pending disposition |

---

## Tenant isolation conclusion

**Technical:** Cross-tenant isolation suite is green (75/75) on this branch. Resolvers and approval authz return 404/403 across tenant boundaries in characterized paths.

**Programme:** Tenant isolation is **not proven at programme assurance level** for PAR-ID-001 cutover until PAR-SEC-003 is formally disposed in roadmap governance. Discovery and characterization may proceed; **privilege cutover remains blocked**.
