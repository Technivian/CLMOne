# PAR-ID-001 evidence summary — 2026-07-22

## Status: In progress — resolver parity merged; staging gate NOT READY for cutover

**ADR:** ADR-0014 **Accepted**  
**PR #53 merge:** `0bf7c9dc` (catalogue 0112)  
**PR #54 merge:** `58966de7` (process-role adapter 0113)  
**PR #55 merge:** `bb881ac2` (2026-07-22T13:35:32Z) — reviewed HEAD `432a55b1`  
**Merge evidence:** PR #59 → `main` @ `0d9712ca`  
**PR #52 / #57:** visual remediation + merge evidence on main  
**PR #58 merge:** `598b7a128cb8d0f5be0c7cd2fb1880f631ca9608` (2026-07-22T14:42:13Z) — resolver-parity comparison (flag default off)

### Delivered
- Additive `RoleDefinition` catalogue (0112)
- Org-scoped `ProcessRoleAssignment` model + governed service (0113)
- Dual-read parity / drift diagnostics (non-authoritative)
- Feature-flagged shadow sync from `UserProfile.role` → `ProcessRoleAssignment`
- Deterministic `process_role_parity_report` management command
- Shadow write-path inventory + Slice 3 implementation/merge authorization
- Resolver usage matrix + resolver-parity authorization (Product `14:17:31Z` / Engineering `14:18:31Z` / Security `14:15:31Z`; prior `14:04–14:06Z` draft record superseded)
- Feature-flagged resolver comparison (`PROCESS_ROLE_RESOLVER_PARITY_ENABLED`, default off) **merged**
- `process_role_resolver_parity_report` staging diagnostics
- Staging activation evidence: [`STAGING_RESOLVER_PARITY_RESULTS.md`](STAGING_RESOLVER_PARITY_RESULTS.md)

### Staging gate (2026-07-22)
- Flags on in staging-equivalent only: shadow write, parity reporting, resolver parity
- All-org report: total 37; MATCH 9; AMBIGUOUS 13; INACTIVE_ASSIGNMENT 14; LEGACY_ONLY 1; critical 0
- CROSS_TENANT_ANOMALY / DIFFERENT_USER / RESOLUTION_ERROR = 0
- **Verdict:** **NOT READY, REMEDIATION REQUIRED**
- `CANONICAL_RESOLVER_CUTOVER_AUTHORIZATION.md` **withheld**

### Explicitly unchanged
- Permissions / authorization outcomes
- `OrganizationMembership.role` authority
- `UserProfile.role` behaviour (still authoritative)
- Approval / signer / workflow runtime resolution return values (legacy always returned)
- Navigation
- PAR-APR-002 / PAR-WF-010
- Defaults remain **off** in committed settings; staging `.env` only

### Programme record
- Canonical catalogue delivered
- Organization-scoped assignments delivered
- Dual-read diagnostics delivered
- Feature-flagged shadow synchronization delivered **and merged**
- Resolver comparison delivered **and merged** (legacy authoritative)
- Staging diagnostic evidence collected; cutover **not** authorized
- Production permissions and runtime resolvers remain legacy
- Dual-return / privilege cutover requires a **separate** authorization after remediation

### Flags (committed default off)
- `PROCESS_ROLE_SHADOW_WRITE_ENABLED`
- `PROCESS_ROLE_PARITY_REPORTING_ENABLED`
- `PROCESS_ROLE_RESOLVER_PARITY_ENABLED`

### Next decision gate
Remediate unresolved LEGACY_ONLY / inactive active-assignment gaps; Product + Security accept or exclude AMBIGUOUS ADMIN; complete threat review; then prepare `CANONICAL_RESOLVER_CUTOVER_AUTHORIZATION.md` with a **separate default-off authority flag** and named votes (do not invent).
Stop before canonical resolver output affects any production decision.
