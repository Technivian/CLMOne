# Activation authorization — PAR-ID-001 canonical resolver authority

**Programme:** PAR-ID-001  
**Prerequisite implementation:** [`CANONICAL_RESOLVER_CUTOVER_AUTHORIZATION.md`](CANONICAL_RESOLVER_CUTOVER_AUTHORIZATION.md) — **Authorized**  
**PR #62 merge:** `4c08fb9c98e934ece9b1ed00ae788055cccae6f0` (2026-07-22T15:59:25Z)  
**Authorization complete timestamp:** 2026-07-22T18:00:59Z  
**Status:** **Authorized** — Product, Engineering, and Security-advisory activation votes recorded from direct user-provided text (timestamps below).

---

## Motion — Authorize controlled-pilot activation

**Text:** Authorize enabling `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED=true` with `PROCESS_ROLE_CANONICAL_RESOLVER_ORG_ALLOWLIST=controlled-pilot-org` only, for approved non-ADMIN process roles on `resolve_assignee` / `resolve_rule_assignee` and their launch/initiation chains. Legacy fallback retained. Diagnostic reporting may remain on. Profile ADMIN and workspace OWNER/ADMIN/MEMBER remain excluded. Global rollout, ADMIN cutover, and legacy resolver removal are **not** authorized.

| Approver | GitHub identity | Capacity | Authority basis | Vote | Consent |
|---|---|---|---|---|---|
| Haroon Wahed | @haroonwahed | Product governance | CODEOWNERS `/docs/`; Charter v2.0 | **Approve** | 2026-07-22T17:58:59Z |
| Technivian | @Technivian | Engineering governance | CODEOWNERS `/contracts/`; PDR-0003 | **Approve** | 2026-07-22T17:59:59Z |
| Security & privacy (advisory) | @Technivian | Security advisory | SECURITY_PRIVACY_ACCESS_AND_AUDIT | **Approve with conditions** | 2026-07-22T18:00:59Z |

**Activation scope:** `controlled-pilot-org` only (not `controlled-pilot-org-b`).  
**Rollback:** set `PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED=false` (immediate legacy).  
**Stop conditions:** CROSS_TENANT leak / unexplained canonical failure / incorrect assignee / privilege expansion / pilot workflow regression.

### Implementation vs activation

| Decision | Status |
|---|---|
| Implementation (default-off flag) | **Authorized** earlier (`15:27–15:29Z`) + merged `#62` |
| Controlled-pilot **activation** | **Authorized** by votes below |
| Global rollout / ADMIN cutover / legacy removal | **Not authorized** |

---

## Verbatim recorded votes (authoritative)

### Product — @haroonwahed

```text
APPROVE — PAR-ID-001 Controlled-Pilot Canonical Resolver Activation

Approver: @haroonwahed
Capacity: Product governance
Vote: Approve
Timestamp: 2026-07-22T17:58:59Z

I approve activation of PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED for:

- controlled-pilot-org only
- approved non-ADMIN process roles
- WorkflowTemplateStep.resolve_assignee
- workflow_routing.resolve_rule_assignee
- their existing launch and initiation chains

Conditions:

- profile ADMIN remains legacy-authoritative
- workspace OWNER, ADMIN, and MEMBER remain excluded
- the legacy resolver remains available as fallback
- no permission, membership, navigation, approval, signer, or privilege changes
- activation must be monitored and rollback-tested
- any cross-tenant anomaly or unexplained canonical failure stops the activation

This vote authorizes controlled-pilot activation only. It does not authorize
global rollout, legacy resolver removal, or ADMIN cutover.
```

### Engineering — @Technivian

```text
APPROVE — PAR-ID-001 Controlled-Pilot Canonical Resolver Activation

Approver: @Technivian
Capacity: Engineering governance
Vote: Approve
Timestamp: 2026-07-22T17:59:59Z

Engineering approves activation of the canonical resolver authority for
controlled-pilot-org only.

Conditions:

- PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED is enabled only with the approved
  organization allowlist
- approved non-ADMIN roles may resolve canonically
- excluded, missing, inactive, ambiguous, or failed canonical resolutions use
  the documented legacy fallback
- cross-tenant anomalies fail closed
- audit and monitoring remain enabled
- disabling the flag must restore legacy authority immediately
- no global activation or legacy resolver removal

This vote authorizes controlled-pilot activation and observation only.
```

### Security advisory — @Technivian

```text
APPROVE WITH CONDITIONS — PAR-ID-001 Controlled-Pilot Canonical Resolver Activation

Approver: @Technivian
Capacity: Security advisory
Vote: Approve with conditions
Timestamp: 2026-07-22T18:00:59Z

Security approves controlled activation subject to these binding conditions:

- activation is limited to controlled-pilot-org
- profile ADMIN and workspace OWNER, ADMIN, and MEMBER remain excluded
- only active, organization-consistent, unambiguous assignments may resolve
  canonically
- cross-tenant anomalies fail closed and trigger security escalation
- no cross-tenant fallback is permitted
- diagnostic and audit evidence must not expose restricted identities, role
  payloads, credentials, or contract content
- canonical failures use the documented legacy fallback
- no automatic repair or privilege expansion
- rollback by disabling the flag must remain available
- global rollout, ADMIN cutover, and legacy resolver removal require separate
  authorization

This vote authorizes controlled-pilot activation only.
```

---

## Activation outcome

See [`CANONICAL_RESOLVER_ACTIVATION_RESULTS.md`](CANONICAL_RESOLVER_ACTIVATION_RESULTS.md) — **PASS**.  
Committed settings remain default **off** after rollback proof; pilot enablement is via explicit env for authorized environments.
