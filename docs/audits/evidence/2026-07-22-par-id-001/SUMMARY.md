# PAR-ID-001 evidence summary — 2026-07-22

## Status: In progress — cutover implementation delivered; activation pending; remediation package merged; R0 gate open

**ADR:** ADR-0014 **Accepted**  
**PR #58 merge:** `598b7a12` (2026-07-22T14:42:13Z) — reviewed code HEAD `44926da9`  
**Merge votes recorded:** Product `15:06:30Z` / Engineering `15:06:45Z` (**after** merge)  
**Retrospective ratification:** Product `15:31:46Z` / Engineering `15:31:55Z` — **GI-2026-07-22-PR58-PREAUTH-MERGE Ratified and Closed**  
**Merge evidence:** `docs/audits/evidence/2026-07-22-par-id-001-pr58-merge/`  
**Canonical resolver:** implemented default-off (PR [#62](https://github.com/Technivian/CLMOne/pull/62) → `main`); activation **Requested**  
**Remediation decision package:** **Approved and merged** PR [#63](https://github.com/Technivian/CLMOne/pull/63) @ `06258d26` (2026-07-22T18:44:14Z); R0 inventory auth gate **opened** (votes Requested)


### Delivered
- Additive `RoleDefinition` catalogue (0112)
- Org-scoped `ProcessRoleAssignment` + governed service (0113)
- Feature-flagged shadow sync + assignment parity reporting
- Feature-flagged resolver comparison **merged** (legacy authoritative while diagnostic)
- Staging remediation + readiness (**READY FOR CUTOVER AUTHORIZATION**)
- `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED` (**default false**) + org allowlist
- Canonical authority wiring on `resolve_assignee` / `resolve_rule_assignee`
- ADMIN / workspace exclusions; legacy fallback; cross-tenant fail-closed
- Activation package prepared (votes **Requested**)

### Votes
| Package | Status |
|---|---|
| Remediation + cutover **implementation** | **Authorized** — Product `15:27:09Z` / Engineering `15:28:09Z` / Security `15:29:09Z` |
| **Activation** | **Requested** — not invented |

### Explicitly unchanged / not done
- Flag **not enabled** in staging or production
- Permissions / membership / navigation / privilege
- PAR-APR-002 / PAR-WF-010
- ADMIN cutover

### Flags (default off on `main` until activation)
- `PROCESS_ROLE_SHADOW_WRITE_ENABLED` = false
- `PROCESS_ROLE_PARITY_REPORTING_ENABLED` = false
- `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` = false
- `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED` = false

### Next decision gate
1. Authorize and execute R0 inventory-only (separate votes) — replace unverified 14/1/13.  
2. Separately authorize R1–R5 remediation slices as needed.  
3. Separate activation decision on [`CANONICAL_RESOLVER_ACTIVATION_AUTHORIZATION.md`](CANONICAL_RESOLVER_ACTIVATION_AUTHORIZATION.md) — stop before enabling canonical authority without recorded activation votes.  
PAR-ID-001 remains **In progress**. No flag enablement by the remediation decision package merge.

