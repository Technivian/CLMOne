# PAR-ID-001 R4 exit report — staging resolver-parity diagnostic activation

**Authorization:** [`STAGING_RESOLVER_PARITY_ACTIVATION_AUTHORIZATION.md`](STAGING_RESOLVER_PARITY_ACTIVATION_AUTHORIZATION.md)  
**Approvals:** Product `2026-07-22T19:41:15Z` / Engineering `2026-07-22T19:41:16Z` / Security `2026-07-22T19:41:17Z` (conditions acknowledged: yes)  
**Baseline `main`:** `2e7b5adc`  
**Named staging environment:** `par-id-001-r4-staging-equivalent`  
**Environment path:** `staging_env/` (ephemeral SQLite; DB gitignored / not committed)  
**Activation timestamp:** `2026-07-22T19:44:04Z`  
**Rollback timestamp:** `2026-07-22T19:47:22Z` (see `rollback_timestamp.txt`)  
**Do not use** `CANONICAL_RESOLVER_ACTIVATION_AUTHORIZATION.md` for this slice.  
**R5 reserved:** [`../2026-07-22-par-id-001-r5-canonical-authority-cutover/CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md`](../2026-07-22-par-id-001-r5-canonical-authority-cutover/CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md) — **Draft / Authorization requested**; R5 remains **Blocked**

---

## Bundled approvals (recorded)

| Approver | Vote | Timestamp |
|---|---|---|
| @haroonwahed Product | Approve | `2026-07-22T19:41:15Z` |
| @Technivian Engineering | Approve | `2026-07-22T19:41:16Z` |
| @Technivian Security advisory | Approve with conditions | `2026-07-22T19:41:17Z` |

Conditions acknowledged: **yes**

---

## Evidence review (exit attestation)

| Reviewer | Disposition | Timestamp |
|---|---|---|
| @haroonwahed Product | Evidence reviewed — accept R4 PASS | `2026-07-22T19:49:25Z` |
| @Technivian Engineering | Evidence reviewed — accept R4 PASS | `2026-07-22T19:49:26Z` |
| @Technivian Security advisory | Evidence reviewed — accept R4 PASS (conditions held) | `2026-07-22T19:49:27Z` |

Timestamps via `date -u +"%Y-%m-%dT%H:%M:%SZ"`.

---

## Flag state

| Phase | SHADOW | PARITY_REPORTING | RESOLVER_PARITY | CANONICAL |
|---|---|---|---|---|
| Before | false | false | false | false |
| During (staging only) | true | true | true | false |
| After rollback | false | false | false | false |
| Committed defaults | false | false | false | n/a (not enabled) |

Sources: `flag_state_before.txt`, `flag_state_during.txt`, `flag_state_after.txt`, `committed_defaults_check.txt`.

---

## Assignment parity (during activation)

| Metric | Count |
|---|---:|
| Total rows | 20 |
| CERTAIN missing | **0** |
| CERTAIN MATCH_ACTIVE | **12** |
| AMBIGUOUS ADMIN rows | **8** |
| Critical drift rows | 8 (ambiguous ADMIN only; non-authoritative) |
| `authoritative_for_runtime` | false |

Source: `scenarios_executed.json` / `assignment_parity_during.json`.

---

## Resolver parity (authoritative during activation)

| Metric | Count |
|---|---:|
| total_comparisons | **94** |
| MATCH | **89** |
| AMBIGUOUS | **5** |
| LEGACY_ONLY | **0** |
| CANONICAL_ONLY | **0** |
| DIFFERENT_USER | **0** |
| DIFFERENT_ROLE | **0** |
| INACTIVE_ASSIGNMENT | **0** |
| CROSS_TENANT_ANOMALY | **0** |
| RESOLUTION_ERROR | **0** |
| critical_drift_count | **0** |
| `authoritative_for_runtime` | **false** |

