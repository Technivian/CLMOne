# PAR-ID-001 remediation decision package — review motion and votes (PR #63)

**PR:** [#63](https://github.com/Technivian/CLMOne/pull/63)  
**Baseline `main`:** `8316a756`  
**Package path:** `docs/audits/evidence/2026-07-22-par-id-001-remediation-decision/`  
**Package-approved reviewed HEAD:** `8390769d28d4e96599072861d950dc2e4ec8b5e2`  
**Package approval recorded:** 2026-07-22T18:36:00Z  
**Package type:** Policy and planning only — **no** production code, seed, assignment, flag, or authority changes in this PR  
**Package approval ≠ merge authorization:** Package Approve votes do **not** authorize merging PR #63; see § Merge authorization (separate).

---

## Inventory limitation (binding for this review)

| Programme target | Status |
|---|---|
| 14 INACTIVE/MISSING | **Unverified** — not committed row-level inventory |
| 1 LEGACY_ONLY | **Unverified** |
| 13 AMBIGUOUS ADMIN | **Unverified** |
| Local DB migration 0113 | **Not applied** on local `db.sqlite3` |
| In-memory seed result | **Pattern evidence only** |

Verified counts require a separate **R0** implementation authorization (below). This package does **not** authorize R0.

---

## Review disposition

| Decision requested | Review finding |
|---|---|
| Approve **P1 labels + P3 authority** | **Accepted as the package motion** — retain `legacy_process_admin` as AMBIGUOUS diagnostic label; do not automatically grant process authority to workspace ADMIN; require explicit CERTAIN process-role assignments |
| Reject **P2** | **Accepted as binding exclusion** — no automatic ADMIN→CERTAIN process-role mapping |
| Approve threat model + remediation architecture | **Accepted as the package motion** — `THREAT_REVIEW.md` T1–T10 + slices R0–R5 as planning architecture |
| Separate R0 before any data remediation | **Accepted as binding gate** — R0 auth is **Requested**, not granted by package approval alone |

---

## Motion — Approve policy package (not R0, not staging)

**Text:** Approve the PAR-ID-001 remediation decision package as policy/planning only: ADMIN posture **P1+P3**; **P2 rejected**; threat review and remediation architecture accepted; programme targets 14/1/13 remain unverified until R0; **no** staging activation, flag enablement, auto-repair, privilege grant, resolver-authority change, or canonical cutover.

| Approver | GitHub identity | Capacity | Vote | Consent |
|---|---|---|---|---|
| Haroon Wahed | @haroonwahed | Product | **Approve** | `2026-07-22T18:33:34Z` — Reviewed HEAD `8390769d`; P1+P3; P2 rejected; package ≠ merge auth |
| Technivian | @Technivian | Engineering | **Approve** | `2026-07-22T18:35:34Z` |
| Security & privacy (advisory) | @Technivian | Security | **Approve with conditions** | `2026-07-22T18:34:34Z` — Conditions 1–6 acknowledged: yes |

**Package vote status:** **Approved** (policy/planning only). Does **not** authorize PR #63 merge, R0 execution, flag enablement, or cutover.

### Recorded package votes (verbatim)

```text
@haroonwahed Product: Approve
Timestamp: 2026-07-22T18:33:34Z
Reviewed HEAD: 8390769d
# P1+P3; P2 rejected; package ≠ merge auth

@Technivian Engineering: Approve
Timestamp: 2026-07-22T18:35:34Z

@Technivian Security advisory: Approve with conditions
Timestamp: 2026-07-22T18:34:34Z
Conditions 1–6 acknowledged: yes
```

---

## Approved ADMIN policy (binding)

**Exactly:**

1. **P1 labels + P3 authority**  
2. Retain `legacy_process_admin` as an **AMBIGUOUS** diagnostic label  
3. No automatic process authority for workspace ADMIN (or via profile ADMIN auto-map)  
4. Explicit **CERTAIN** process-role assignments required for process coverage  
5. **P2** automatic ADMIN→process-role mapping **rejected**

---

## Binding Security conditions (verbatim — acknowledged)

1. Never merge workspace ADMIN with process ADMIN.  
2. No automatic privilege grant via `legacy_process_admin`.  
3. AMBIGUOUS retained in diagnostics until explicit CERTAIN assignment.  
4. Threat review T1–T10 acknowledged; residual legacy ADMIN first-match (T5) accepted only until separate cutover authorization.  
5. No staging activation, dual-return, privilege cutover, or auto-repair by this package vote.  
6. R0 (if later authorized) must remain inventory-only: no assignment repair, no flag enablement, no resolver-authority change.

---

## CI state

| HEAD | Status |
|---|---|
| `8390769d` (package-approved reviewed HEAD) | All 6 required checks **SUCCESS**; merge state CLEAN |
| Tip after this vote-record commit | Must be CI-green (or content-identical) before merge |

Required checks: Forbidden-brand scan · Anti-drift + contrast · pr-release-evidence · security-scans · verify-ui · quality-and-tenancy — all SUCCESS.

---

## Merge authorization (PR #63) — separate from package approval

**Status:** **Requested** — package is Approved; CI was green on `8390769d`; awaiting Product + Engineering **Approve merge**.

Package approval does **not** authorize merge.

### Merge vote blocks

```text
PR #63 MERGE AUTHORIZATION — 2026-07-22

PR: #63
Reviewed HEAD: 8390769d
(or later content-identical / CI-green tip that includes this vote record)
Package: docs/audits/evidence/2026-07-22-par-id-001-remediation-decision/

@haroonwahed Product: Approve merge | Reject merge
Timestamp: <actual ISO-8601 UTC>

Merge authorization confirms:
- Policy package Product/Engineering/Security votes recorded Approve
- Motion remains P1+P3; P2 rejected
- Docs-only PR; no code/flag/data mutation
- Does not authorize R0 execution
- Does not authorize staging activation or cutover
```

```text
@Technivian Engineering: Approve merge | Reject merge
Timestamp: <actual ISO-8601 UTC>
```

---

## R0 authorization status

**Not authorized.** Package is **Approved**. R0 remains blocked until:

1. PR #63 **merged** under separate merge authorization, and  
2. Separate R0 votes recorded in [`R0_INVENTORY_IMPLEMENTATION_AUTHORIZATION.md`](R0_INVENTORY_IMPLEMENTATION_AUTHORIZATION.md).

R0 allow/deny unchanged: inventory-only in clean staging-equivalent env; apply 0113; deterministic setup; tenant-scoped inventory + provenance; parity rerun; replace 14/1/13; **no** repair, flags, privileges, resolver-authority change, staging activation, or cutover.

---

## Gate sequence (binding)

1. Record package votes (Product / Engineering / Security) — **done; package Approved**.  
2. Separate Product + Engineering **Approve merge** for PR #63 — **current step**.  
3. Merge PR #63 (docs-only) when CI green on merge HEAD.  
4. Open R0 inventory authorization gate only after PR #63 merged; execute only after separate R0 votes.  
5. R1+ and staging/canonical activation remain later gates.

## Next authorized action

**Await separate Product + Engineering Approve merge** votes.  
Do **not** merge without them. Do **not** open or execute R0. Do **not** enable flags.
