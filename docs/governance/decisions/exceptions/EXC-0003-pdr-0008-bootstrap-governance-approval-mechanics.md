# EXC-0003: PDR-0008 bootstrap governance approval mechanics

**Status:** Active — temporary bootstrap-governance exception
**Owner:** Haroon Wahed (`@haroonwahed`)
**Approval authority:** Explicit, attributable repository-owner direction under
Governance Charter §16 / PDR-0010; this is an owner authorization, not an
independent GitHub review
**Start date:** 2026-08-09
**Hard expiry / review date:** 2026-09-30
**Affected Charter rule:** Independent Product, Engineering, and Security
approval mechanics for PDR-0008 private-by-default access implementation

## Deviation

For PDR-0008 only, the owner may replace the normal three-independent-human
reviewer approval mechanics that are unavailable in this single-maintainer
bootstrap organization. This exception authorizes implementation planning and
implementation work for the approved private-by-default policy; it does not
authorize a runtime authorization change, deployment, production activation,
or a release.

The normal governance requirement remains independent Product, Engineering,
and Security GitHub approval, green CI for the unchanged reviewed SHA, and the
applicable release evidence. This temporary exception replaces only the
unavailable reviewer mechanics and records the owner authorization
transparently.

## Scope

Approval mechanics for the PDR-0008 shared private-by-default contract access
implementation, including its inherited document, workflow, search, audit and
export controls. It applies to no other PDR, contract type, permission,
production environment, deployment, data repair, migration, or legacy
retirement.

## Rationale

Haroon Wahed is the sole direct human repository/product owner and GitHub
collaborator with administrator access. Independent human review is therefore
not currently available. The owner has directed:

> PDR-0008 APPROVED FOR IMPLEMENTATION UNDER BOOTSTRAP GOVERNANCE EXCEPTION.

This record implements the Charter's temporary owner-directed mechanism rather
than fabricating independent approvals, creating proxy accounts, or treating
automation as a reviewer.

## Risks

The exception removes independent human review of the approval mechanics for a
security-sensitive access-policy implementation. It does not reduce the risk
of an authorization, tenant-isolation, metadata-disclosure, or rollback
failure; those risks remain mandatory gates.

## Safeguards

- Full authorization, tenant-isolation, and security regression evidence.
- PAR-SEC-002 enforcement and characterization coverage.
- Search and count non-disclosure coverage.
- Access-revocation coverage.
- Document, workflow, and export inheritance coverage.
- Bandit, TruffleHog, and dependency-audit results.
- Full browser-regression evidence.
- Documented and tested rollback evidence.
- An immutable existing-data accountability/backfill preflight before any
  ownership or creator-data transition.

No security invariant is waived. In particular, private-by-default
fail-closed behavior, tenant isolation, auditability, non-disclosure, and
rollback requirements remain mandatory before any live authorization or
production gate.

## Monitoring

PDR-0008 implementation work must remain linked to PR #176 and preserve the
listed evidence. Any scope expansion, runtime authorization change, missing
safeguard, failed security gate, or expired exception stops work pending a new
authorized decision. Feature flags do not grant authority.

## Exit plan

The exception expires automatically on 2026-09-30 unless it is explicitly
reviewed and renewed through the governance process. It ends earlier when
independent governance capacity becomes available; subsequent PDR-0008 work
then uses the normal independent Product, Engineering, and Security review
mechanics.

## Resolution evidence

- Owner-directed authorization: AGENT PROMPT 41 in the owner-controlled Codex
  workspace, dated 2026-08-09.
- Governance package: [PR #176](https://github.com/Technivian/CLMOne/pull/176).

This record contains no manually maintained approval table, copied review, or
claimed independent approval.
