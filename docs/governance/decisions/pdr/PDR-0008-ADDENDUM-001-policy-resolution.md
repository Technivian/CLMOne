# PDR-0008 Addendum 001: Resolution of policy controls

**Status:** Planning-only addendum; disposition **Accept for policy scope**.
This does not authorize implementation or activation.
**Date:** 2026-07-25
**Owner:** PAR-SEC-002 — `@haroonwahed`, recorded Programme, Product,
Engineering, and Security owner under the Pilot Hardening bootstrap.
**Parent:** [PDR-0008](PDR-0008-object-level-read-enforcement-policy.md)
**Evidence:** PAR-SEC-002 characterization in
`docs/audits/evidence/2026-07-25-par-sec-002-characterization/ROUTE_MATRIX.md`.

## Disposition and boundary

This addendum resolves the five policy questions left open in PDR-0008.  The
disposition is **Accept for policy scope only**: it selects target rules for a
future implementation, but does not create a model, service, migration, flag,
permission, filter, telemetry pipeline, AI redaction, production behavior, or
runtime authority.  PDR-0008 remains non-authorizing until a separately
approved implementation is reviewed and released.

Every implementation remains subject to independent Product, Engineering, and
Security GitHub approvals on the exact implementation SHA, green CI, the
applicable default-off/reversible controls, and a named operator or release
record.  A flag cannot grant authority.

## 1. Analytics aggregate suppression

**Default rule.**  Every analytics metric, facet bucket, percentile, and
pagination total is calculated only from objects the requester may read under
the object policy.  Suppress a metric or bucket when fewer than **five**
eligible source objects contribute.  The response must not disclose the hidden
count, identity, or whether the cause was a wall or a small cohort.

**Exceptions.**  No per-user bypass exists.  A different threshold or a
statutory/reporting exception requires a separately accepted Product/Security
policy, a named purpose, a bounded audience, and evidence that differencing
queries cannot reconstruct a restricted cohort.  Workspace managers do not
receive an implicit exception.

**Fail closed.**  If eligibility, cohort size, policy version, or aggregate
computation is unavailable or inconsistent, return a generic unavailable/empty
result and do not return the unfiltered aggregate.

**Audit evidence.**  Record policy version, metric class, suppression category,
coarse reporting window, and an opaque correlation.  Do not log source IDs,
titles, query text, hidden counts, or restricted metadata.

**Rollback/disablement.**  Disable the new analytics projection and return a
generic unavailable result until a policy-safe path is restored; never roll
back to an unfiltered aggregate.  Preserve the content-free audit evidence.

**Unresolved risks.**  Repeated-query differencing, high-cardinality buckets,
small changes over time, and joins across independently suppressed metrics can
still create inference risk and require test fixtures before implementation.

## 2. AI classification and redaction catalogue

**Default rule.**  AI context is built only after object authorization and a
versioned field/document classification lookup.  Unclassified, wall-restricted,
or indeterminate content is excluded; if exclusion cannot be proven, the AI
request receives no context.  Redaction occurs before prompt construction and
provider submission.  AI remains non-authoritative.

**Exceptions.**  An explicit, time-bounded AI policy may allow a classified
`INTERNAL` field for a named use case and audience when the object is otherwise
eligible.  `CONFIDENTIAL` and `RESTRICTED` fields remain excluded unless a
future policy explicitly authorizes a redaction rule; a user prompt never
overrides classification or an Ethical Wall.

**Fail closed.**  Missing catalogue entry, stale catalogue version, failed
redaction, wall match, tenant mismatch, or provider-context uncertainty means
no object context is sent.  The external response contains no field name,
value, title, or wall reason.

**Audit evidence.**  Record the AI use case, policy and catalogue versions,
redaction outcome category, model request correlation, and reviewer state.  Do
not record prompt, source text, redacted value, or restricted identifier.

**Rollback/disablement.**  Disable the affected AI use case or context builder
and use the existing AI kill switch; do not fall back to unfiltered retrieval.
Previously stored AI suggestions are not repaired or reclassified by this
addendum.

**Unresolved risks.**  Catalogue completeness, document-region extraction,
embedded images/OCR, derived embeddings, provider-side retention, and leakage
through model error messages remain implementation risks.

## 3. Break-glass access

**Default rule.**  Break-glass is unavailable.  Normal object policy and
Ethical Wall denial apply to every requester.

**Exceptions.**  A future incident-only grant may be issued to an existing
workspace owner or administrator who is not the restricted subject, or to a
security incident responder named in the release/operator record.  It must be
limited to one workspace, named object/surface, and one incident; require two
independent approvers (Product and Security, with Engineering review when a
technical control is changed); carry a reason and ticket; expire automatically
after **30 minutes**; and be non-renewable without a new approval.  It cannot
grant ADMIN authority, change permissions, export data, or bypass tenant
isolation.

