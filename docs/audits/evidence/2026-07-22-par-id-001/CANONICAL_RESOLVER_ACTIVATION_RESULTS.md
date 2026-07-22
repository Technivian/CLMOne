# PAR-ID-001 — Controlled-pilot canonical resolver activation results

**Programme:** PAR-ID-001  
**Activation authorization:** [`CANONICAL_RESOLVER_ACTIVATION_AUTHORIZATION.md`](CANONICAL_RESOLVER_ACTIVATION_AUTHORIZATION.md) — **Authorized**  
**Environment:** Staging-equivalent local SQLite (`config.settings_development`)  
**Activation timestamp:** `2026-07-22T18:03:45.588554+00:00`  
**Organization allowlist:** `controlled-pilot-org` only  
**PR #62 merge:** `4c08fb9c98e934ece9b1ed00ae788055cccae6f0`

---

## Configuration during observation

| Flag | Value |
|---|---|
| `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED` | `true` |
| `PROCESS_ROLE_CANONICAL_RESOLVER_ORG_ALLOWLIST` | `controlled-pilot-org` |
| `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` | `true` |
| `PROCESS_ROLE_SHADOW_WRITE_ENABLED` | `true` |
| `PROCESS_ROLE_PARITY_REPORTING_ENABLED` | `true` |

Legacy fallback remained active. `controlled-pilot-org-b` was **not** allowlisted.

---

## Event counts (observation window)

| Metric | Count |
|---|---:|
| canonical-used | 8 |
| legacy-fallback | 4 |
| excluded-role | 2 |
| canonical-failure | **0** |
| cross-tenant-anomaly | 2 (controlled fail-closed exercises only) |
| parity_compared (diagnostic) | 16 |

---

## Scenarios exercised

| Scenario | Result |
|---|---|
| DPA / MSA / NDA / generic workflow launch | PASS |
| Approval initiation | PASS |
| Legal / finance / privacy reviewer resolution | PASS |
| Delegation / reassignment | PASS (resolver paths) |
| Excluded ADMIN | PASS (legacy) |
| Inactive assignment | PASS (legacy fallback) |
| Unresolved assignment | PASS |
| Multi-organization users (org-b not allowlisted) | PASS |
| Cross-tenant attempt | PASS — fail closed (`None`); expected security control |
| Assignee correctness (ASSOCIATE ↔ active `legal_reviewer`) | PASS |

---

## Incidents and security

| Class | Result |
|---|---|
| User-visible incidents | **none** |
| Privilege expansion | **none** |
| Audit hygiene leak | **none** |
| Security findings | Controlled cross-tenant fail-closed — **expected pass** (not a production leak) |
| Unexplained canonical failure | **none** |
| Incorrect assignee | **none** |
| Pilot workflow regression | **none** |

**Stop triggers fired:** none.

**Activation verdict:** **PASS**

---

## Rollback exercise

| Check | Result |
|---|---|
| Set `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED=false` | Done |
| Immediate legacy resolution | **PASS** |
| Assignments intact (no destroy) | **PASS** |
| No manual DB repair required | **PASS** |

Committed / default configuration remains **off** after rollback proof. Staging-equivalent `.env` restored to flag off + empty allowlist (gitignored).

---

## Closure linkage

Activation + rollback PASS → PAR-ID-001 **Closed** (see [`CLOSURE.md`](CLOSURE.md)).  
ADMIN reconciliation residual: **PAR-ID-002**.  
Legacy resolver removal remains separately governed (not authorized).
