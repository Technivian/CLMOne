# PAR-ID-001 — R1 CERTAIN non-ADMIN remediation authorization

**Programme:** PAR-ID-001  
**Baseline `main`:** `0404e284`  
**Prerequisite:** R0 inventory **PASS** ([`R0_EXIT_REPORT.md`](R0_EXIT_REPORT.md))  
**Policy binding:** P1 labels + P3 authority; **P2 rejected**  
**Status:** **Authorized** (bundled implementation + merge)  
**Related:** [`R1_MAPPING_MANIFEST.md`](R1_MAPPING_MANIFEST.md), [`R1_ROW_SCOPE.md`](R1_ROW_SCOPE.md), [`R1_TEST_MATRIX_AND_ROLLBACK.md`](R1_TEST_MATRIX_AND_ROLLBACK.md)

---

## Motion — Authorize R1 CERTAIN non-ADMIN remediation only

**Text:** Authorize an idempotent, dry-run/apply remediation that creates **missing** org-scoped `ProcessRoleAssignment` rows **only** for the **12** CERTAIN non-ADMIN R0 rows (R1-MAP-01..04); records provenance including a shared remediation run ID; preserves existing valid assignments; produces before/after inventory and parity evidence; supports rollback by remediation run ID; adds required tests; and authorizes PR review + merge after CI green — **without** ADMIN/AMBIGUOUS remediation, permission/membership changes, automatic runtime repair, feature-flag enablement, canonical resolver authority, dual-return, staging activation, R2–R5, or production apply to an unnamed environment.

| Approver | Vote | Consent |
|---|---|---|
| @haroonwahed Product | **Approve** | `2026-07-22T19:16:55Z` |
| @Technivian Engineering | **Approve** | `2026-07-22T19:16:56Z` |
| @Technivian Security advisory | **Approve with conditions** | `2026-07-22T19:16:57Z` — Conditions 1–10 acknowledged: **yes** |

**R1 authorization status:** **Authorized** (bundled — implementation, tests, evidence, PR review, merge after CI green; **no** separate merge vote required).

### Recorded approvals (verbatim)

```text
@haroonwahed Product: Approve
Timestamp: 2026-07-22T19:16:55Z

@Technivian Engineering: Approve
Timestamp: 2026-07-22T19:16:56Z

@Technivian Security advisory: Approve with conditions
Timestamp: 2026-07-22T19:16:57Z
Conditions 1–10 acknowledged: yes
```

Timestamps obtained at recording via `date -u +"%Y-%m-%dT%H:%M:%SZ"` (not placeholders).

---

## Authorized scope

| Rule | Mapping | Verified rows |
|---|---|---|
| R1-MAP-01 | PARTNER → `partner_reviewer` | 2 |
| R1-MAP-02 | SENIOR_ASSOCIATE → `senior_reviewer` | 4 |
| R1-MAP-03 | ASSOCIATE → `legal_reviewer` | 3 |
| R1-MAP-04 | PARALEGAL → `paralegal_reviewer` | 3 |
| **Total** | | **12** |

R1-MAP-05 / R1-MAP-06 remain **reserved and unauthorized**.

Exact rows: [`R1_ROW_SCOPE.md`](R1_ROW_SCOPE.md).

---

## Hard exclusions

Do not: map workspace ADMIN to process role; grant authority via `legacy_process_admin`; modify the 8 AMBIGUOUS ADMIN rows; infer roles from workspace membership/permissions; enable any `PROCESS_ROLE_*` flag; change resolver authority; change privileges/permissions/memberships/navigation/approvals/signers; runtime auto-repair; authorize R2–R5; staging activation or canonical cutover; execute against production or an unnamed environment (authorized apply = clean staging-equivalent / test corpus only).

---

## Binding Security conditions (verbatim — acknowledged)

1. R1 may create assignments **only** for CERTAIN non-ADMIN mappings listed in the mapping manifest.  
2. Profile `ADMIN` / `legacy_process_admin` / AMBIGUOUS rows are **hard-excluded**; P2 remains rejected.  
3. Every write must be org-scoped; cross-tenant create/update is forbidden and must fail closed.  
4. R1 must not change `OrganizationMembership`, permissions, navigation, or authz outcomes.  
5. R1 must not enable `PROCESS_ROLE_*` flags or alter resolver return authority (legacy remains authoritative).  
6. No automatic runtime repair — apply only via explicit dry-run/apply command (or authorized one-shot service invocation).  
7. Rollback must be limited to rows tagged with the remediation run ID; must not deactivate unrelated assignments.  
8. Post-apply parity: `CROSS_TENANT_ANOMALY` must remain **0**; R1 must not introduce `DIFFERENT_USER` for remediated CERTAIN paths.  
9. Evidence must distinguish verified post-R1 counts from historical programme targets and from R0 baselines.  
10. Staging activation and canonical cutover remain separately gated.

---

## Merge rule (bundled)

After implementation: review final HEAD; verify diff within R1 scope; verify required CI green; **merge without** a separate Product/Engineering merge vote; record merge SHA, timestamp, and updated `main` HEAD.

---

## Exit criteria

Exactly 12 approved CERTAIN assignments created; no ADMIN-derived assignment; no unrelated assignment changed; CROSS_TENANT_ANOMALY 0; DIFFERENT_USER 0; rollback succeeds; flags default false; before/after evidence published; residual LEGACY_ONLY and AMBIGUOUS from fresh parity; CI green.
