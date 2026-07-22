# PAR-ID-001 evidence summary — 2026-07-22

## Status: In progress — remediation decision package pending

**ADR:** ADR-0014 **Accepted**  
**PR #58 merge:** `598b7a12`  
**Evidence HEAD:** `main` @ `8316a756`  
**Retrospective ratification:** GI-2026-07-22-PR58-PREAUTH-MERGE **Ratified and Closed**  
**Remediation decision package:** `docs/audits/evidence/2026-07-22-par-id-001-remediation-decision/` (**pending votes**)

### Delivered
- Additive `RoleDefinition` catalogue (0112)
- Org-scoped `ProcessRoleAssignment` model + governed service (0113)
- Dual-read parity / drift diagnostics (non-authoritative)
- Feature-flagged shadow sync from `UserProfile.role` → `ProcessRoleAssignment`
- Deterministic `process_role_parity_report` management command
- Shadow write-path inventory + Slice 3 implementation/merge authorization
- Resolver usage matrix + resolver-parity authorization (Product `14:17:31Z` / Engineering `14:18:31Z` / Security `14:15:31Z`)
- Feature-flagged resolver comparison **merged** (`PROCESS_ROLE_RESOLVER_PARITY_ENABLED`, default off)
- `process_role_resolver_parity_report` management command
- Merge authorization Product `15:06:30Z` / Engineering `15:06:45Z` (staging activation **not** authorized; `14:34:37Z` staging claim superseded)

### Explicitly unchanged
- Permissions / authorization outcomes
- `OrganizationMembership.role` authority
- `UserProfile.role` behaviour (still authoritative)
- Approval / signer / workflow runtime resolution return values (legacy always returned)
- Navigation
- PAR-APR-002 / PAR-WF-010
- Flags remain **default off** (not enabled by merge)

### Programme record
- Canonical catalogue delivered
- Organization-scoped assignments delivered
- Dual-read diagnostics delivered
- Feature-flagged shadow synchronization delivered **and merged**
- Resolver comparison delivered **and merged** behind default-off flag (legacy authoritative)
- Production permissions and runtime resolvers remain legacy
- Dual-return / privilege cutover requires separate authorization
- Staging flag activation requires separate authorization

### Flags (default off on `main`)
- `PROCESS_ROLE_SHADOW_WRITE_ENABLED` = false
- `PROCESS_ROLE_PARITY_REPORTING_ENABLED` = false
- `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` = false

### Next decision gate
1. Approve remediation decision package (ADMIN policy + threat review + analysis).  
2. Separately authorize and verify remediation implementation slices (R0+).  
3. Only then consider staging activation authorization.  
PAR-ID-001 remains **In progress**. No flag enablement by this package.
