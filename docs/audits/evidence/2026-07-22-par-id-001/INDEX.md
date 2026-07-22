# PAR-ID-001 evidence index

**Programme ID:** PAR-ID-001  
**Status:** **In progress** — resolver parity merged (`598b7a12`); staging remediation complete; cutover readiness **READY FOR CUTOVER AUTHORIZATION** (authority flag **not** implemented/enabled); production authority still legacy  
**ADR:** ADR-0014 **Accepted**  
**PR #51 merge:** `21e65f09`  
**PR #53 merge:** `0bf7c9dc`  
**PR #54 merge:** `58966de7`  
**PR #52 merge:** `3c5e628b`  
**PR #55 merge:** `bb881ac2` (2026-07-22T13:35:32Z) — reviewed HEAD `432a55b1`  
**PR #57 merge (PR #52 evidence):** `2f14c034`  
**PR #59 merge (PR #55 merge evidence):** `0d9712ca`  
**PR #58 merge:** `598b7a128cb8d0f5be0c7cd2fb1880f631ca9608` (2026-07-22T14:42:13Z)  
**Baseline `main`:** `598b7a12`  
**Evidence branch:** `cursor/docs-par-id-001-staging-resolver-parity-d7f1` (PR [#60](https://github.com/Technivian/CLMOne/pull/60))

---

## Governance

| Artifact | Purpose |
|---|---|
| [`../../../governance/decisions/adr/0014-role-definition-reconciliation.md`](../../../governance/decisions/adr/0014-role-definition-reconciliation.md) | Accepted ADR |
| [`0112-implementation-authorization.md`](0112-implementation-authorization.md) | Catalogue authorization |
| [`0113-process-role-adapter-implementation-authorization.md`](0113-process-role-adapter-implementation-authorization.md) | Adapter authorization |
| [`SHADOW_ROLE_SYNC_IMPLEMENTATION_AUTHORIZATION.md`](SHADOW_ROLE_SYNC_IMPLEMENTATION_AUTHORIZATION.md) | Slice 3 implementation + merge authorization |
| [`RESOLVER_PARITY_IMPLEMENTATION_AUTHORIZATION.md`](RESOLVER_PARITY_IMPLEMENTATION_AUTHORIZATION.md) | Slice 4 resolver comparison (**Authorized**) |
| [`RESOLVER_READINESS_REMEDIATION_AUTHORIZATION.md`](RESOLVER_READINESS_REMEDIATION_AUTHORIZATION.md) | Staging assignment remediation (**Requested**) |
| [`CANONICAL_RESOLVER_CUTOVER_AUTHORIZATION.md`](CANONICAL_RESOLVER_CUTOVER_AUTHORIZATION.md) | Proposed authority flag package (**Requested**; not implemented) |
| [`../2026-07-22-par-sec-003/CLOSURE.md`](../2026-07-22-par-sec-003/CLOSURE.md) | PAR-SEC-003 Closed |

---

## Discovery + mapping

| Artifact | Purpose |
|---|---|
| [`ROLE_USAGE_MATRIX.md`](ROLE_USAGE_MATRIX.md) | Full inventory |
| [`TARGET_ROLE_MODEL.md`](TARGET_ROLE_MODEL.md) | Five-concept target |
| [`PROCESS_ROLE_MAPPING_MATRIX.md`](PROCESS_ROLE_MAPPING_MATRIX.md) | Mapping rules + first-cutover ADMIN exclusion |
| [`SHADOW_WRITE_PATH_MATRIX.md`](SHADOW_WRITE_PATH_MATRIX.md) | Legacy write → shadow eligibility |
| [`RESOLVER_USAGE_MATRIX.md`](RESOLVER_USAGE_MATRIX.md) | Runtime resolver consumer inventory |
| [`RESOLVER_PARITY_TEST_MATRIX.md`](RESOLVER_PARITY_TEST_MATRIX.md) | Slice 4 tests |
| [`CUTOVER_PLAN.md`](CUTOVER_PLAN.md) | Cutover plan (ADMIN exclusion noted; authority not authorized) |

---

## Staging + readiness

| Artifact | Purpose |
|---|---|
| [`STAGING_RESOLVER_PARITY_RESULTS.md`](STAGING_RESOLVER_PARITY_RESULTS.md) | Parity counts; post-remediation **READY FOR CUTOVER AUTHORIZATION** |
| [`INACTIVE_ASSIGNMENT_REMEDIATION.md`](INACTIVE_ASSIGNMENT_REMEDIATION.md) | CERTAIN inactive reactivation evidence |
| [`RESOLVER_CUTOVER_THREAT_REVIEW.md`](RESOLVER_CUTOVER_THREAT_REVIEW.md) | Focused threat review (PASS for packaging) |

---

## Implementation evidence

| Artifact | Purpose |
|---|---|
| [`migrate-forward.txt`](migrate-forward.txt) / rollback / reforward | 0112 proof |
| [`migrate-0113-forward.txt`](migrate-0113-forward.txt) / rollback / reforward | 0113 proof |
| [`TEST_RESULTS.md`](TEST_RESULTS.md) | Test evidence |
| [`django-tests-slice3.txt`](django-tests-slice3.txt) | Slice 3 captured run |
| [`django-tests.txt`](django-tests.txt) | Prior adapter run |
| [`../2026-07-22-pr52-merge/SUMMARY.md`](../2026-07-22-pr52-merge/SUMMARY.md) | PR #52 merge evidence |

---

## Scope boundary

- **Delivered on main:** Catalogue; org-scoped assignments; dual-read; shadow sync; resolver comparison (PR #58)
- **Staging-equivalent:** Diagnostic flags on; CERTAIN assignment gap remediation; ADMIN first-cutover exclusion recorded
- **Not delivered:** `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED`; dual-return; privilege cutover; production auto-repair
- **Production authority:** Still uses legacy resolvers
