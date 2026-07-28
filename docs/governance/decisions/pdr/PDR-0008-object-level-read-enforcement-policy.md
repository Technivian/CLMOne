# PDR-0008: Object-level read enforcement policy for search, analytics, and AI

**Status:** Proposed — policy scope accepted in Addendum 001; implementation
requires either the stated review gate or explicit repository-owner
authorization for a defined scope.
**Date:** 2026-07-25
**Owner:** Pilot Hardening PAR-SEC-002 — Programme, Product, Engineering, and Security: `@haroonwahed` (the recorded sole direct human administrator)
**Affected Charter sections:** §16 Repository evidence and release control
**Related programme:** PAR-SEC-002
**Evidence:** `docs/audits/evidence/2026-07-24-par-sec-002/BASELINE_AUDIT.md`; `docs/audits/evidence/2026-07-25-par-sec-002-characterization/ROUTE_MATRIX.md`
**Addendum:** [PDR-0008 Addendum 001](PDR-0008-ADDENDUM-001-policy-resolution.md)

## Status and authority boundary

This record proposes the product and security policy needed before PAR-SEC-002
can change any read result, permission, filtering, or runtime authorization.
It creates no service, model, migration, feature flag, role, permission,
filter, result-visibility change, operational activation, or production
behaviour.  Until a separately authorized implementation is merged and
activated through its applicable release gate, current runtime behaviour is
unchanged.

The Pilot Hardening bootstrap permits this planning-only record to use the
repository-owner attestation process for its PR.  It does not authorize the
future enforcement described here.  Any implementation or activation that
changes permissions or visible results requires independent Product,
Engineering, and Security GitHub approvals, green CI, and the applicable
release record; a feature flag alone grants no authority.

## Problem and context

The completed baseline and characterization show that the inventoried search,
analytics, and AI routes enforce workspace isolation, but do not consistently
apply an object-level policy.  In particular, `EthicalWall` is stored with an
organization, client and/or matter, restricted users, active state, and expiry
but is not evaluated by these read paths.  Search facets and analytics can
therefore be affected by restricted rows, search telemetry returns raw query
text to any active workspace member, and AI context is only membership-gated.

The active domain, security, engineering, and data/AI documents require
object-level access, Ethical Wall enforcement, non-leaking restricted metadata,
and AI context limited to data the requester may access.  Guessing those
semantics in a code fix would itself be a permission and product decision.

## Proposed policy

### Object read eligibility and Ethical Walls

Every in-scope read must first establish the active workspace and ordinary
server-side route permission, then evaluate object read eligibility before the
object, its metadata, a count derived from it, or its AI context is returned.
Client-side hiding is never part of that decision.

For a future implementation, an Ethical Wall matches a contract only when all
of the following hold:

1. the wall, contract, requester, and related client/matter are in the same
   organization;
2. the wall is active and is not expired;
3. the wall has a direct relationship to the contract's matter, contract's
   client, or the client of the contract's matter; and
4. the requester is listed in that wall's `restricted_users`.

Any matching wall denies the protected object read.  Multiple matching walls
are additive: one denial is sufficient.  A wall with neither a client nor a
matter is invalid configuration, not an organization-wide implicit wall; a
future configuration path must reject or quarantine it rather than inventing a
scope.  A contract without either relation has no Ethical-Wall match under this
policy, but it remains subject to every other existing object and route check.

This is a target policy, not a claim that the current `EthicalWall` data is
complete or enforced.  A future implementation must use one reusable
Access-Control policy boundary rather than duplicating relation logic in each
view or serializer.

### Search results, suggestions, and facets

Search, autocomplete, repository list projections, semantic retrieval, and
saved-view previews must filter candidate objects through object read
eligibility before serialization.  A denied object must not affect a title,
identifier, URL, status, counterparty, type, timestamp, result count, spelling
suggestion, ranking signal, or empty-state explanation returned to the
requester.

Facets, totals, and pagination totals must be calculated only from eligible
objects.  If a query backend cannot apply the same policy before it aggregates,
the surface is unavailable rather than returning an unfiltered aggregate.  A
future UI may present a generic empty result, but it must not reveal whether a
restricted object exists.

### Analytics role gates and aggregate suppression

Executive, clause, and operational analytics are an organization-manager
surface.  A future implementation must require the existing server-side
manager/owner-or-admin predicate before calculating or returning those
analytics; an active membership alone is insufficient.

Analytics must be formed only from objects eligible for the requesting manager
under the same object policy as source records.  To prevent small-cohort
disclosure, a proposed metric or facet bucket is suppressed when fewer than
five eligible source objects contribute to it.  Suppressed buckets must not
reveal the underlying count or identity, and a response must not distinguish a
suppressed restricted cohort from an absent cohort.  The threshold and its
exception process require Product/Security acceptance before implementation;
this proposed value is not live policy.

### Telemetry minimization

Raw search text, prompts, result counts tied to a query, contract identifiers,
and object metadata are not operations telemetry.  A future telemetry endpoint
may be available only to the manager audience and may return only aggregated,
content-free operational data such as surface, standardized event category,
and reporting window.  It must not return raw historical query rows.

Existing raw telemetry must not be silently deleted, repaired, exported, or
reclassified by this policy.  Any retention change or historic-data action is
a separately scoped privacy and operational decision with its own rollback
plan.

### AI context filtering and redaction

Before an AI route retrieves a contract, document, clause, or search context,
it must apply the same object read eligibility decision as the corresponding
human read.  A denied or indeterminate decision supplies no object context and
returns a non-leaking denial.  A prompt cannot broaden the retrieval scope.

