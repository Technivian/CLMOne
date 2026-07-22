# Implementation authorization — PAR-ID-001 resolver parity (comparison only)

**Programme:** PAR-ID-001  
**ADR:** ADR-0014 **Accepted**  
**Prerequisite:** PR [#55](https://github.com/Technivian/CLMOne/pull/55) merged to `main` @ `bb881ac2` (feature-flagged shadow sync)  
**Request timestamp:** 2026-07-22T13:36:08Z  
**Status:** **Requested** — votes not invented; do not implement until Product, Engineering, and Security advisory Approve votes are recorded verbatim

---

## Motion — Authorize non-authoritative resolver comparison

**Text:** Authorize a default-off feature flag that runs canonical process-role resolution **beside** selected legacy resolvers, compares results, records drift, and produces staging diagnostics — while **always returning the legacy result unchanged** to callers.

| Approver | GitHub identity | Governance capacity | Authority basis | Vote | Consent |
|---|---|---|---|---|---|
| Haroon Wahed | @haroonwahed | Product governance | CODEOWNERS `/docs/`; Charter v2.0 | **Requested** | Pending |
| Technivian | @Technivian | Engineering governance | CODEOWNERS `/contracts/`; PDR-0003 | **Requested** | Pending |
| Security & privacy (advisory) | @Technivian | Security review capacity | SECURITY_PRIVACY_ACCESS_AND_AUDIT; Charter §7 | **Requested (advisory, with conditions)** | Pending |

**Result:** **Not authorized** until all three votes are recorded with ISO-8601 UTC timestamps and non-authoritative confirmation.

---

## Requested scope

| Item | Requested |
|---|---|
| Flag `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` (default **off**) | **Yes** |
| Invoke canonical resolution beside selected legacy resolvers | **Yes** |
| Compare organization, user, role, delegation, active status, ambiguity | **Yes** |
| Record drift + staging diagnostics (JSON / management command) | **Yes** |
| Always return the legacy result unchanged | **Yes** |
| Fail closed for cross-tenant diagnostic anomalies + security finding | **Yes** |
| Tests proving legacy result unchanged and no automatic repair | **Yes** |

---

## Explicitly excluded

| Item | Authorized |
|---|---|
| Canonical result returned to callers | **No** |
| Access or privilege changes | **No** |
| Approval routing changes | **No** |
| Signer-selection changes | **No** |
| Workflow-assignment changes | **No** |
| Contract-owner changes | **No** |
| Legacy resolver removal | **No** |
| Automatic repair | **No** |
| Permission / membership / navigation changes | **No** |
| PAR-APR-002 / PAR-WF-010 | **No** |
| Privilege cutover | **No** |

---

## Proposed Security advisory conditions

1. Legacy resolvers remain authoritative for every production decision.
2. Workspace roles (OWNER/ADMIN/MEMBER) are never treated as process-role resolution inputs for canonical comparison targets.
3. Ambiguous ADMIN mappings remain explicit (`legacy_process_admin` / AMBIGUOUS); never merged with workspace ADMIN.
4. Parity / comparison results never alter access decisions, approval routing, signer selection, workflow assignment, or contract ownership.
5. No automatic repair of assignments or resolvers.
6. No production resolver or privilege cutover in this slice.
7. Canonical resolution errors must never replace the legacy result.
8. Cross-tenant anomalies fail closed for the diagnostic operation and create a security finding.
9. Diagnostics must not include credentials or contract content.

---

## Implementation gate

Do **not** add `PROCESS_ROLE_RESOLVER_PARITY_ENABLED` wiring or comparison hooks until this file records verbatim Product, Engineering, and Security advisory Approve votes.
