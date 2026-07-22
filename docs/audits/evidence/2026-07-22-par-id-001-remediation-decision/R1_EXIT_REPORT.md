# PAR-ID-001 R1 exit report — CERTAIN non-ADMIN remediation

**Authorization:** Product `2026-07-22T19:16:55Z` / Engineering `2026-07-22T19:16:56Z` / Security `2026-07-22T19:16:57Z` (conditions 1–10 yes)  
**Baseline package tip:** `03eab9a6` / R0 tip `0404e284`  
**Authorized environment:** clean staging-equivalent SQLite + R0 deterministic seed corpus (`r0_staging_env/`; DB not committed)  
**Not authorized:** production / unnamed environments; flag enablement; cutover  

Raw evidence: [`r1_dry_run.json`](r1_dry_run.json), [`r1_apply_evidence.json`](r1_apply_evidence.json)

---

## Approvals (actual UTC at recording)

| Approver | Vote | Timestamp |
|---|---|---|
| @haroonwahed Product | Approve | `2026-07-22T19:16:55Z` |
| @Technivian Engineering | Approve | `2026-07-22T19:16:56Z` |
| @Technivian Security advisory | Approve with conditions | `2026-07-22T19:16:57Z` |

Bundled: implementation + tests + PR + merge after CI (no separate merge vote).

---

## Dry-run

| Metric | Result |
|---|---|
| `to_create_count` | **12** |
| `scope_valid` | **true** |
| ADMIN / AMBIGUOUS creates planned | **0** |

---

## Apply

| Metric | Result |
|---|---|
| Created | **12** |
| Skipped | 0 |
| `legacy_process_admin` active | **0** |
| First remediation run ID | `80ec4528-60e5-410f-964a-219714361c16` |
| Rollback deactivated | **12** |
| Re-apply created | **12** (final corpus left remediated) |

---

## Before / after parity (fresh runs; flags false)

| Metric | Before | After R1 |
|---|---|---|
| CERTAIN missing | 12 | **0** |
| CERTAIN MATCH_ACTIVE | 0 | **12** |
| AMBIGUOUS ADMIN profile rows | 8 | **8** (unchanged) |
| Assignment `legacy_without_canonical` | 20 | **8** (ADMIN only) |
| Resolver LEGACY_ONLY | 89 | **0** |
| Resolver AMBIGUOUS | 5 | **5** |
| Resolver MATCH | 0 | **89** |
| CROSS_TENANT_ANOMALY | 0 | **0** |
| DIFFERENT_USER | 0 | **0** |

---

## Flags

All `PROCESS_ROLE_*` remained **false** for the entire R1 evidence run.

---

## Residual R2 scope (not authorized)

| Residual | Count | Notes |
|---|---|---|
| AMBIGUOUS ADMIN profile rows | **8** | Hold under P1+P3; no R1 writes |
| Resolver AMBIGUOUS | **5** | ADMIN path labels |
| LEGACY_ONLY (post-R1 corpus) | **0** | Cleared for CERTAIN-covered seed paths |
| Production / other envs | unknown | Require separate inventory before any apply |

**R2** (if opened later): residual LEGACY_ONLY in non-corpus envs + path coverage beyond these 12 CERTAIN creates — **not** authorized here.

---

## Rollback evidence

Rollback by run ID deactivated **12** R1 rows; MANUAL/unrelated assignments not present in corpus; re-apply restored **12**. Automated tests: `tests/test_par_id_001_r1_certain_remediation.py` (rollback + preserve existing).

---

## Exit verdict

**PASS** for authorized staging-equivalent corpus.

Next activation gate: **canonical / staging flag activation** remains separately gated (`CANONICAL_RESOLVER_ACTIVATION_AUTHORIZATION.md`). R2–R5 not authorized.
