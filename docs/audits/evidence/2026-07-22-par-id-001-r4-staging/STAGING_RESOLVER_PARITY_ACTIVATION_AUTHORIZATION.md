# PAR-ID-001 — R4 staging resolver-parity diagnostic activation authorization

**Programme:** PAR-ID-001  
**ADR:** ADR-0014 **Accepted**  
**Baseline `main`:** `2e7b5adc`  
**Prerequisite:** R0 inventory **Completed** / **PASS**; R1 CERTAIN remediation **Completed** / **PASS** (12 creates); R2 **Not required on verified corpus**; R3 **Deferred** (explicit CERTAIN assignments only; AMBIGUOUS ADMIN hold under P1+P3; P2 rejected)  
**Policy binding:** P1 labels + P3 authority; **P2 rejected**  
**Status:** **Authorized and executed — R4 PASS** (bundled authorization + staging execution)  
**Authorized environment (named):** `par-id-001-r4-staging-equivalent`  
**Environment path:** `docs/audits/evidence/2026-07-22-par-id-001-r4-staging/staging_env/` (ephemeral SQLite; DB not committed)  
**Does not authorize:** production activation; R5 canonical authority; dual-return; privilege / ADMIN cutover; removal of legacy fallback  

**Do not use** `CANONICAL_RESOLVER_ACTIVATION_AUTHORIZATION.md` for this slice.  
**R5 reserved separately:** [`CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md`](CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md)

---

## Motion — Authorize R4 staging diagnostic activation only

**Text:** Authorize enabling the three diagnostic process-role flags **only** in the explicitly named non-production staging environment `par-id-001-r4-staging-equivalent`, for resolver/assignment parity evidence collection under the runtime requirements below; execute the approved scenario matrix; capture parity, security, and rollback evidence; and publish an R4 exit verdict — **without** enabling flags in production, adding or enabling a canonical authority flag, returning canonical output to callers, authorizing R5, performing privilege or ADMIN cutover, or removing legacy fallback. Committed defaults must remain `false`.

| Approver | Vote | Consent |
|---|---|---|
| @haroonwahed Product | **Approve** | `2026-07-22T19:41:15Z` |
| @Technivian Engineering | **Approve** | `2026-07-22T19:41:16Z` |
| @Technivian Security advisory | **Approve with conditions** | `2026-07-22T19:41:17Z` — Conditions acknowledged: **yes** |

**R4 authorization status:** **Authorized** (bundled — authorization + staging activation + evidence capture in `par-id-001-r4-staging-equivalent` only).

### Recorded approvals (verbatim)

```text
@haroonwahed Product: Approve
Timestamp: 2026-07-22T19:41:15Z

@Technivian Engineering: Approve
Timestamp: 2026-07-22T19:41:16Z

@Technivian Security advisory: Approve with conditions
Timestamp: 2026-07-22T19:41:17Z
Conditions acknowledged: yes
```

Timestamps obtained at recording via `date -u +"%Y-%m-%dT%H:%M:%SZ"` (not placeholders).

---

## Authorized staging flags

| Flag | Staging value | Committed / production default |
|---|---|---|
| `PROCESS_ROLE_SHADOW_WRITE_ENABLED` | `true` | `false` |
| `PROCESS_ROLE_PARITY_REPORTING_ENABLED` | `true` | `false` |
| `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` | `true` | `false` |

**Not authorized:** `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED` (must remain off / unused for R4).

Activation method: environment variables in `par-id-001-r4-staging-equivalent` only (gitignored DB / local env). No committed default change.

---

## Runtime requirements (binding)

1. Legacy resolver output remains authoritative and is always returned.
2. Canonical output remains diagnostic only.
3. Comparison failure remains fail-open.
4. No automatic repair.
5. No process authority derived from workspace ADMIN.
6. AMBIGUOUS ADMIN remains non-authoritative.
7. No privilege, permission, membership, signer, approval, or navigation changes.
8. No production activation.
9. Flag-off is the immediate rollback.
10. All diagnostic evidence must be tenant-scoped and permission-safe.

---

## Binding Security conditions (acknowledged)

1. Activation is limited to the named non-production environment `par-id-001-r4-staging-equivalent`.
2. Committed defaults for all `PROCESS_ROLE_*` flags remain `false`.
3. Legacy resolver return values must never be replaced, reordered, or filtered by canonical comparison.
4. Comparison errors must fail-open (legacy still returned; no product-path raise from comparison).
5. Cross-tenant anomalies must be classified `CROSS_TENANT_ANOMALY` / security findings and must not attempt repair.
6. AMBIGUOUS ADMIN must remain explicit and non-authoritative; no workspace ADMIN → process authority.
7. Diagnostic output must be tenant-scoped and must not leak credentials, contract content, or unrestricted cross-tenant identity.
8. No automatic create/deactivate/rewrite of assignments, memberships, or profiles during R4 activation.
9. No privilege, permission, membership, signer, approval, or navigation changes.
10. R5 canonical authority cutover remains separately gated; this vote does not authorize R5.

---

## Required scenarios

Exercise at minimum:

- NDA launch and assignment
- MSA launch and assignment
- DPA launch and privacy routing
- generic workflow
- approval initiation
- legal reviewer resolution
- finance approver resolution
- privacy reviewer resolution
- signer resolution where applicable
- delegation
- reassignment
- inactive assignment
- unresolved assignment
- ADMIN ambiguity
- two-tenant isolation
- comparison error and fail-open behaviour

---

## Required evidence

- assignment parity counts
- resolver parity counts
- MATCH / LEGACY_ONLY / CANONICAL_ONLY / DIFFERENT_USER / DIFFERENT_ROLE / AMBIGUOUS / INACTIVE_ASSIGNMENT / CROSS_TENANT_ANOMALY / RESOLUTION_ERROR
- rollback result
- audit and diagnostic metadata review
- flag state before, during, and after activation

---

## R4 exit criteria

- `CROSS_TENANT_ANOMALY` = 0
- `DIFFERENT_USER` = 0
- unexpected `LEGACY_ONLY` = 0
- unexpected `CANONICAL_ONLY` = 0
- known ADMIN ambiguity explicitly identified and non-authoritative
- comparison errors do not change runtime output
- rollback by flag-off passes
- legacy remains authoritative
- no restricted diagnostic leakage
- all committed defaults remain false
- tests and CI green
- evidence reviewed by Product, Engineering and Security

---

## Explicit non-authorization

| Item | Status |
|---|---|
| Production flag enablement | **Not authorized** |
| Canonical authority flag / dual-return | **Not authorized** |
| R5 / `CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION` | **Reserved; not authorized** |
| Privilege or ADMIN cutover | **Not authorized** |
| Removal of legacy fallback | **Not authorized** |
| Use of `CANONICAL_RESOLVER_ACTIVATION_AUTHORIZATION.md` for this slice | **Prohibited** |

---

## Programme gate status (at authorization)

| Gate | Status |
|---|---|
| R0 | **Completed** |
| R1 | **Completed** |
| R2 | **Not required on verified corpus** |
| R3 | **Deferred** (explicit CERTAIN assignments only) |
| R4 | **Authorized and Completed (PASS)** — see [`R4_EXIT_REPORT.md`](R4_EXIT_REPORT.md) |
| R5 | **Blocked** — draft/requested [`../2026-07-22-par-id-001-r5-canonical-authority-cutover/CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md`](../2026-07-22-par-id-001-r5-canonical-authority-cutover/CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md) (not authorized) |
