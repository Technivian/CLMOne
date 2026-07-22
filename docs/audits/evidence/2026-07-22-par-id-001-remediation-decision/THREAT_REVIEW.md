# PAR-ID-001 — Threat review (REM-06) — remediation / resolver-parity residuals

**Baseline `main`:** `8316a756`  
**Status:** **Proposed — pending Security advisory acceptance**  
**Scope:** Comparison-only resolver parity (merged, flag default off) + proposed remediation postures  
**Non-scope:** Dual-return, privilege cutover, staging flag enablement

Related: [`REMEDIATION_ANALYSIS.md`](REMEDIATION_ANALYSIS.md), [`ADMIN_ROLE_MAPPING_DECISION.md`](ADMIN_ROLE_MAPPING_DECISION.md)

---

## Threat scenarios and controls

| # | Threat | Residual risk | Control / mitigation | Status |
|---|---|---|---|---|
| T1 | **Tenant isolation** — comparison or inventory leaks cross-org identities | Medium if mis-logged | Org-scoped queries; evidence fields limited to ids/codes; CROSS_TENANT_ANOMALY class; no foreign org payloads | In code for parity; must hold for R0 inventory |
| T2 | **Privilege escalation** — PRA or ADMIN map grants workspace or approval power | High if cutover premature | Flags default off; legacy return authoritative; ADMIN mapping AMBIGUOUS / non-authoritative under recommended policy | Binding |
| T3 | **Role confusion** — workspace ADMIN ≡ process ADMIN | High | Separate catalogue codes (`workspace_admin` label vs `legacy_process_admin`); dual-read collision note; never merge | Binding |
| T4 | **Inactive assignment reuse** — inactive PRA treated as live canonical actor | Medium | Classifier `INACTIVE_ASSIGNMENT`; active filter on canonical candidates; no auto-reactivate | In parity code |
| T5 | **Fallback abuse** — attackers rely on first-match legacy ADMIN profile resolution | Medium (legacy behaviour) | Document residual; no “fix” by returning canonical; future cutover needs explicit assignees | Residual accepted until cutover auth |
| T6 | **Diagnostic metadata leakage** — logs/reports expose secrets or contract content | Medium | Permission-safe evidence schema; forbid credentials/contract bodies in parity audits | In parity tests |
| T7 | **Flag misuse** — staging/prod enable without auth | High | Default false; separate activation authorization; ratification explicitly forbids staging enablement | Binding |
| T8 | **Rollback failure** — cannot undo remediation writes | Medium | Prefer deactivate system-managed PRA; flag-off kill switch; no schema dependency for parity | Plan in analysis |
| T9 | **Audit coverage gaps** — silent drift | Medium | Require inventory + parity events; REM packages recorded under evidence/ | Partial — R0 still needed |
| T10 | **Auto-repair** — parity or remediation mutates authority silently | High | Explicitly forbidden; no repair in comparison path | Binding |

---

## ADMIN-specific notes

- Recommended posture (P1 labels + P3 authority): catalogue may retain `legacy_process_admin`, but **no automatic process authority**.  
- Security must reject any implementation that promotes profile ADMIN → CERTAIN process role without Product+Security votes (rejects P2).  
- Coexistence of membership ADMIN and profile ADMIN must remain an explicit diagnostic, not a merge.

---

## Rollback (threat lens)

1. Disable all `PROCESS_ROLE_*` flags (defaults).  
2. Deactivate remediation-created system-managed PRA rows.  
3. Revert mapping-policy PRs if a harmful policy shipped.  
4. Legacy resolvers remain the production path throughout.

---

## Acceptance criteria for REM-06

- [ ] Security advisory Accepts this review (or Accepts with recorded conditions)  
- [ ] Product ADMIN option selected and consistent with this review  
- [ ] No staging activation requested in the same vote set  
- [ ] Residual T5 (legacy ADMIN first-match) explicitly accepted or scheduled for separate cutover work  

---

## Security vote block

```text
PAR-ID-001 THREAT REVIEW (REM-06) — 2026-07-22
Baseline main: 8316a756

@Technivian Security advisory: Approve with conditions | Reject
Timestamp: <actual ISO-8601 UTC>

T1–T10 acknowledged: yes | no
Residual T5 (legacy ADMIN first-match) accepted until separate cutover auth: yes | no
No staging activation / dual-return / privilege cutover by this vote: yes | no
```
