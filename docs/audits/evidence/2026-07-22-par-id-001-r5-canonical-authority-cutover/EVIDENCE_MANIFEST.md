# PAR-ID-001 R5 — evidence manifest (preparation)

**Status:** Structure prepared; execution results **PENDING**  
**Evidence root:** `docs/audits/evidence/2026-07-22-par-id-001-r5-canonical-authority-cutover/`  
**Do not invent results.** Placeholders below must remain pending until an authorized R5 execution occurs.

---

## Required artifacts

| Artifact | Path / name | Status |
|---|---|---|
| Authorization record | `CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md` | Prepared (votes Requested) |
| Votes and timestamps | Ballot tables in authorization record | **PENDING** |
| Reviewed HEAD | Recorded in authorization + `pending/reviewed_head.txt` | **PENDING** |
| Deployed artifact identity | `pending/deployed_artifact.txt` | **PENDING** |
| Environment identity | Authorization + `pending/environment.txt` | Named proposal ready; runtime confirm **PENDING** |
| Operator identities | Authorization operator table | **PENDING** |
| Flag state before | `pending/flag_state_before.txt` | **PENDING** |
| Activation timestamp | `pending/activation_timestamp.txt` | **PENDING** |
| Parity / resolver counts | `pending/resolver_parity_during.json` | **PENDING** |
| Scenario results | `pending/scenarios_executed.json` | **PENDING** |
| Assignment results | `pending/assignment_parity_during.json` | **PENDING** |
| Tenant-isolation evidence | `pending/tenant_isolation.txt` | **PENDING** |
| Authorization / permission evidence | `pending/permission_unchanged.txt` | **PENDING** |
| Fail-open result | `pending/fail_open_probe.json` | **PENDING** |
| Monitoring output | `pending/monitoring.txt` | **PENDING** |
| Abort-condition review | `pending/abort_condition_review.md` | **PENDING** |
| Rollback or rollback-readiness | `pending/rollback_result.json` | **PENDING** |
| Final flag state | `pending/flag_state_after.txt` | **PENDING** |
| Test output | `pending/django-tests-*.txt` | **PENDING** |
| `manage.py check` output | `pending/django-check.txt` | **PENDING** |
| Security review | `pending/SECURITY_REVIEW.md` | **PENDING** |
| Final Product / Engineering review | `pending/FINAL_REVIEW.md` | **PENDING** |
| Roadmap update | `docs/roadmap/PLATFORM_ALIGNMENT_ROADMAP.md` | Prep note landed; execution update **PENDING** |
| Final go / rollback / suspension | `pending/FINAL_DECISION.md` | **PENDING** |

---

## Preparation-only artifacts (present now)

| Artifact | Status |
|---|---|
| `R4_EVIDENCE_VERIFICATION.md` | Present |
| `AUTHORITY_TRANSITION.md` | Present |
| `R5_EXECUTION_READINESS.md` | Present |
| `INDEX.md` / `SUMMARY.md` | Present |
| `pending/.gitignore` | Present (blocks sqlite DB commit) |

---

## Placeholder marker convention

Any file whose body begins with `PENDING — not executed` is non-authoritative and must not be treated as cutover evidence.
