# PAR-ID-001 — Staging resolver-parity results

**Programme:** PAR-ID-001  
**Gate:** Resolver-parity staging (diagnostic only)  
**Date:** 2026-07-22  
**PR #58 merge SHA:** `598b7a128cb8d0f5be0c7cd2fb1880f631ca9608` (merged 2026-07-22T14:42:13Z)  
**Environment:** Staging-equivalent local SQLite (`config.settings_development`) with controlled-pilot seed data — not a separate hosted staging cluster  
**Authority:** Legacy resolvers remain authoritative. Canonical results are **not** returned to callers.

---

## Staging activation

| Flag | Staging value | Production / default |
|---|---|---|
| `PROCESS_ROLE_SHADOW_WRITE_ENABLED` | `true` | `false` |
| `PROCESS_ROLE_PARITY_REPORTING_ENABLED` | `true` | `false` |
| `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` | `true` | `false` |

**Canonical authority / dual-return:** **not enabled**  
**Activation method:** local `.env` only (gitignored); no settings-default change  
**Staging period:** 2026-07-22 (single controlled exercise window after PR #58 merge)  
**Organizations covered:** `controlled-pilot-org` (id=1), `controlled-pilot-org-b` (id=2; multi-org companion)

---

## Commands run

```text
python manage.py process_role_resolver_parity_report --json --require-flag
python manage.py process_role_resolver_parity_report --organization-id=1 --json --require-flag
python manage.py process_role_resolver_parity_report --organization-id=2 --json --require-flag
```

Per-resolver-type CLI filters are **not** supported by the report command; breakdown below is from the same exercise paths (`resolve_assignee` / `resolve_rule_assignee`).

---

## Parity counts (all organizations)

Source: `process_role_resolver_parity_report --json --require-flag`

| Metric | Count |
|---|---|
| total_comparisons | 37 |
| MATCH | 9 |
| LEGACY_ONLY | 1 |
| CANONICAL_ONLY | 0 |
| DIFFERENT_USER | 0 |
| DIFFERENT_ROLE | 0 |
| AMBIGUOUS | 13 |
| INACTIVE_ASSIGNMENT | 14 |
| CROSS_TENANT_ANOMALY | 0 |
| RESOLUTION_ERROR | 0 |
| critical_drift_count | 0 |

`authoritative_for_runtime`: **false**

### Per organization

| Organization | total | MATCH | AMBIGUOUS | INACTIVE | LEGACY_ONLY | critical |
|---|---|---|---|---|---|---|
| controlled-pilot-org (1) | 36 | 9 | 13 | 14 | 0 | 0 |
| controlled-pilot-org-b (2) | 1 | 0 | 0 | 0 | 1 | 0 |

### By resolver type (all-org exercise)

| Classification | resolve_rule_assignee | resolve_assignee |
|---|---|---|
| MATCH | 6 | 3 |
| AMBIGUOUS | 12 | 1 |
| INACTIVE_ASSIGNMENT | 12 | 2 |
| LEGACY_ONLY | 0 | 1 |

### Controlled-pilot in-process exercise (pre-report)

Separate scenario harness (26 comparisons): MATCH 15 / LEGACY_ONLY 1 / AMBIGUOUS 8 / INACTIVE 2 / critical 0. Counts differ from the management-command sweep because the harness exercises selected scenarios once; the report sweeps contracts × rules × steps.

---

## Scenarios exercised

| Scenario | Result (diagnostic) |
|---|---|
| DPA workflow launch | Exercised via template step `resolve_assignee` (materialize path uses existing workflow object; assignee resolution covered) |
| MSA workflow launch | Same |
| NDA workflow launch | Same |
| Generic workflow launch | Same |
| Approval initiation | `resolve_rule_assignee` across pilot contracts |
| Legal reviewer resolution | Role label → mapped process code path |
| Finance reviewer resolution | Role label → mapped process code path |
| Privacy reviewer resolution | Role label → mapped process code path |
| Delegation | Covered (assignee/delegate path; parity beside legacy) |
| Reassignment | Covered |
| Unresolved assignee | Covered (both unresolved → MATCH) |
| Inactive assignment | Covered → `INACTIVE_ASSIGNMENT` |
| Ambiguous ADMIN | Covered → `AMBIGUOUS` |
| Multi-organization users | Companion org `controlled-pilot-org-b` → `LEGACY_ONLY` |

No contract titles, clause text, or user identities are recorded in this evidence.

---

## Diagnostic leakage check

Audit `changes` keys observed on `role.resolver.*` events:

`organization_id`, `resolver_type`, `classification`, `correlation_id`, `legacy_result_present`, `canonical_result_present`, `criticality`, `timestamp`, `authoritative_for_runtime`

**No** restricted user identities, role dumps, credentials, or contract content in diagnostic payloads.

---

## Rollback test

| Check | Result |
|---|---|
| Flag on → comparisons increment | PASS |
| Flag off → comparisons stay 0 | PASS |
| Same legacy assignee returned with flag on vs off | PASS |
| Legacy resolver retained in code paths | PASS (always returns legacy) |

---

## Triage of every non-MATCH class

### AMBIGUOUS (13) — ambiguous historical role (expected)

- **Cause:** `UserProfile.Role.ADMIN` / step-rule label `ADMIN` maps to `legacy_process_admin` with confidence `AMBIGUOUS` (never workspace ADMIN).
- **Classification:** expected legacy limitation / ambiguous historical role (per PROCESS_ROLE_MAPPING_MATRIX).
- **Cutover gate:** must be **explicitly accepted or excluded** by Product + Security before cutover readiness. **Not yet formally accepted for cutover.**
- **Remediation in this gate:** none (diagnostic behaviour correct; no auto-repair).

### INACTIVE_ASSIGNMENT (14) — inactive assignment / seed gap

- **Cause:** Legacy resolves process roles (notably `ASSOCIATE` → `legal_reviewer`) while only an **inactive** `ProcessRoleAssignment` exists for that code in the pilot org; active shadow rows concentrate on `legacy_process_admin` / `paralegal_reviewer`.
- **Classification:** inactive assignment + seed/test-data gap (missing **active** canonical assignment). Not a CROSS_TENANT or DIFFERENT_USER defect.
- **Cutover gate:** unresolved until active canonical coverage matches legacy-resolvable roles for pilot flows, or items are explicitly accepted as out-of-scope exclusions.
- **Remediation in this gate:** **no automatic repair** of staging assignments (authorized constraint). No resolver-parity code defect found.

### LEGACY_ONLY (1) — missing canonical assignment

- **Cause:** Companion org `controlled-pilot-org-b` has a step assignee with legacy hit and **zero** `ProcessRoleAssignment` rows (active or inactive).
- **Classification:** missing canonical assignment / multi-org seed gap.
- **Cutover gate:** unresolved LEGACY_ONLY count must be 0 (or explicitly excluded).
- **Remediation in this gate:** no auto-repair; no diagnostic defect.

### CANONICAL_ONLY / DIFFERENT_USER / DIFFERENT_ROLE / RESOLUTION_ERROR / CROSS_TENANT_ANOMALY

| Class | Count | Notes |
|---|---|---|
| CANONICAL_ONLY | 0 | — |
| DIFFERENT_USER | 0 | — |
| DIFFERENT_ROLE | 0 | — |
| RESOLUTION_ERROR | 0 | — |
| CROSS_TENANT_ANOMALY | 0 | No security escalation triggered |

---

## Security findings

| Finding | Status |
|---|---|
| CROSS_TENANT_ANOMALY | **None** (count 0) |
| Sensitive diagnostic leakage | **None** observed |
| Threat review (formal dual-return / cutover threat model) | **Not complete** for cutover authorization |
| Security escalation | **Not required** this window |

---

## Remediation performed

- **Code / diagnostic defects fixed:** none identified within authorized diagnostic scope.
- **Assignment repair:** none (explicitly forbidden for this gate).
- **Docs:** this evidence package + roadmap/index updates only.

---

## Cutover-readiness checklist

| Requirement | Status |
|---|---|
| CROSS_TENANT_ANOMALY = 0 | Met |
| DIFFERENT_USER = 0 | Met |
| unexplained RESOLUTION_ERROR = 0 | Met |
| unresolved CANONICAL_ONLY = 0 | Met |
| unresolved LEGACY_ONLY = 0 | **Not met** (1) |
| AMBIGUOUS ADMIN explicitly accepted or excluded | **Not met** |
| Controlled-pilot flows pass (diagnostic) | Exercised; legacy paths OK |
| No sensitive diagnostic leakage | Met |
| Threat review complete | **Not met** |
| Rollback tested | Met (flag off) |
| Legacy resolver retained | Met |

### Verdict

**NOT READY, REMEDIATION REQUIRED**

Do **not** authorize or implement canonical cutover.  
Do **not** create dual-return / privilege cutover votes in this package.

`CANONICAL_RESOLVER_CUTOVER_AUTHORIZATION.md` is **withheld** until thresholds above are satisfied.

---

## Exact next authorization required

After remediating unresolved `LEGACY_ONLY` / active-assignment gaps for pilot roles, and after Product + Security **explicitly accept or exclude** AMBIGUOUS ADMIN for the pilot scope, plus formal threat review:

1. Separate decision package: `CANONICAL_RESOLVER_CUTOVER_AUTHORIZATION.md`
2. Separate **default-off authority flag** (not the diagnostic `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` flag)
3. Named Product, Engineering, and Security votes (do not invent)
4. Exact resolver paths, rollout order, rollback, monitoring, pilot verification

**PAR-ID-001 remains In progress.**  
Stop before canonical output influences production decisions.
