# PAR-ID-001 evidence index

**Programme ID:** PAR-ID-001  
**Status:** **In progress** — discovery complete; ADR-0014 awaiting ratification  
**ADR:** ADR-0014 **Proposed**  
**Branch:** `cursor/feat-par-apr-001-foundation-governance`

---

## Governance

| Artifact | Purpose |
|---|---|
| [`../../../governance/decisions/adr/0014-role-definition-reconciliation.md`](../../../governance/decisions/adr/0014-role-definition-reconciliation.md) | Proposed ADR |
| [`../../../governance/decisions/adr/0014-governance-decision-package-2026-07-22.md`](../../../governance/decisions/adr/0014-governance-decision-package-2026-07-22.md) | Decision-ready package (not ratified) |
| [`../../../product/CANONICAL_DOMAIN_MODEL.md`](../../../product/CANONICAL_DOMAIN_MODEL.md) §2.5 | Canonical Role Definition |
| [`../../../architecture/SECURITY_PRIVACY_ACCESS_AND_AUDIT.md`](../../../architecture/SECURITY_PRIVACY_ACCESS_AND_AUDIT.md) | Authz / least privilege |

---

## Discovery evidence

| Artifact | Purpose |
|---|---|
| [`SUMMARY.md`](SUMMARY.md) | Programme summary |
| [`CURRENT_ROLE_MATRIX.md`](CURRENT_ROLE_MATRIX.md) | Dual-role overview (initial) |
| [`ROLE_USAGE_MATRIX.md`](ROLE_USAGE_MATRIX.md) | Full role-like concept inventory |
| [`TARGET_ROLE_MODEL.md`](TARGET_ROLE_MODEL.md) | Five-concept target model |
| [`CUTOVER_PLAN.md`](CUTOVER_PLAN.md) | Migration plan (not authorized) |
| [`CHARACTERIZATION_TESTS.md`](CHARACTERIZATION_TESTS.md) | Test inventory |

---

## Test proof

| Artifact | Purpose |
|---|---|
| [`TEST_RESULTS.md`](TEST_RESULTS.md) | Characterization + isolation results |
| [`django-tests.txt`](django-tests.txt) | PAR-ID characterization test run |

---

## Scope boundary

- **Complete:** Discovery, terminology, target model, cutover plan, decision package, characterization tests
- **Blocked:** Schema migrations, backfill, resolver cutover, privilege changes
- **Requires:** ADR-0014 Acceptance + implementation authorization + PAR-SEC-003 disposition