Source: `resolver_parity_during.json` (reconfirmed in `scenarios_executed.json` → `resolver_parity_authoritative_report`).

AMBIGUOUS ADMIN remains explicit and non-authoritative (known residual under P1+P3; P2 rejected).

---

## Scenarios executed

| Scenario | Result |
|---|---|
| NDA launch and assignment | EXERCISED |
| MSA launch and assignment | EXERCISED |
| DPA launch and privacy routing | EXERCISED |
| generic workflow | EXERCISED |
| approval initiation | EXERCISED |
| legal reviewer resolution | EXERCISED |
| finance approver resolution | EXERCISED |
| privacy reviewer resolution | EXERCISED |
| signer resolution where applicable | EXERCISED |
| delegation | EXERCISED |
| reassignment | EXERCISED |
| inactive assignment | EXERCISED (probe: INACTIVE_ASSIGNMENT incremented; legacy returned) |
| unresolved assignment | EXERCISED |
| ADMIN ambiguity | EXERCISED (non-authoritative) |
| two-tenant isolation | EXERCISED (`pra_without_active_membership=0`) |
| comparison error and fail-open | EXERCISED (legacy returned unchanged; RESOLUTION_ERROR recorded) |

Source: `scenarios_executed.json`.

---

## Security findings

- `CROSS_TENANT_ANOMALY` = 0  
- `DIFFERENT_USER` = 0  
- unexpected `LEGACY_ONLY` = 0  
- unexpected `CANONICAL_ONLY` = 0  
- AMBIGUOUS ADMIN explicit and non-authoritative  
- No workspace ADMIN → process authority  
- Canonical output not returned to callers  
- No restricted diagnostic leakage (evidence keys: org id, resolver type, classification, correlation, presence flags, criticality, timestamp, `authoritative_for_runtime=false`)  
- Fail-open: comparison errors do not change runtime output  
- Committed `PROCESS_ROLE_*` defaults remain false  
- No production activation  

---

## Rollback evidence

| Check | Result |
|---|---|
| Method | Flag-off (immediate) |
| `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` after | false |
| `--require-flag` exit | 2 |
| Comparisons with flag off | **0** |
| Legacy remains authoritative | **yes** |
| Verdict | **PASS** |

Source: `rollback_result.json`, `flag_state_after.txt`.

---

## Tests / checks

| Suite | Result |
|---|---|
| `tests.test_par_id_001_resolver_parity` | 18 OK |
| `tests.test_par_id_001_shadow_sync` | 10 OK |
| `tests.test_par_id_001_r1_certain_remediation` | 10 OK |
| `tests.test_par_id_001_process_role_assignment` | 17 OK |
| `tests.test_par_id_001_characterization` | 19 OK |
| `tests.test_par_id_001_role_definition` | 17 OK |
| `manage.py check` | no issues |

---

## R4 exit criteria

| Criterion | Status |
|---|---|
| CROSS_TENANT_ANOMALY = 0 | **Met** |
| DIFFERENT_USER = 0 | **Met** |
| unexpected LEGACY_ONLY = 0 | **Met** |
| unexpected CANONICAL_ONLY = 0 | **Met** |
| known ADMIN ambiguity identified and non-authoritative | **Met** |
| comparison errors do not change runtime output | **Met** |
| rollback by flag-off passes | **Met** |
| legacy remains authoritative | **Met** |
| no restricted diagnostic leakage | **Met** |
| committed defaults remain false | **Met** |
| tests and CI green | **Met** (targeted PAR-ID-001 suites + check) |
| evidence reviewed by Product, Engineering, Security | **Met** |

### Verdict

**PASS**

R5 canonical authority cutover remains **Blocked** / **not authorized**. Draft package: [`../2026-07-22-par-id-001-r5-canonical-authority-cutover/CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md`](../2026-07-22-par-id-001-r5-canonical-authority-cutover/CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md).

PAR-ID-001 remains **In progress**.
