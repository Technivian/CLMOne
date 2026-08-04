# PayrollMinds Pilot Success Criteria

**Status:** Proposed
**Measurement boundary:** Metrics are pilot acceptance evidence, not customer SLAs, commercial commitments or production-readiness claims.

## Minimum successful user outcomes

| Outcome | Proposed acceptance evidence | Failure condition |
|---|---|---|
| Governed ingestion | An authorized user uploads a synthetic approved agreement; it remains unavailable until a clean quarantine verdict; one canonical document/version and provenance-bearing record are released. | Untrusted bytes reach canonical storage, OCR, search, workflow, download or external access before clean verdict. |
| Human verification | An authorized user reviews and verifies required material metadata, with source/provenance and audit evidence. | Suggestion/extraction becomes authoritative without governed human verification. |
| Private access | An eligible named user accesses a record; an ineligible/revoked user cannot discover it through direct URL, search, suggestion, count, notification, export or API. | Any object-level existence or metadata leak. |
| Dates and reminders | Expiry, renewal and notice dates display correctly; reminder creation/delivery/failure/retry evidence is available to the owner. | Reminder is silently lost, sent to an ineligible user, or has no operable failure path. |
| Evidence and export | Authorized owner/admin retrieves audit evidence and a controlled export; the export is logged. | Export bypasses authorization/audit or includes ineligible data. |
| Operations | Isolated pre-production rehearsal demonstrates monitored deployment, backup, restoration, rollback/compensating action and named support response. | Required operator evidence is absent or a drill fails. |

## Proposed acceptance thresholds

- All mandatory go/no-go items pass on the same immutable candidate SHA.
- All in-scope synthetic UAT scenarios pass before any real data is loaded.
- Zero unresolved critical/high findings affecting the pilot scope.
- No scope limit is exceeded: one workspace, 10 named users, 50 initial
  records, three approved agreement types, browser ingestion only, AI off.
- Every required audit action is present and audit integrity verification is
  successful for the exercised pilot workspace.

## Non-success conditions

The following do not count as success: a pleasing UI without server-side
authorization; a feature flag without release authority; a local test without
exact-SHA CI; demo-only evidence; an untested backup script; an AI capability
that was merely configured; or importing real data before privacy, access and
operations evidence is complete.

## End-of-pilot decision

At the end of the approved 30-day window, Product Owner, launch owner and the
applicable release authorities assess the retained evidence against this file,
the Risk Register and the Go/No-Go Checklist. The permitted outcomes are:

1. close and offboard under the charter;
2. continue only through a separately proposed and approved scope/release
   decision; or
3. stop, preserve required evidence and remediate outside the active pilot.

No outcome is pre-approved by this document.
