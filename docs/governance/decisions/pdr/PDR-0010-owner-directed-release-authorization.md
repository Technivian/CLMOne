# PDR-0010: Owner-directed repository and release authorization

**Status:** Proposed — not yet binding.  
**Date:** 2026-07-28  
**Owner:** Repository owner (`@haroonwahed`)  
**Affected Charter sections:** Active Charter §16; proposed Charter v3 §10–11  
**Related PDRs:** PDR-0004, PDR-0008, PDR-0009  
**Related Charter proposal:** `docs/governance/GOVERNANCE_CHARTER_V3_PROPOSED.md`

## Problem

CLM One currently requires independent Product, Engineering, and Security
GitHub reviews for production, permission, visibility, automatic-repair,
ADMIN-authority, and legacy-retirement changes. The repository currently has
one direct human administrator, making those gates impossible to satisfy and
preventing the owner from authorizing work in an owner-operated application.

## Proposed decision

Adopt an owner-directed authorization model. The authenticated repository owner
`@haroonwahed` is the final Product, Engineering, Security, and Release
Authority for this repository and may authorize any repository change,
including production activation, permission or visibility changes, automatic
repair, ADMIN authority, and legacy retirement.

An explicit owner instruction recorded in an owner-controlled Codex workspace,
GitHub pull request, issue, release, or deployment record is sufficient
authorization. Independent reviewers and approving GitHub reviews become
optional advisory controls rather than mandatory release gates.

Green CI remains the default technical gate for the exact release SHA.
Overriding a failed or unavailable check requires an explicit owner decision
that names the affected check, reason, scope, rollback plan, and target SHA.
Historical approvals, CI records, and release evidence remain immutable.

## Users and roles affected

This changes repository governance only. It creates no CLM One product role,
workspace permission, or end-user authority. The authorization belongs solely
to the authenticated GitHub repository owner.

## Lifecycle impact

None. Contract, workflow, approval, document, signature, and obligation
lifecycle semantics remain unchanged. Individual implementation decisions
remain responsible for their own lifecycle and rollback behavior.

## Permissions and access behavior

This decision allows the repository owner to authorize changes to access
behavior without independent reviewers. It does not itself change any runtime
permission, visibility rule, tenant boundary, or production configuration.
Each such change must still be explicit, tested, auditable, and separately
implemented.

## Terminology

- **Repository owner:** the authenticated owner account `@haroonwahed`.
- **Owner authorization:** an explicit, attributable instruction approving a
  defined scope or exact SHA.
- **Advisory review:** optional review that informs but does not bind the owner.

## Alternatives considered

### Retain three independent mandatory reviewers

Rejected as the proposed target because the repository has only one direct
human administrator and the requirement blocks owner-operated delivery.

### Apply the existing single-maintainer exception only

Rejected as insufficient because it excludes permission, visibility,
production, repair, ADMIN-authority, and retirement changes.

### Remove all CI and release evidence

Rejected. Owner authority replaces mandatory human approval, not technical
verification, traceability, rollback planning, or historical evidence.

## Consequences and trade-offs

Delivery no longer depends on recruiting independent reviewers. Decision
authority and accountability are concentrated in one person, increasing the
risk that design, security, or operational defects are not independently
challenged. Optional specialist review remains encouraged for high-risk work.

## Migration and compatibility

After acceptance, one atomic governance change must:

1. replace active Charter §16 with the owner-directed authorization text;
2. update `AGENTS.md` and the GitHub review/release evidence guide;
3. update affected roadmap and PDR gate language without rewriting historical
   evidence;
4. update CI checks that validate the former mandatory-review policy; and
5. record the effective version and date.

Existing GitHub reviews, attestations, releases, and deferral records remain
historical evidence and must not be deleted or reinterpreted.

## Acceptance criteria

- The replacement Charter text identifies one accountable owner authority.
- Agent instructions accept explicit owner authorization for in-scope work.
- Independent reviews are advisory, not mandatory.
- Green CI remains the normal exact-SHA technical gate.
- Any owner override of CI is explicit, attributable, scoped, and reversible.
- Runtime authorization, tenant isolation, audit, testing, and rollback
  requirements remain intact.
- Historical governance evidence is preserved.

## Metrics and evidence

Track release SHA, CI outcome, owner authorization reference, rollback
availability, deployment result, and post-release incidents. Do not fabricate
reviews or rewrite historical evidence.

## Approval

This record is Proposed and does not yet change active governance. Its status,
effective date, and authorizing evidence must be recorded through the
governance process applicable while this proposal is under consideration.

