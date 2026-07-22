# PAR-ID-001 remediation decision package — review motion and votes (PR #63)

**PR:** [#63](https://github.com/Technivian/CLMOne/pull/63)  
**Baseline `main`:** `8316a756`  
**Package path:** `docs/audits/evidence/2026-07-22-par-id-001-remediation-decision/`  
**Review timestamp:** 2026-07-22T15:56:14Z  
**CI on package HEAD:** 6/6 SUCCESS (at review)  
**Package type:** Policy and planning only — **no** production code, seed, assignment, flag, or authority changes in this PR

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
| Haroon Wahed | @haroonwahed | Product | **Requested** | Pending real ISO-8601 UTC timestamp |
| Technivian | @Technivian | Engineering | **Requested** | Pending real ISO-8601 UTC timestamp |
| Security & privacy (advisory) | @Technivian | Security | **Requested (advisory, with binding conditions)** | Pending real ISO-8601 UTC timestamp + conditions acknowledged |

**Package vote status:** **Not authorized** until all three votes are recorded verbatim.

---

## Approved ADMIN policy (when votes recorded)

**P1 labels + P3 authority:**

1. Retain `legacy_process_admin` as an **AMBIGUOUS** diagnostic label.  
2. Do **not** automatically grant process authority from workspace ADMIN or from profile ADMIN.  
3. Require **explicit CERTAIN** process-role assignments for any process coverage.  
4. **P2 rejected** — no automatic ADMIN-to-process-role mapping.

---

## Binding Security conditions (must be acknowledged in Security vote)

1. Never merge workspace ADMIN with process ADMIN.  
2. No automatic privilege grant via `legacy_process_admin`.  
3. AMBIGUOUS retained in diagnostics until explicit CERTAIN assignment.  
4. Threat review T1–T10 acknowledged; residual legacy ADMIN first-match (T5) accepted only until separate cutover authorization.  
5. No staging activation, dual-return, privilege cutover, or auto-repair by this package vote.  
6. R0 (if later authorized) must remain inventory-only: no assignment repair, no flag enablement, no resolver-authority change.

---

## Explicit vote blocks (paste verbatim; do not invent)

### Product — @haroonwahed

```text
PAR-ID-001 REMEDIATION DECISION PACKAGE (PR #63) — 2026-07-22
Baseline main: 8316a756

@haroonwahed Product: Approve | Reject
Timestamp: <actual ISO-8601 UTC>

Approved:
- P1 labels + P3 authority
- P2 rejected
- Threat model + remediation architecture (planning)
- Separate R0 authorization required before data remediation

Confirms:
- 14/1/13 remain unverified until R0
- No staging activation
- No cutover / flag enablement / auto-repair
- PAR-ID-001 remains In progress
```

### Engineering — @Technivian

```text
@Technivian Engineering: Approve | Reject
Timestamp: <actual ISO-8601 UTC>

Engineering confirms:
- Package is docs/policy only
- R0–R5 each need separate implementation authorization
- R0 is inventory-only when authorized
- P2 will not be implemented
```

### Security advisory — @Technivian

```text
@Technivian Security advisory: Approve with conditions | Reject
Timestamp: <actual ISO-8601 UTC>

Binding conditions 1–6 acknowledged: yes | no
P1+P3 / P2 rejected acknowledged: yes | no
No staging activation by this vote: yes | no
```

---

## R0 authorization status

**Not authorized.** See [`R0_INVENTORY_IMPLEMENTATION_AUTHORIZATION.md`](R0_INVENTORY_IMPLEMENTATION_AUTHORIZATION.md) — status **Requested**; blocked until this policy package is Approved **and** separate R0 votes are recorded.

---

## Next implementation gate

1. Record Product + Engineering + Security votes on **this policy package**.  
2. Open/record separate **R0** implementation authorization votes.  
3. Execute R0 only as inventory (migrations in clean staging-equivalent env; verified counts).  
4. Update this decision package with verified inventory.  
5. Only then consider R1+ remediation implementation authorization.  
6. Staging activation remains a later, separate gate.
