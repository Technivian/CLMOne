# PDR-0004: GitHub-backed governance vote evidence

- **Status:** Proposed
- **Date:** 2026-07-23
- **Owner:** Repository steward
- **Affected Charter sections:** Charter §10 Change Control
- **Related ADRs:** ADR-0015 (unchanged authority scope)
- **Related exceptions:** None
- **Related active operating rule:** [Solo-maintainer standing authorization](../../SOLO_MAINTAINER_STANDING_AUTHORIZATION.md)

## Problem

Manual UTC timestamps in governance vote text are easy to misstate and can
obscure the genuine source of an approver's decision. Governance needs a
traceable, immutable evidence source without making timestamp administration a
manual task.

## Decision

For new governance votes, the genuine GitHub comment or review is the evidence
of the vote. GitHub's system-generated `created_at` is the authoritative audit
timestamp and may be retrieved for an audit, but approvers must not enter or
calculate it themselves.

Vote tables use:

| Approver | Capacity | Vote | Evidence |
|---|---|---|---|
| | | | |

The Evidence entry must link to the genuine GitHub comment or review. A valid
vote contains approver identity, governance capacity, explicit vote, reviewed
reference, and explicit conditions when applicable. The standard vote text is
defined in
[`GITHUB_VOTE_EVIDENCE_GUIDANCE.md`](../../GITHUB_VOTE_EVIDENCE_GUIDANCE.md).

This change does not remove required approval authorities, approval dates or
effective dates where applicable, platform audit timestamps, or any existing
authorization gate. It only removes manual vote-timestamp administration.
The separate solo-maintainer rule is limited to low-risk PR merges and does
not turn a missing governance vote into a valid vote.

## Users and roles affected

Product governance, Engineering governance, Security advisory reviewers,
repository stewards, and auditors.

## Lifecycle impact

None. This PDR does not create, alter, or authorize a product lifecycle.

## Permissions and access behavior

None. GitHub authorship remains the evidence identity; no CLM One permission,
role, or authority behavior changes.

## Terminology

Use **Evidence** for the direct GitHub comment or review link. Use **audit
timestamp** only for GitHub's system-generated `created_at`, not for manually
entered vote text.

## Alternatives considered

### Keep manually entered timestamps

Rejected: a manually entered value is not the source of the vote and can be
generated, copied, or inferred.

### Remove evidence requirements

Rejected: would weaken traceability and conflict with the Charter's decision
and audit expectations.

## Consequences and trade-offs

New templates require a direct evidence link and auditors may need to retrieve
the corresponding GitHub `created_at`. Historical records stay intact, so no
retroactive validation or data rewrite occurs.

## Migration and compatibility

Apply the Evidence column and standard vote text to new templates and new
authorization packages after acceptance. Preserve genuine historical GitHub
timestamps, the PR #78 premature-merge incident and correction trail, and all
retracted invented timestamps. Do not retroactively validate missing votes.

## Acceptance criteria

- Governance and agent guidance prohibit manual vote timestamps.
- ADR, PDR, exception, evidence, motion, authorization, and PR templates use
  Evidence links rather than a manual timestamp field.
- A valid-vote rule rejects proxy, generated, inferred, and copied votes.
- No runtime, migration, permission, authority, or PAR-status change occurs.

## Metrics and evidence

Review the template diff and, after acceptance, sample new governance PRs for
direct GitHub evidence links and absent manual timestamp fields.

## Approval

No approval is recorded by this proposal. It is non-binding until formally
accepted through the repository governance process.
