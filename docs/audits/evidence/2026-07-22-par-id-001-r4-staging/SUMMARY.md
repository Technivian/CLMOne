# PAR-ID-001 R4 — summary

**Verdict:** **PASS**  
**Environment:** `par-id-001-r4-staging-equivalent`  
**Activation:** `2026-07-22T19:44:04Z`  
**Approvals:** Product `19:41:15Z` / Engineering `19:41:16Z` / Security `19:41:17Z`  
**Evidence review:** Product `19:49:25Z` / Engineering `19:49:26Z` / Security `19:49:27Z`

## Gate map

| Gate | Status |
|---|---|
| R0 | Completed |
| R1 | Completed |
| R2 | Not required on verified corpus |
| R3 | Deferred (explicit CERTAIN only; AMBIGUOUS ADMIN hold) |
| R4 | **Completed (PASS)** |
| R5 | **Blocked** — draft/requested [`../2026-07-22-par-id-001-r5-canonical-authority-cutover/`](../2026-07-22-par-id-001-r5-canonical-authority-cutover/) |

## Headline counts

| Resolver | Count |
|---|---:|
| MATCH | 89 |
| AMBIGUOUS | 5 |
| LEGACY_ONLY | 0 |
| CANONICAL_ONLY | 0 |
| DIFFERENT_USER | 0 |
| CROSS_TENANT_ANOMALY | 0 |

| Assignment | Count |
|---|---:|
| CERTAIN created / MATCH_ACTIVE | 12 |
| CERTAIN missing | 0 |
| AMBIGUOUS ADMIN | 8 |

Committed `PROCESS_ROLE_*` defaults remain **false**. Legacy remains authoritative. R5 authorization and execution-readiness package prepared under `…-par-id-001-r5-canonical-authority-cutover/`; R5 remains **Blocked** until Motions 1–4 are carried.
