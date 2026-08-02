# PayrollMinds Production Pilot Charter

**Status:** Proposed — approval and activation evidence not supplied
**Proposed owner:** CLM One Product Owner (named approver to be recorded on the authorizing GitHub record)
**Proposed duration:** 30 days from approved controlled production activation
**Authority:** This charter is subordinate to the active Governance Charter and accepted decision records. It does not authorize production activation.

## Purpose

Prove one narrow, governed outcome: PayrollMinds can ingest approved agreement
files, create provenance-bearing contract records, verify material metadata,
find only authorized records and dates, receive reminders, and retrieve audit
evidence. This is not a general enterprise release.

## Proposed pilot boundary

| Boundary | Proposed rule |
|---|---|
| Workspace | One isolated PayrollMinds workspace in an isolated production environment. |
| Users | At most 10 individually named, invited and active users. The approved user list is not yet supplied. No shared accounts, service accounts acting as humans, or external users. |
| Workspace permissions | Use existing workspace roles only: `OWNER`, `ADMIN`, and `MEMBER`. No new role, permission, status or lifecycle vocabulary is introduced. Workflow responsibilities remain distinct from workspace permission. |
| Contract types | At most three types: Master Services Agreement, Order Confirmation, and Mutual NDA. This proposed selection is a scope limit, not a PayrollMinds commitment. A different selection requires approved scope amendment before ingest. |
| Volume | At most 50 initial contract records. No additional bulk load without approved scope amendment and capacity evidence. |
| Data | Contract documents and contract metadata only, as classified in [DATA_CLASSIFICATION.md](DATA_CLASSIFICATION.md). |
| Input | Manual upload and bulk upload after the approved quarantine-first ingestion gate is active. Email forwarding remains disabled. |
| AI | Disabled (`GEMINI_AI_ENABLED=false`). No provider receives PayrollMinds documents or metadata. |
| Access | Private by default. Each record/document read, search result, count, export and AI context must satisfy the approved server-side object-read policy; workspace membership alone is insufficient. |
| Support | One named launch owner and one documented support channel, both to be supplied before activation. No 24/7, SLA, legal-advice or customer-success commitment is created by this charter. |

## Allowed data

Only the data classes in the Allowed column of the data-classification record
may enter the pilot. The minimum necessary contract file and related metadata
may be processed solely to operate the pilot. Provenance, verification,
access, reminder and audit metadata are allowed when they are content-minimized
and access-controlled.

## Prohibited data

Raw payroll files, salary/compensation data, employee or worker bulk records,
bank, tax, benefits, identity-verification, credential, special-category
personal data, and any data outside an approved agreement/document purpose are
prohibited. A prohibited-data or suspected-malicious upload is a stop condition,
not a data-cleanup task for an ordinary user.

## Feature exclusions

- email forwarding and all unproven integrations;
- AI extraction, summarisation, drafting, semantic search and autonomous
  decisions;
- external collaboration/portals;
- e-signature, advanced negotiation/redlining and signature automation;
- SAML, SCIM and broad identity provisioning;
- advanced analytics and enterprise reporting;
- payroll calculation, HRIS/payroll-system access and employee-data handling.

## Retention assumptions

No PayrollMinds retention, deletion, offboarding or legal-hold commitment is
approved by this charter. Before real data is accepted, the workspace must have
an approved retention policy, legal basis, deletion/offboarding procedure,
export procedure, data-location record and responsible owner. In their absence,
real data must not be loaded. Quarantine retention and released-document
retention remain separate under ADR-0016.

## Stop conditions

Immediately stop upload, access expansion or pilot operation and preserve
content-minimized evidence if any of the following occurs:

- a cross-workspace, object-level or revoked-access denial fails;
- restricted metadata appears in search, counts, notification, export, logs or
  an AI/integration context;
- quarantine, malware/type validation, storage privacy or provenance control
  fails or becomes unavailable;
- prohibited data is submitted or suspected;
- AI, email forwarding, external sharing or a deferred integration is enabled;
- audit integrity fails, a required audit event is missing, or backups/restores
  cannot be evidenced;
- release SHA, CI, environment, scope, user count, contract-type or volume
  limits diverge from the approved record; or
- a material privacy, security or operational incident is declared.

The launch owner pauses the affected capability, records the incident through
the approved operational process, and seeks Product, Engineering and Security
direction. A feature flag does not itself authorize restart.

## Pilot end and offboarding

At the approved pilot end date, stop new ingestion and disable pilot-only
exposure. The launch owner must reconcile the contract/document inventory,
authorized users, audit evidence, exports, open reminders, retention/legal
holds and unresolved incidents. Provide any approved customer export through a
permission-controlled, logged path. Retain or delete data only under the
approved retention/legal-hold policy and record the operator outcome. Access
must then be revoked, pilot flags returned to their approved default state, and
a closure/go-no-go decision recorded through GitHub and operator evidence.

## Approval

Proposed only. Approval, named users, launch owner, support channel, retention
terms and production activation must be evidenced separately; none are implied
by this document.