**Fail closed.**  Missing approver identity, incident ticket, scope, expiry,
clock, or audit sink denies the grant.  An expired or revoked grant is denied
immediately; there is no grace period.

**Audit evidence.**  Record requester, approvers, workspace, opaque object
scope, purpose/ticket, policy version, issued/expiry/revocation events, and
outcome.  The audit record is restricted to authorized security/audit readers
and contains no contract content.

**Rollback/disablement.**  Revoke the grant, invalidate associated sessions or
tokens, and disable the break-glass mechanism.  If revocation cannot be
confirmed, fail closed for the affected surface and open an incident.

**Unresolved risks.**  Insider misuse, compromised administrator credentials,
clock skew, approver collusion, and audit-sink outage require operational
drills and incident-response ownership before any grant exists.

## 4. Search-index and facet semantics

**Default rule.**  Search results, suggestions, facets, totals, and ranking
signals are computed only from objects that pass the current object policy.
The index may store tenant/object references, but the request path must apply a
current policy check before serialization.  An index snapshot with stale wall,
membership, or classification state is not authoritative for access.

**Exceptions.**  A health or rebuild diagnostic may report content-free job
status and error categories to operators, never user-facing results or counts.
No cached result, saved view, semantic index, or facet has an access bypass.

**Fail closed.**  If the index cannot apply current tenant and object policy,
the system must recheck against an authoritative policy-safe source or return
a generic unavailable/empty result.  It must not return an unfiltered hit,
facet, count, URL, or existence signal.

**Audit evidence.**  Record index snapshot/version, policy version, stale-state
category, fallback outcome, and opaque correlation.  Do not log query text or
restricted result data.

**Rollback/disablement.**  Disable the affected index/facet path and route to
a policy-safe source or generic unavailable response.  Never restore the old
unfiltered index path as a rollback.

**Unresolved risks.**  Index lag, delete/revoke propagation, cache invalidation,
cross-shard joins, ranking leakage, and facet reconstruction attacks require
load and adversarial tests.

## 5. Telemetry fields, retention, and legal basis

**Default rule.**  PAR-SEC-002 telemetry is content-free and operational only.
Allowed fields are route surface, standardized event category, actor class,
outcome category, policy version, and coarse UTC reporting window.  It excludes
raw queries, prompts, result counts tied to a query, contract/document/client
IDs, titles, field values, and response content.  The telemetry endpoint is
manager/security-operations-only and returns aggregates, not event rows.

Retain content-free event records for **30 days**, then retain only daily
aggregates for **90 days** before deletion.  The proposed legal basis is
legitimate interest in security operations and service reliability, subject to
workspace notice, DPA/privacy review, purpose limitation, and documented
retention policy.

**Exceptions.**  A documented security incident or legal hold may preserve
content-free records for up to **90 additional days**, limited to the incident
scope and approved by Security and Privacy.  It may not restore or collect raw
query/prompt content.  Existing historical raw telemetry is outside this
addendum and is not deleted, repaired, or reclassified by it.

**Fail closed.**  If field minimization, retention classification, audience
checks, or legal-basis configuration is unavailable, do not emit or return
telemetry; the product request itself must not fall back to raw telemetry.

**Audit evidence.**  Record telemetry-policy version, aggregate window,
retention action, audience decision, and exception/hold correlation without
content or object identifiers.

**Rollback/disablement.**  Disable telemetry emission and endpoint access while
preserving product behavior.  Restore only the approved content-free schema;
never roll back to raw-query exposure.

**Unresolved risks.**  Existing raw records may have different legal bases,
workspace notice coverage, deletion propagation, and operational usefulness;
these require a separate privacy inventory and retention execution plan.

## Implementation boundary

The smallest separately authorized slice remains a default-off, non-production,
named-environment and allowlisted evaluator for contract-search results and
contract-search facets only.  It must enforce current tenant plus the accepted
Ethical-Wall rule before serialization and facet derivation, return eligible-only
results/counts with generic fail-closed outcomes, and disable cleanly without
falling back to an unfiltered path.  Analytics, telemetry, AI, break-glass,
migrations, permissions, production behavior, repair, ADMIN authority,
canonical reads, and legacy retirement remain outside that slice.

## Policy disposition

**Accept for policy scope only.**  The five policy questions are resolved above;
the remaining risks are implementation and operations prerequisites, not an
authorization to build or activate.  Acceptance of this addendum must be
recorded through the applicable GitHub PR evidence on its immutable SHA.
