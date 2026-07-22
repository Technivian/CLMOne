# PAR-ID-001 — R5 execution readiness (preparation)

**Status:** Readiness package prepared — **R5 remains Blocked**  
**Authorization:** [`CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md`](CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md) (Draft / Authorization requested)  
**R4 prerequisite:** PASS — [`../2026-07-22-par-id-001-r4-staging/R4_EXIT_REPORT.md`](../2026-07-22-par-id-001-r4-staging/R4_EXIT_REPORT.md)

---

## Readiness checklist (pre-vote / pre-execution)

| Gate | Ready? | Notes |
|---|---|---|
| R4 PASS verified | Yes | [`R4_EVIDENCE_VERIFICATION.md`](R4_EVIDENCE_VERIFICATION.md) |
| Authority transition defined | Yes | [`AUTHORITY_TRANSITION.md`](AUTHORITY_TRANSITION.md) |
| Abort conditions defined | Yes | Authorization § Immediate abort conditions |
| Rollback procedure defined | Yes | Flag-based; non-destructive |
| Evidence locations created | Yes | This directory + `pending/` |
| Motions 1–4 drafted | Yes | Votes **Requested** (not carried) |
| Operator identities filled | No | **PENDING** |
| Reviewed deployment HEAD for execution | No | **PENDING** at vote time |
| Staging-equivalent env recreate run for R5 | No | **PENDING** — do not run as part of prep claim |
| Votes carried | No | **Blocked** |
| Canonical flag enabled | No | Must remain false |

---

## Proposed recreate (do not execute under this prep claim)

```bash
# PROPOSED ONLY — not executed by the preparation package
export DJANGO_SETTINGS_MODULE=config.settings_development
export DATABASE_URL="sqlite:///$(pwd)/docs/audits/evidence/2026-07-22-par-id-001-r5-canonical-authority-cutover/staging_env/db.sqlite3"
export PROCESS_ROLE_SHADOW_WRITE_ENABLED=false
export PROCESS_ROLE_PARITY_REPORTING_ENABLED=false
export PROCESS_ROLE_RESOLVER_PARITY_ENABLED=false
export PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED=false
export PROCESS_ROLE_CANONICAL_RESOLVER_ORG_ALLOWLIST=
# migrate + seed_* + process_role_r1_certain_remediation --apply
# then await carried votes before any CANONICAL=true
```

---

## Required tests before any future execution (commands)

```bash
make check
make test-fast APP=tests.test_par_id_001_canonical_resolver_authority
make test-fast APP=tests.test_par_id_001_resolver_parity
make test-fast APP=tests.test_par_id_001_shadow_sync
make test-fast APP=tests.test_par_id_001_r1_certain_remediation
make test-fast APP=tests.test_par_id_001_process_role_assignment
make test-fast APP=tests.test_par_id_001_characterization
make test-fast APP=tests.test_par_id_001_role_definition
bash scripts/check_governance_authority.sh
```

Outcomes of a future authorized run must be captured under `pending/` — not invented here.

---

## Explicit non-readiness for execution

This package is **not** execution-ready until Motions 1–4 are carried and PENDING gates above are closed with real evidence.