For an eligible object, a future AI context builder must exclude fields or
document regions classified as restricted by an accepted data-classification
policy.  Until that classification and redaction map exist, the safe proposed
behaviour for a wall-restricted or indeterminate object is deny-without-context,
not partial redaction inferred from labels or templates.  AI remains
non-authoritative and this policy does not change its `SUBMITTED` or decision
semantics.

### Fail-closed behaviour

Missing workspace context, tenant mismatch, inactive membership, missing
object relation needed for evaluation, malformed wall scope, unavailable policy
evaluation, or an unclassified required AI field causes a deny or generic
empty result.  No route may fall back to membership-only access merely because
the object policy cannot be evaluated.  The external response must contain no
restricted title, identifier, count, query, prompt, or reason; operators may
receive only the content-free evidence described below.

## Audit, abort, and rollback rules

A future enforcement change must produce protected audit evidence for allow,
deny, suppression, policy-error, and rollback outcomes.  The evidence may use
an authorized audit correlation and opaque resource reference, but must not
put titles, query text, prompts, document contents, result counts, or
restricted metadata in application logs or client responses.  Denial reasons
are limited to policy categories such as `tenant`, `membership`, `wall`,
`object_policy_unavailable`, `analytics_role`, and `redaction_unavailable`.

Stop and abort an enforcement observation immediately if any cross-tenant or
Ethical-Wall-protected content reaches a requester; a suppressed aggregate can
be distinguished from a restricted cohort; raw telemetry or AI context is
returned outside policy; an allow/deny mismatch is found; audit evidence
contains protected content; or rollback cannot restore the pre-existing read
path.  The rollback plan disables only the new enforcement path, restores the
legacy read path, preserves non-content audit evidence, and does not mutate
business data or repair historic rows.

## Smallest proposed default-off enforcement slice

After this PDR is accepted and a separate authorization is obtained, the
smallest enforcement slice is a reusable, server-side object-read evaluator
for **contract search results and their contract-search facets only**.  It
would:

1. be committed disabled by default and restricted to a named non-production
   environment and explicit pilot allowlist;
2. evaluate active same-organization Ethical Walls using the direct
   client/matter rules above before serializing a contract or deriving a facet;
3. return generic, content-free deny/empty outcomes and eligible-only totals;
4. leave analytics, telemetry, AI, writes, migrations, permissions, and all
   other search surfaces unchanged; and
5. include an immediate flag-off rollback that restores the exact legacy read
   path without data mutation.

This is still a runtime authorization and result-visibility change when
enabled.  It therefore needs independent Product, Engineering, and Security
GitHub approvals on its immutable implementation SHA, green CI, a documented
rollback drill, and a release/operator record before it is built or activated.

## Required acceptance evidence before implementation

- Accepted PDR status through the repository governance process; no copied
  approval statements or manual approval table.
- A route-to-policy inventory showing every search result, facet, analytics,
  telemetry, and AI context entry point and its source object.
- Tests for unauthenticated access, inactive membership, cross-tenant access,
  ordinary eligible access, client wall, matter wall, inherited matter-client
  wall, expired wall, multiple walls, malformed wall scope, denied metadata,
  facets/totals, role-gated analytics, aggregate suppression, telemetry, AI
  context/redaction, and flag-off legacy parity.
- Content-free audit assertions, exact-SHA green CI, rollback drill results,
  and a named-environment operator/release record where applicable.
- A demonstrated failure path for unavailable policy evaluation that fails
  closed without an object-existence leak.

## Alternatives considered

### Continue tenant-only reads

Rejected as a target policy.  Tenant isolation is necessary but does not meet
the object-level, Ethical-Wall, metadata, or AI-context requirements.

### Add separate checks to every endpoint

Rejected.  That would duplicate sensitive relation logic and allow search,
analytics, and AI to drift again.  The policy needs one reusable server-side
boundary with surface-specific projections.

### Treat any active member as an analytics and telemetry audience

Rejected.  The baseline shows raw query disclosure and inconsistent analytics
gates; membership alone is not a sufficient operations audience.

### Redact opportunistically after AI context retrieval

Rejected.  Retrieval before authorization risks exposure.  Authorization and
retrieval filtering must happen before context construction; unknown
classification fails closed.

## Resolved by Addendum 001

Addendum 001 resolves the aggregate threshold and exception model, AI
classification/redaction boundary, break-glass controls, search-index/facet
semantics, and telemetry schema/retention/legal-basis proposal.  Its
disposition is **Accept for policy scope only**.  It does not authorize
implementation, activation, or any permission, visibility, migration,
telemetry, AI, production, repair, ADMIN, canonical-read, or legacy-retirement
change.

## Remaining implementation risks

1. Adversarial testing is still needed for aggregate differencing and
   high-cardinality joins.
2. The catalogue must be populated and tested across document regions, OCR,
   embeddings, and provider-side retention.
3. Break-glass drills must prove revocation, clock handling, and audit-sink
   failure behavior.
4. Index lag, cache invalidation, and cross-shard policy rechecks need proof.
5. Existing raw telemetry needs a separately authorized privacy inventory;
   this addendum does not alter it.

## Approval

This is a Proposed planning decision.  Its status may change only through the
applicable GitHub PR review and CI evidence on the immutable reviewed SHA.
Acceptance would select a target policy but would not authorize implementation,
activation, permission changes, result-visibility changes, production,
repair, ADMIN authority, canonical-read cutover, or legacy retirement.
