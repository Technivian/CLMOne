# PAR-ID-001 Slice 4 — Resolver parity test matrix

**Status:** Planned — implement only after [`RESOLVER_PARITY_IMPLEMENTATION_AUTHORIZATION.md`](RESOLVER_PARITY_IMPLEMENTATION_AUTHORIZATION.md) is **Authorized**.  
**Flag:** `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` (default false)  
**Hard rule:** Canonical comparison must never change the value returned to production callers.

---

## Behavioural invariants

| # | Assertion |
|---|---|
| I1 | Flag off → legacy resolvers behave identically (no extra failures; return unchanged) |
| I2 | Flag on → returned actor/role is **byte-for-byte / identity-equal** to legacy-only run |
| I3 | Canonical exception → legacy result still returned; `RESOLUTION_ERROR` recorded |
| I4 | Drift never writes `UserProfile`, `OrganizationMembership`, or auto-repairs PRA |
| I5 | Cross-tenant anomaly never “fixes” by adopting canonical user |
| I6 | No contract content / credentials in report or audit payload |

---

## Classification cases

| Classification | Test intent |
|---|---|
| MATCH | Legacy user equals sole/primary canonical candidate for mapped role |
| LEGACY_ONLY | Legacy returns user; canonical has no active matching assignment |
| CANONICAL_ONLY | Canonical has candidate(s); legacy returns None (or empty) |
| DIFFERENT_USER | Both resolve; different user ids |
| DIFFERENT_ROLE | Role code mismatch for resolved actors |
| AMBIGUOUS | ADMIN / multi-candidate / ambiguous mapping surfaced explicitly |
| INACTIVE_ASSIGNMENT | Expected canonical code exists only inactive |
| CROSS_TENANT_ANOMALY | Canonical or comparison path would cross org boundary |
| RESOLUTION_ERROR | Canonical side throws / times out |

---

## Resolver coverage

| Area | Required tests |
|---|---|
| A1 `resolve_assignee` | specific_assignee short-circuit; role match; None; flag on/off identity |
| A2 `resolve_rule_assignee` | specific_approver; role match; None; flag on/off identity |
| Delegation fields | Comparison of delegated vs assigned if in scope of report (not changing gates) |
| Report command | org filter; resolver-type filter; JSON; exit non-zero on CROSS_TENANT_ANOMALY / critical |
| Audit | `role.resolver.parity_checked` / `drift_detected` / `security_anomaly` / `comparison_failed` |

---

## Regression suites (must remain green)

| Suite | Why |
|---|---|
| `tests.test_par_id_001_shadow_sync` | Slice 3 unchanged |
| `tests.test_par_id_001_role_definition` | Catalogue |
| `tests.test_par_id_001_process_role_assignment` | Dual-read diagnostics |
| `tests.test_par_id_001_characterization` | Baseline behaviour |
| `tests.test_cross_tenant_isolation` | Tenant safety |
| Approval authorization / workflow / PAR-APR-001 | No authz outcome change |
| `tests.test_par_wf_010_characterization` | Workflow isolation |
| Governance authority script | Docs integrity |

---

## Explicit non-goals for tests

- Do not assert that canonical becomes preferred.
- Do not assert flagship drafting (B2) starts using `approver_role`.
- Do not enable the flag in default test settings.
