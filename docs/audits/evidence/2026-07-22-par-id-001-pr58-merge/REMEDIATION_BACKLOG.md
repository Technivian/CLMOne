# PAR-ID-001 — post-Slice-4 remediation backlog (after PR #58 ratification)

**Status:** **Prepared — blocked on GI-2026-07-22-PR58-PREAUTH-MERGE ratification**  
**Opened:** 2026-07-22T15:19:31Z  
**Programme status:** PAR-ID-001 remains **In progress**  
**Staging activation:** **Not requested** until ratification is complete **and** this backlog’s Product/Security acceptance items for ADMIN policy are addressed

Related: [`GOVERNANCE_INCIDENT_AND_RATIFICATION_ADDENDUM.md`](GOVERNANCE_INCIDENT_AND_RATIFICATION_ADDENDUM.md)

---

## Preconditions

Do **not** start this remediation as production cutover work.  
Do **not** enable `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` / shadow / parity-reporting flags until separate staging activation authorization exists **after** ratification.

Remediation here is **diagnostic cleanup and policy acceptance**, not authority flip.

---

## Backlog items

| ID | Item | Count / scope | Owner capacity | Acceptance |
|---|---|---|---|---|
| REM-01 | Inactive or missing `ProcessRoleAssignment` rows relative to legacy profile roles | **14** inactive or missing assignments | Engineering | Triage list; no auto-repair; propose create/deactivate plan under separate write authorization if needed |
| REM-02 | Organization with persistent `LEGACY_ONLY` resolver/assignment posture | **1** organization | Engineering + Product | Org-scoped investigation; document residual or repair plan |
| REM-03 | Ambiguous ADMIN profile → `legacy_process_admin` mappings | **13** AMBIGUOUS ADMIN mappings | Engineering | Keep explicit `AMBIGUOUS`; never map to workspace ADMIN |
| REM-04 | Product acceptance of ADMIN mapping policy | Policy decision | Product | Accept retain-`legacy_process_admin` / AMBIGUOUS, or authorize alternate catalogue policy via PDR/ADR path |
| REM-05 | Security acceptance of ADMIN mapping policy | Advisory | Security | Threat/privacy review of AMBIGUOUS ADMIN handling; confirm no privilege conflation |
| REM-06 | Threat review completion for resolver-parity residual risk | Review package | Security + Engineering | Close threat items for comparison-only mode; confirm fail-open + tenant scoping |

---

## Recommended sequence (post-ratification)

1. Close GI-2026-07-22-PR58-PREAUTH-MERGE with **Ratify** (or execute **Revert** and stop).  
2. Inventory evidence for REM-01..03 (org-scoped reports; permission-safe).  
3. Product + Security decisions on REM-04 / REM-05 (ADMIN policy).  
4. Complete REM-06 threat review write-up.  
5. Only then consider a **separate** staging activation authorization request (not part of this backlog open).

---

## Explicit non-goals

- Enabling any `PROCESS_ROLE_*` flag
- Dual-return / privilege cutover
- Automatic repair of assignments
- Marking PAR-ID-001 Completed
- Changing permissions, memberships, navigation, or legacy resolver return values
