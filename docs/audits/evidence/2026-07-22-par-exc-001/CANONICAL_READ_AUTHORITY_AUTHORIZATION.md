# PAR-EXC-001 — Canonical read authority authorization (Motion 4)

**Programme:** PAR-EXC-001  
**ADR:** ADR-0015 **Accepted** (`2026-07-22T19:12:39Z`)  
**Prerequisites:** Motion 2 **Authorized** (default-off dual-write); Motion 3 **Authorized** + controlled-pilot activation **PASS**; monitoring extension on `main` (PR #78 / correction PR #79)  
**Package type:** Separate canonical-read authority (Motion 4)  
**Status:** **Authorization requested** — votes **not carried**  
**This vote enables flags?** **No**  
**This vote merges implementation?** **No**  
**Production?** **OUT OF SCOPE**

**Do not invent votes.** Product, Engineering, and Security must each record a genuine vote with a UTC timestamp on the authorizing PR before this package may be treated as **Authorized**.

---

## Decision outcome (live)

| Field | Value |
|---|---|
| Decision | **Not authorized** (Motion 4 not carried) |
| Aggregate | Product / Engineering / Security votes incomplete |
| Security conditions acknowledged | **No** (pending Security vote) |
| Flags enabled by this record | **No** |
| Committed defaults changed by this record | **No** |
| Programme status | PAR-EXC-001 remains **In progress** |
| Exact blocker | Canonical read authority **unauthorized** — Engineering and Security votes outstanding (and Product vote must be genuine on the authorizing PR) |

---

## Motion 4 — Authorize controlled-pilot canonical read authority

**Text:** Authorize **canonical read authority** for PAR-EXC-001 under the exact environment, scope, allowlist, observation window, abort conditions, and rollback defined in this package only; authorize subsequent **default-off** dual-read / canonical-read implementation and **named-env-only** operational enablement after that implementation is merged to `main`; do **not** enable flags by this vote; do **not** change committed defaults; do **not** authorize production, automatic repair, permission/privilege changes, ADMIN authority, or legacy retirement.

### Exact environment

| Field | Value |
|---|---|
| Named environment | `par-exc-001-canonical-read-authority` |
| Class | Non-production **staging-equivalent** only (local/controlled SQLite recreate) |
| Path | `docs/audits/evidence/2026-07-22-par-exc-001/canonical_read_env/` (DB gitignored; not committed) |
| Seed / corpus basis | Recreate from Motion 3 activation evidence patterns (`controlled-pilot-org` + non-allowlisted `demo-firm` negatives) |
| Production | **OUT OF SCOPE** |
| Remote shared staging URL | **Not identified** — not inferred |

### Exact scope

| In scope | Out of scope (hard) |
|---|---|
| Six Motion-2/3 source paths only: `KEEP_EXCEPTION`, `ACCEPTED_RISK`, `AI_EXCEPTION`, `CONFLICT_CHECK_WAIVER`, `DEADLINE_DEFER`, `DPA_APPROVE_WITH_BLOCKERS` | Any other exception-like path (break-glass, signature-provider, residuals) |
| Default-off dual-read / canonical-read flags + adapters (implementation gate before enablement) | Changing committed flag defaults in repo settings |
| For allowlisted org only: enforcement **may consult** canonical `ExceptionRequest` / `ExceptionDecision` applicability (`exception_is_applicable` / `privilege_granted`) as the **authoritative applicability read** when a correlated canonical row exists | Production activation |
| Legacy write paths remain in place; dual-write may remain enabled in the same named env for the same allowlist | Automatic repair / deletion / historical invention |
| Fail-closed on cross-tenant and Critical bypass without Security approval | Permission, privilege, membership, signer, approval, or navigation changes |
| Monitoring via existing `pilot_daily_health` `exception_dual_write` block + any additive metadata-only counters required for this window | ADMIN authority / ADMIN mapping |
| | Legacy retirement / removal of legacy fallback |
| | PAR-APR-002 / PAR-WF-010 / PAR-ID-002 |

### Exact allowlist

| Flag (proposed; default-off until implemented and separately enabled in named env only) | Authorized operational value |
|---|---|
| `EXCEPTION_CANONICAL_READ_ENABLED` | `true` **only** in `par-exc-001-canonical-read-authority` after Motions carried **and** default-off implementation is on `main` |
| `EXCEPTION_CANONICAL_READ_ORG_ALLOWLIST` | `controlled-pilot-org` **only** |
| `EXCEPTION_DUAL_WRITE_ENABLED` (prerequisite during observation) | `true` in the same named env only (Motion 3 already authorized) |
| `EXCEPTION_DUAL_WRITE_ORG_ALLOWLIST` | `controlled-pilot-org` **only** |

Committed defaults in `config/settings_base.py` / `config/settings_test.py` must remain **false** / empty at all times under this package.

Global enable without allowlist is **prohibited**.

### Authority model (if Motions carried and named-env enabled)

| Phase | Authority |
|---|---|
| Before enablement | Legacy remains authoritative; canonical rows non-authoritative |
| During authorized observation (allowlisted org + correlated canonical present) | Canonical applicability / privilege-token checks are **authoritative for read**; on canonical miss/failure → **legacy fallback** (fail-open to legacy product path except cross-tenant / Critical-gate fail-closed) |
| AI_EXCEPTION without decision | Remains **SUBMITTED**; must **not** become applicable via invented decision |
| After observation (default plan) | Return all canonical-read flags to **false** / empty unless a **separate sustainment** vote carries |
| Abort / rollback | Immediate flag-off; legacy sole authority; leave canonical rows in place (no repair) |

### Observation window

| Field | Value |
|---|---|
| Window type | Controlled named-env observation (harness + required scenarios), not a production multi-day watch |
| Earliest start | Only after (1) Motions 4.1–4.4 carried with genuine votes, (2) default-off implementation merged to `main`, (3) reviewed deployment HEAD recorded, (4) rollback dry-validated |
| Planned duration | Complete required six-path matrix + negatives + monitoring stop-condition scan within a single operator session; record UTC start/end in exit evidence |
| Operators on watch | Engineering (cutover / rollback); Security may order stop |
| Evidence location | This directory + `canonical_read_env/` + `pending/` placeholders as created at execution |

### Abort conditions (immediate stop)

Disable `EXCEPTION_CANONICAL_READ_ENABLED` and clear `EXCEPTION_CANONICAL_READ_ORG_ALLOWLIST` (and, if dual-write stop conditions also fire, disable dual-write per Motion 3) on **any** of:

1. Cross-tenant anomaly or data exposure  
2. Unauthorized Critical bypass / Security-gate failure  
3. Invented historical decision or AI_EXCEPTION becoming applicable without authorized decision  
4. Duplicate canonical decision / duplicate correlation creating conflicting authority  
5. Missing owner or expiry on an approved/active temporary exception relied on for authority  
6. Privilege or permission expansion attributable to canonical read  
7. ADMIN authority or automatic ADMIN mapping  
8. User-visible regression attributable to canonical read  
9. Inability to restore legacy authority immediately via flag-off  
10. Material difference between reviewed and deployed HEAD  
11. Restricted content (credentials, contract body, unrestricted identity) appearing in monitoring evidence  
12. Security reviewer stop instruction  

Abort criteria do **not** depend solely on aggregate percentages. A single tenant-isolation, Critical-control, or invented-authority violation is a **stop**.

### Rollback

```bash
# In par-exc-001-canonical-read-authority only
export EXCEPTION_CANONICAL_READ_ENABLED=false
export EXCEPTION_CANONICAL_READ_ORG_ALLOWLIST=
# If dual-write stop also required:
export EXCEPTION_DUAL_WRITE_ENABLED=false
export EXCEPTION_DUAL_WRITE_ORG_ALLOWLIST=
```

1. Flag-off is non-destructive.  
2. Leave canonical rows in place — **no** automatic repair or deletion.  
3. Legacy paths become sole authority again.  
4. Capture stop-event audit evidence; do not invent remediation decisions.  
5. Committed repo defaults remain unchanged.

---

## Motions (explicit)

### Motion 4.1 — Accept exact environment, scope, allowlist, and observation window

**Text:** Accept the exact named environment `par-exc-001-canonical-read-authority`, six-path scope, allowlist `controlled-pilot-org` only, observation window, and monitoring posture defined above.

| Approver | Capacity | Vote | Timestamp (UTC) | Evidence |
|---|---|---|---|---|
| @haroonwahed | Product governance | _pending_ | | |
| @Technivian | Engineering governance | _pending_ | | |
| @Technivian | Security advisory | _pending_ | | |

**Motion 4.1 result:** **Not carried**

### Motion 4.2 — Authorize canonical read authority in that exact environment

**Text:** Authorize canonical read authority (canonical applicability authoritative for correlated rows) in `par-exc-001-canonical-read-authority` only, for `controlled-pilot-org` and the six approved paths only; authorize default-off implementation of `EXCEPTION_CANONICAL_READ_*` (or equivalent) prior to enablement; this vote does **not** enable flags.

| Approver | Capacity | Vote | Timestamp (UTC) | Evidence |
|---|---|---|---|---|
| @haroonwahed | Product governance | _pending_ | | |
| @Technivian | Engineering governance | _pending_ | | |
| @Technivian | Security advisory | _pending_ | | |

**Motion 4.2 result:** **Not carried**

### Motion 4.3 — Authorize defined rollback on abort

**Text:** Authorize the flag-off rollback procedure above as the binding abort response; Security may order stop; Engineering executes.

| Approver | Capacity | Vote | Timestamp (UTC) | Evidence |
|---|---|---|---|---|
| @haroonwahed | Product governance | _pending_ | | |
| @Technivian | Engineering governance | _pending_ | | |
| @Technivian | Security advisory | _pending_ | | |

**Motion 4.3 result:** **Not carried**

### Motion 4.4 — Confirm hard exclusions remain out of scope

**Text:** Confirm that production activation, automatic repair, permission/privilege/membership/signer/approval/navigation changes, ADMIN authority, and legacy retirement remain **out of scope** and are **not** authorized by Motions 4.1–4.3.

| Approver | Capacity | Vote | Timestamp (UTC) | Evidence |
|---|---|---|---|---|
| @haroonwahed | Product governance | _pending_ | | |
| @Technivian | Engineering governance | _pending_ | | |
| @Technivian | Security advisory | _pending_ | | |

**Motion 4.4 result:** **Not carried**

---

## Security conditions (must be acknowledged on Security vote)

1. Activation limited to `controlled-pilot-org` in the named non-production env only.  
2. Committed defaults remain off; this vote does not enable flags.  
3. Cross-tenant anomalies fail closed.  
4. Critical bypasses require existing Security controls (`security_approval=True`).  
5. No invented historical decisions; AI exceptions stay SUBMITTED until authorized decision.  
6. No automatic repair; no privilege/permission expansion; no ADMIN authority.  
7. Restricted data must not appear in monitoring evidence.  
8. Rollback must remain immediately available; Security stop instruction honored immediately.  
9. Production and legacy retirement remain unauthorized.  
10. Stop on any listed abort condition.

**Security conditions acknowledged:** **No** (pending Security **Approve** or **Approve with conditions** that explicitly acknowledges 1–10).

---

## Vote template (reply on the authorizing PR — do not invent)

```text
MOTION 4 — PAR-EXC-001 Canonical Read Authority

Approver: @<identity>
Capacity: Product governance | Engineering governance | Security advisory
Timestamp: <UTC ISO-8601>

Motions 4.1–4.4: Approve | Approve with conditions | Reject

Vote: <...>

Conditions acknowledged (required for Security):
1–10 as listed in CANONICAL_READ_AUTHORITY_AUTHORIZATION.md — yes/no
```

---

## Preconditions before any operational enablement (after votes carry)

1. Motions 4.1–4.4 carried with genuine Product + Engineering + Security votes and UTC timestamps.  
2. Security conditions 1–10 acknowledged **yes**.  
3. Default-off dual-read / canonical-read implementation merged to `main` (separate implementation PR).  
4. Exact reviewed deployment HEAD recorded and deployed to the named env without material drift.  
5. Dual-write Motion 3 stop conditions clear (or dual-write also rolled back if required).  
6. Rollback dry-validated (flag-off) **before** canonical-read enablement.  
7. Evidence capture locations ready.  
8. No production target.

---

## Related programme notes

- PR #78 monitoring remains on `main`; Eng/Sec post-merge ratification for continued retention is a **separate** governance item and is **not** substituted by Motion 4.  
- PAR-EXC-001 stays **In progress** until Completion criteria are met; authorizing Motion 4 alone does not mark the programme Completed.  
- Flags were **not** enabled by preparing this package.
