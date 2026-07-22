# Governance incident / ratification addendum — PR #58 pre-authorization merge

**Programme:** PAR-ID-001  
**PR:** [#58](https://github.com/Technivian/CLMOne/pull/58)  
**Merge commit:** `598b7a128cb8d0f5be0c7cd2fb1880f631ca9608`  
**Incident ID:** `GI-2026-07-22-PR58-PREAUTH-MERGE`  
**Opened:** 2026-07-22T15:19:31Z  
**Status:** **Open — awaiting retrospective decision** (Ratify merge | Revert merge)  
**Responsible owner:** Product governance (@haroonwahed) with Engineering co-owner (@Technivian)  
**PAR-ID-001 programme status:** remains **In progress** (not Completed)

Related:
- [`SUMMARY.md`](SUMMARY.md)
- [`../2026-07-22-par-id-001/RESOLVER_PARITY_IMPLEMENTATION_AUTHORIZATION.md`](../2026-07-22-par-id-001/RESOLVER_PARITY_IMPLEMENTATION_AUTHORIZATION.md)
- [`REMEDIATION_BACKLOG.md`](REMEDIATION_BACKLOG.md) (prepared for after ratification; not a staging activation request)

---

## 1. Finding

PR #58 was **merged to `main` before** formal Product and Engineering **Approve merge** votes were recorded with the authoritative ISO-8601 UTC timestamps.

This is a **process/governance discrepancy**, not a runtime authority change. Implementation authorization for the comparison slice existed earlier; **merge authorization** was recorded after the merge commit.

---

## 2. Exact timeline (timestamps unchanged)

| Event | Timestamp (UTC) | SHA / note |
|---|---|---|
| Review package locked | `2026-07-22T14:09:08Z` | authorization package |
| Security advisory Approve with conditions | `2026-07-22T14:15:31Z` | implementation auth |
| Product Approve (implementation) | `2026-07-22T14:17:31Z` | implementation auth |
| Engineering Approve (implementation) | `2026-07-22T14:18:31Z` | implementation auth |
| Draft docs note claiming merge+staging auth | `2026-07-22T14:34:37Z` | later **superseded**; staging enablement **not** in force |
| Reviewed code HEAD (CI green) | — | `44926da9` |
| Docs-only tip before merge | — | `f7b56ab5` (`config/`/`contracts/`/`tests/` identical to `44926da9`) |
| **PR #58 merged to `main`** | **`2026-07-22T14:42:13Z`** | **`598b7a12`** |
| Product Approve merge (recorded) | `2026-07-22T15:06:30Z` | **after** merge |
| Engineering Approve merge (recorded) | `2026-07-22T15:06:45Z` | **after** merge |
| This addendum opened | `2026-07-22T15:19:31Z` | retrospective decision requested |

**Gap:** ~24 minutes between merge (`14:42:13Z`) and Product merge vote (`15:06:30Z`); ~24.5 minutes to Engineering merge vote (`15:06:45Z`).

---

## 3. Scope of merged code

Merged under PR #58 (non-authoritative Slice 4):

| Area | Change |
|---|---|
| Settings | `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` default **false** |
| Service | `contracts/services/process_role_resolver_parity.py` — compare beside legacy; always return legacy; fail-open |
| Hooks | `WorkflowTemplateStep.resolve_assignee`; `workflow_routing.resolve_rule_assignee` |
| Report | `process_role_resolver_parity_report` management command |
| Tests / evidence | `tests/test_par_id_001_resolver_parity.py` + docs under `docs/audits/evidence/2026-07-22-par-id-001/` |

**Not in scope of the merge:** dual-return, privilege/permission/membership/navigation changes, automatic repair, staging flag enablement, resolver cutover.

---

## 4. Technical impact

| Dimension | Impact |
|---|---|
| Runtime resolver return values | **Unchanged** when flag is off (default) |
| Permissions / privileges | **None** |
| Membership authority | **None** |
| Navigation | **None** |
| Schema / migrations | **None** |
| Default flag state on `main` | All `PROCESS_ROLE_*` flags **false** (verified post-merge) |
| Canonical path | Diagnostic only; never returned to callers under authorized design |

---

## 5. Why runtime authority remained unchanged

1. `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` defaults to **false** in `config/settings_base.py`.
2. Comparison runs only when the flag is on; otherwise resolvers return the pre-computed legacy result without side effects beyond a no-op path.
3. When the flag is on (not enabled on `main`), the wrapper still **always returns the legacy user** and fails open on comparison errors.
4. No code path in the merge alters `authorize_approval_actor`, workspace membership roles, or navigation gates.

---

## 6. Safeguards confirmed (post-merge)

| Safeguard | Status |
|---|---|
| Flag default off | **Confirmed** |
| Legacy output authoritative | **Confirmed** |
| Canonical diagnostic only | **Confirmed** |
| Fail-open comparison errors | **Confirmed** (design + tests) |
| CI green at reviewed HEAD | **Confirmed** (6/6) |
| Post-merge tests green | **Confirmed** (37 PASS resolver-parity + characterization) |
| `make check` / governance authority | **Confirmed** PASS |
| Staging flags not enabled | **Confirmed** |
| Dual-return / cutover not started | **Confirmed** |
| Draft staging-activation claim (`14:34:37Z`) | **Superseded / not in force** |

---

## 7. Recommendation

**Recommend: Ratify merge** — subject to Product + Engineering explicit retrospective votes below — **only because** all of the following hold:

- flags remain default off;
- legacy output remains authoritative;
- CI and post-merge tests remain green;
- no permission, privilege, membership, navigation, or runtime behaviour changed under default configuration.

**Do not** treat post-hoc merge votes alone as curing process without this retrospective Ratify/Revert decision.

**Do not** request staging activation until this incident is closed by ratification **and** remediation backlog acceptance progresses (see [`REMEDIATION_BACKLOG.md`](REMEDIATION_BACKLOG.md)).

---

## 8. Corrective action

| Action | Owner | Status |
|---|---|---|
| Open this incident/addendum with exact timeline | Engineering (docs) | **Done** (this file) |
| Request Ratify \| Revert votes (Product + Engineering) | Product / Engineering | **Requested** |
| Keep PAR-ID-001 **In progress** | Programme | **Confirmed** |
| Keep all `PROCESS_ROLE_*` flags default off | Engineering | **Confirmed** |
| Prepare remediation backlog (no staging request) | Engineering | **Done** ([`REMEDIATION_BACKLOG.md`](REMEDIATION_BACKLOG.md)) |
| If Revert: revert `598b7a12` under separate execution auth | Engineering | Contingent |
| If Ratify: close incident; proceed only to remediation (not staging) | Product / Engineering | Contingent |

---

## 9. Prevention measure

1. **Hard gate:** do not mark PRs ready / merge until Product + Engineering **Approve merge** votes with real ISO-8601 UTC timestamps are recorded in the authorization file **and** pasted on the PR.
2. Agents must not treat “implementation Authorized” as “merge Authorized.”
3. Docs-only commits that claim merge/staging authorization must not be used to unblock merge unless they contain named votes with real timestamps matching this programme’s vote protocol.
4. Prefer draft PRs until merge votes are recorded; empty CI re-triggers must not coincide with merge without the vote record.

---

## 10. Retrospective decision — vote blocks (do not invent)

### Product — @haroonwahed

```text
GI-2026-07-22-PR58-PREAUTH-MERGE — RETROSPECTIVE DECISION

PR: #58
Merge commit: 598b7a12
Merged at: 2026-07-22T14:42:13Z
Product merge vote recorded at: 2026-07-22T15:06:30Z
Engineering merge vote recorded at: 2026-07-22T15:06:45Z

@haroonwahed Product: Ratify merge | Revert merge
Timestamp: <actual ISO-8601 UTC>

Conditions acknowledged (if Ratify):
- Flags remain default off: yes | no
- Legacy output remains authoritative: yes | no
- No staging activation authorized by this ratification: yes | no
- PAR-ID-001 remains In progress: yes | no
```

### Engineering — @Technivian

```text
@Technivian Engineering: Ratify merge | Revert merge
Timestamp: <actual ISO-8601 UTC>

Engineering confirms technical safeguards remain in force and runtime
authority was unchanged under default-off flags.

Conditions acknowledged: yes | no
```

| Approver | Vote | Consent |
|---|---|---|
| @haroonwahed Product | **Requested** | Pending real ISO-8601 UTC timestamp |
| @Technivian Engineering | **Requested** | Pending real ISO-8601 UTC timestamp |

**Ratification status:** **Not ratified** — awaiting retrospective decision.

---

## 11. Closure criteria

Incident closes when either:

1. **Ratify merge** recorded verbatim for Product + Engineering → update this file to **Closed — Ratified**; keep flags off; proceed to remediation backlog only; **no** staging activation yet; or  
2. **Revert merge** recorded → execute revert under that decision; update this file to **Closed — Reverted**.
