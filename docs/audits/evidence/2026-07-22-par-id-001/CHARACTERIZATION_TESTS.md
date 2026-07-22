# PAR-ID-001 — Characterization tests

**Module:** `tests/test_par_id_001_characterization.py`  
**Purpose:** Lock interim dual-role semantics before Role Definition reconciliation  
**Count:** **19 tests** across 8 test classes

## Test classes

| Class | Tests | Coverage |
|---|---|---|
| `RoleDefinitionInterimCharacterizationTests` | 5 | Dual enum coexistence, ADMIN collision, no auto-sync |
| `WorkspaceRoleCharacterizationTests` | 3 | `can_manage_organization`, contract EDIT by workspace role |
| `WorkflowRoleDefinitionCharacterizationTests` | 3 | Template/rule assignee resolution by profile role |
| `RuntimeAssignmentCharacterizationTests` | 1 | `assigned_to` independent of profile role change |
| `DelegationCharacterizationTests` | 2 | Delegate authority; original assignee preserved |
| `SignerResolutionCharacterizationTests` | 2 | Email-based signer auth; `signer_role` display only |
| `NavigationVsAuthorizationCharacterizationTests` | 1 | Member sees Reviews nav, not Configuration |
| `CrossTenantRoleCharacterizationTests` | 2 | Cross-tenant approval 404; org-scoped resolver |

## Run command

```bash
.venv/bin/python manage.py test tests.test_par_id_001_characterization --settings=config.settings_test
```

## Programme isolation (related)

```bash
.venv/bin/python manage.py test tests.test_cross_tenant_isolation --settings=config.settings_test
```

## Cutover invariant

Any future reconciliation MUST either:

1. Preserve these interim behaviours during dual-read, or
2. Explicitly migrate with backfill + characterization test updates + Accepted ADR-0014

## PAR-SEC-003 note

Privilege cutover requires formal PAR-SEC-003 disposition even if isolation suite passes.
