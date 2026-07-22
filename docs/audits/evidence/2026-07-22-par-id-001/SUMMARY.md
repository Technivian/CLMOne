# PAR-ID-001 evidence summary — 2026-07-22

## Status: In progress — shadow sync delivered (non-authoritative)

**ADR:** ADR-0014 **Accepted**  
**PR #53 merge:** `0bf7c9dc` (catalogue 0112)  
**PR #54 merge:** `58966de7` (process-role adapter 0113)  
**This slice:** feature-flagged shadow synchronization + parity evidence (no new migration)

### Delivered
- Additive `RoleDefinition` catalogue (0112)
- Org-scoped `ProcessRoleAssignment` model + governed service (0113)
- Dual-read parity / drift diagnostics (non-authoritative)
- Feature-flagged shadow sync from `UserProfile.role` → `ProcessRoleAssignment`
- Deterministic `process_role_parity_report` management command
- Shadow write-path inventory + implementation authorization request

### Explicitly unchanged
- Permissions / authorization outcomes
- `OrganizationMembership.role` authority
- `UserProfile.role` behaviour (still authoritative)
- Approval / signer / workflow runtime resolution
- Navigation
- PAR-APR-002 / PAR-WF-010

### Programme record
- Canonical catalogue delivered
- Organization-scoped assignments delivered
- Dual-read diagnostics delivered
- Feature-flagged shadow synchronization delivered
- Parity evidence available
- Production permissions and runtime resolvers remain legacy
- Resolver cutover requires separate authorization

### Flags (default off)
- `PROCESS_ROLE_SHADOW_WRITE_ENABLED`
- `PROCESS_ROLE_PARITY_REPORTING_ENABLED`

### Next slice (not authorized)
Feature-flagged production resolver dual-read consumption / privilege cutover — **new authorization required**.
Stop before production resolver or privilege cutover.
