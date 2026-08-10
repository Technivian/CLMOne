# PayrollMinds expanded production scope change

**Status:** Product Owner business-scope direction recorded — no technical
activation, merge, deployment, feature activation, customer-data import, or
production use is authorized by this document. The immutable-SHA GitHub
review, CI, and release/operator gates remain mandatory.

**Repository baseline inspected:** `origin/main` at
`2b1fe6da1431ed4d63b0afe226d404e4af4aced7` (fetched 2026-08-09).

**Decision requested:** PayrollMinds requires CLM One beyond the initial
three-type controlled scope. This package proposes a staged, evidence-led
expansion; it does not remove restrictions or turn on a route.

**Authority required before technical implementation:**
[`PDR-0013: PayrollMinds Expanded Production Contract Scope`](../../governance/decisions/pdr/PDR-0013-payrollminds-expanded-production-contract-scope.md)
records the Product Owner's business-scope direction. Its PDR status remains
Proposed until the applicable GitHub decision evidence exists; in either case,
this package remains non-authorizing for permission changes, exposure, and
production activation until the individual technical gate is complete.

## 1. Authority and scope-record reconciliation

The active Governance Charter, canonical domain model, engineering guardrails,
and security architecture remain controlling. In particular, contract type is
a governed classification, server-side authorization is required, provenance
and immutable document versions are mandatory, audit is append-only, and a
feature flag grants no release authority.

There is a material source conflict that must be resolved in the authorizing
PDR/PR before any activation:

| Source | Three types stated | Authority/status | Consequence |
| --- | --- | --- | --- |
| This change request | MSA, NDA, DPA | Product Owner request | Treats Order Confirmation and all other types as excluded pending this amendment. |
| `PILOT_SCOPE.md` and `PILOT_CHARTER.md` on the inspected remote baseline | MSA, Order Confirmation, Mutual NDA | Proposed pilot records | Does not authorize activation and conflicts with the requested current-state statement. |
| `PDR-0011` on the inspected remote baseline | MSA, Order Confirmation, Mutual NDA | Proposed | Does not resolve the conflict. |

No code or configuration may select one list by implication. The approving
PDR must state the exact superseded scope record and its effective date. Until
then, the more restrictive intersection is the safe operational position:
**MSA and NDA only**. DPA and Order Confirmation must not be considered
approved merely because one source names them.

### Mandatory access-policy dependency

PDR-0013 business-scope direction does not cure the workspace-wide access
model. The required sequence is:

> PDR-0013 business scope → PDR-0008 approval package → separately authorized
> shared access implementation → per-type technical activation gate.

See [PDR-0008 Addendum 002](../../governance/decisions/pdr/PDR-0008-ADDENDUM-002-payrollminds-private-contract-access-approval-package.md)
and the [private-by-default impact assessment](PRIVATE_BY_DEFAULT_ACCESS_CHANGE_IMPACT.md).
Order Confirmation and Purchase Order remain **BUSINESS SCOPE APPROVED /
TECHNICAL ACTIVATION BLOCKED**.

## 2. Actual-product inventory

### 2.1 What the code represents

`Contract.ContractType` contains 21 persisted enum codes. The governed
`ContractType` catalogue mirrors those codes; `contract_type` remains a
transitional denormalized mirror. The generic form reads active catalogue
entries, so a visible picker is not evidence that a type has a complete,
approved lifecycle.

The terms **Custom agreement** and **Generic/upload-based agreement** are not
enum codes. They are represented, respectively, by `OTHER` and by origin/path
(`UPLOAD`, ingestion release, legacy Upload & Review, or CSV/import), and must
not be turned into new types without a decision record.

Legend: **Yes*** = available on ordinary remote-main routes when
`CONTROLLED_PILOT_ENABLED=false`; this is not pilot permission. **Config** =
only launch-copy/routing metadata or a generic workflow selection, not proof of
a type-specific published workflow. **Audit** = a creation/provenance audit
path exists; it is not evidence of the full required type acceptance pack.

| Contract type/path | Exists | Currently exposed | Pilot allowed | Workflow | Export | Audit | Security tests | Browser tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MSA | Enum, catalogue, dedicated builder | Yes*; dedicated `/contracts/new/msa/` | Disputed; request says Yes | Dedicated MSA route; finance threshold | Activity export only; no type export | Audit | MSA/pilot coverage exists, not complete production evidence | No type-specific browser proof found |
| NDA | Enum, catalogue, dedicated builder | Yes*; dedicated `/contracts/new/nda/` | Yes in all stated lists | Dedicated NDA route | Activity export only | Audit | NDA/pilot coverage exists | No type-specific browser proof found |
| DPA | Enum, catalogue, dedicated builder | Yes*; dedicated `/contracts/new/dpa/` | Disputed; request says Yes, remote proposal says No | Dedicated DPA/privacy route | Activity export only | Audit | DPA and pilot coverage exists | No type-specific browser proof found |
| Order Confirmation | Enum, catalogue, procurement card | Yes*; card → generic create | Disputed; remote proposal says Yes, request says excluded | Config: commercial review; generic workflow selection | Activity export only | Audit | No per-type security pack found | No |
| SOW | Enum, catalogue, recommended card | Yes*; card → generic create | No | Config: commercial review; generic workflow selection | Activity export only | Audit | No per-type security pack found | No |
| Purchase Order / PO | Enum, catalogue, procurement card | Yes*; card → generic create | No | Config: commercial review; generic workflow selection | Activity export only | Audit | No per-type security pack found | No |
| Vendor agreement | `VENDOR` enum/catalogue, supplier card | Yes*; card → generic create | No | Config: procurement + legal; high-risk routing | Activity export only | Audit | No per-type security pack found | No |
| Custom agreement | `OTHER` enum/catalogue | Yes*; card/dropdown → generic create | No | General counsel/custom drafting route | Activity export only | Audit | No per-type security pack found | No |
| Generic/upload-based agreement | `UPLOAD` provenance and ingestion models/routes; not a type | APIs exist but default-off; legacy Upload & Review exists | No | No workflow is created by clean release | Activity export only | Ingestion, provenance and version events | Ingestion and pilot security coverage exists, but not per proposed type | No end-to-end browser path found |
| Non-Compete / Non-Solicitation | Enum/catalogue | Yes*; dropdown only | No | Generic workflow; extra date metadata | Activity export only | Audit | No per-type security pack found | No |
| Subcontractor SOW | Enum/catalogue | Yes*; dropdown only | No | Commercial config | Activity export only | Audit | No per-type security pack found | No |
| Consulting / Independent Contractor | Enum/catalogue | Yes*; dropdown only | No | Generic workflow; extra date metadata | Activity export only | Audit | No per-type security pack found | No |
| Employment | Enum/catalogue | Yes*; dropdown only | No | High-risk routing; extra date metadata | Activity export only | Audit | No per-type security pack found | No |
| Lease | Enum/catalogue | Yes*; dropdown only | No | High-risk routing; extra date metadata | Activity export only | Audit | No per-type security pack found | No |
| License | Enum/catalogue | Yes*; dropdown only | No | High-risk routing | Activity export only | Audit | No per-type security pack found | No |
| SaaS agreement | Enum/catalogue, recommended card | Yes*; card → generic create | No | Security/data-processing review copy; generic workflow selection | Activity export only | Audit | No per-type security pack found | No |
| Terms of Service / Terms & Conditions | Enum/catalogue | Yes*; dropdown only | No | Generic workflow | Activity export only | Audit | No per-type security pack found | No |
| Partnership | Enum/catalogue | Yes*; dropdown only | No | High-risk routing | Activity export only | Audit | No per-type security pack found | No |
| Referral / Reseller / Channel Partner | Enum/catalogue | Yes*; dropdown only | No | Commercial config | Activity export only | Audit | No per-type security pack found | No |
| Settlement | Enum/catalogue | Yes*; dropdown only | No | Dispute-counsel config and high-risk routing | Activity export only | Audit | No per-type security pack found | No |
| Amendment | Enum/catalogue, recommended card | Yes*; card → generic create | No | Parent-link/reuse guidance; requires content | Activity export only | Audit | No per-type security pack found | No |
| BAA | Enum/catalogue | Yes*; dropdown only | No | Generic workflow; no dedicated privacy configuration | Activity export only | Audit | No per-type security pack found | No |

### 2.2 Intake-path inventory

| Path | Current behavior | Controlled-pilot behavior | Classification |
| --- | --- | --- | --- |
| `/contracts/new/start/` | Template picker; cards for MSA, NDA, DPA, SOW, Vendor, PO, Order Confirmation, SaaS, Amendment and Other; full form has active catalogue dropdown | Allowed, but cards for generic paths can lead to a redirect | Pilot restriction plus UI consistency defect |
| `/contracts/new/msa/`, `/nda/`, `/dpa/` | Dedicated builders | Allowed by middleware allowlist | Scope restriction; DPA allowance conflicts with remote scope documents |
| `/contracts/new/?type=<code>` | Generic form can create every active catalogue type | Redirected by `ControlledPilotScopeMiddleware` | Pilot scope restriction, not authorization |
| `/contracts/new/upload/` + `/api/documents/upload/` | Legacy direct Upload & Review path; can create a contract while quarantine enforcement is off | UI route redirected; API needs separate gate verification | Class C legacy/alternate upload; do not activate |
| `/api/documents/ingestion/…/release/` | Default-off, quarantine-first clean release; may create `Contract` + `Document` + immutable `DocumentVersion` with `UPLOAD` provenance | Available only with named environment/org/scanner controls; not type-limited | Candidate governed upload path, but needs per-type tests and workflow handoff |
| `/contracts/repository/import/` | Default-off owner/admin CSV dry-run, commit and archive-only compensating rollback | Not explicitly pilot-allowed; flag required | Separate import behavior; no documents; Class C until remediation |
| `/api/integrations/import/{csv,json}/` and inbound/integration services | Alternate integration/import routes exist | Not explicitly denied by type middleware; integration remains out of scope | Class C; keep default-off/excluded |

The only controlled export identified for the bounded path is workspace
activity export (`/contracts/organizations/activity/export/`), restricted to
workspace owners/admins and audit-logged. It is not a type-specific contract
or document export and cannot satisfy the expanded-scope export gate alone.

## 3. Risk classification and proposed scope

### 3.1 Classification of currently excluded types

No excluded type is Class A today. The shared model is necessary but not
sufficient: the repository lacks per-type evidence for workflow, private
search, export, audit and browser behavior.

| Class | Types/paths | Basis | Required disposition |
| --- | --- | --- | --- |
| B — configuration/workflow difference | Order Confirmation, SOW, Purchase Order, Vendor, SaaS, Amendment, Subcontractor SOW, Reseller, Non-Compete, Consulting, Employment, Lease, License, Terms of Service, Partnership, Settlement, BAA | They use the canonical `Contract` classification and generic form, but vary in required fields, high-risk/privacy/commercial routing, or lack a defined type workflow/metadata pack. | Do not activate until the exact metadata, workflow version, route and per-type evidence are approved. |
| C — separate or legacy behavior | `OTHER`/Custom, generic Upload & Review, quarantine release until workflow handoff is added, repository CSV import, integration CSV/JSON/inbound paths | `OTHER` is an explicit unmapped bucket; uploads/imports have distinct paths, and some create no workflow or have default-off/alternate controls. | Do not enable merely for breadth. Remediate and separately approve canonical provenance, authorization, document/version, audit, export and rollback behavior. |

### 3.2 Proposed activation scope (not authorization)

The smallest sensible first technical cohort is **Order Confirmation and
Purchase Order**. Both share the generic commercial route and identical
baseline required fields (`counterparty`, `governing_law`, `jurisdiction`).
They still require independent evidence because their browser entry and
business controls are distinct. Under PDR-0013's Class A/B/C taxonomy, this
is the first narrow cohort within **Batch 2**, not a populated Batch 1: no
Class A type was found.

**Later Batch 2 cohort:** SOW and Vendor Agreement, after the first cohort's
evidence is accepted.
SOW needs its own scope/deliverable metadata and relationship decision; Vendor
Agreement needs procurement routing and the high-risk path.

**Later Batch 2 cohort:** SaaS and Amendment, after explicit Security/Privacy and
parent-agreement/approval-reset decisions, respectively.

All remaining enum types, `OTHER`/custom, generic upload, CSV/import and
integration paths remain excluded. They are not silently included by a phrase
such as “full CLM usage.”

### 3.3 Affected areas for each proposed batch

| Area | First technical cohort (PDR-0013 Batch 2): Order Confirmation, PO | Later PDR-0013 Batch 2 cohort: SOW, Vendor | Later PDR-0013 Batch 2 cohort: SaaS, Amendment |
| --- | --- | --- | --- |
| Data and storage | Contract type catalogue binding; required metadata; canonical document/version if a document is attached | Add scope/deliverable or supplier metadata only through approved definitions; preserve document provenance | Security/data-processing fields or parent relationship; no new property without governance |
| Users and permissions | Existing workspace roles; owner/private access; no new role | Same | Same |
| Workflow | Published immutable workflow/version and transition tests | Commercial/procurement workflow and high-risk branch evidence | Security/privacy or amendment/approval-reset workflow evidence |
| Audit and export | Create, type assignment, workflow, document, access and export events | Same | Same |
| Privacy | Metadata minimization; no AI | Assess supplier/SOW data flags | Security/data-processing and amendment history need specific review |
| Operations | Named-environment release, support, rollback and observation record | Same | Same |

## 4. Controls explicitly unchanged

Every batch preserves, without exception:

- workspace/tenant isolation and private-by-default contract access;
- server-side authorization, including cross-workspace and revoked-access
  denial;
- locked provenance and immutable `DocumentVersion`;
- append-only audit and controlled, logged export;
- AI default-off and non-authoritative requirements;
- inbound email default-off;
- signatures and external integrations default-off;
- production security controls, retention/privacy obligations, and release
  evidence requirements.

The middleware is an exposure control only. It must not be weakened to bypass
object-level authorization, quarantine, export controls, or privacy gates.

## 5. Restriction register: route, UI, flag, and security distinction

| Subject | Route/UI action | Middleware/flag condition | Backend security behavior | Classification |
| --- | --- | --- | --- | --- |
| Order Confirmation, SOW, PO, Vendor, Custom/Other | Cards or dropdown resolve to `/contracts/new/?type=<code>` | Pilot middleware rejects freeform `/contracts/new/` and all non-builder `/contracts/new/*` | Generic form has tenant-scoped owner/relations and required-field validation, but this is not an activation gate | Pilot scope restriction; no type-specific security authorization change |
| MSA/NDA/DPA dedicated paths | Dedicated builder cards | Allowlisted `/contracts/new/{msa,nda,dpa}` when pilot flag is on | Existing contract/workflow permissions still apply | Pilot scope restriction; not proof of release authorization |
| Upload & Review / generic upload | Dashboard/legacy Upload & Review, `/contracts/new/upload/` | Pilot middleware redirects UI path; quarantine/integration flags are independently default-off | Direct API and enforcement state must apply repository/action checks; legacy behavior is not approved | Both scope restriction and a real ingestion/security limitation |
| Quarantine intake/release | Ingestion APIs only; no approved browser journey | `DOCUMENT_QUARANTINE_*` environment, org allowlist, scanner and abort controls | Private attempt access; clean verdict; atomic canonical release; provenance/version/audit | Real security control; not removed by this amendment |
| CSV repository import | Repository Import CSV action | `REPOSITORY_CSV_IMPORT_ENABLED`; owner/admin only | Signed preview, workspace binding, archival compensating rollback; no documents | Separate import product path; excluded pending evidence |
| Integration/inbound import | API/service paths | Integration configuration and feature controls; no type middleware rule | Must not bypass tenant, provenance or audit controls | Actual product/security limitation and excluded capability |
| Search/repository/export | Contracts, search and activity export | Not restricted by type; repository/search enforcement has separate controls | Policy-filtered querysets and owner/admin export control | Security control, never a pilot-type toggle |

## 6. Per-type activation gate

No additional type reaches a named environment until its own row is complete
on the immutable candidate SHA. Reuse may be asserted only by demonstrating
the same endpoint, application service, configuration version, authorization
policy and browser path; a shared enum is not sufficient.

Required evidence for **each** activated type:

1. Authorized typed intake/create path, including invalid type rejection.
2. Canonical `Contract` and governed catalogue binding.
3. Correct `Document` and immutable `DocumentVersion` where a file is used.
4. Locked provenance with actor, source and correlation evidence.
5. Owner/private default plus unauthorized-user and cross-workspace denial.
6. Search, counts and facets non-disclosure.
7. Immutable workflow version, correct routing, required metadata and rejected
   invalid transition.
8. Append-only audit events for creation, material transition and export.
9. Permission-controlled export with an export audit event.
10. A browser happy path and isolation cleanup in a disposable test workspace.
11. A documented rollback/removal: hide new entry, stop launch, retain records
    and audit, and use only a compensating/archive action where applicable.

## 7. Automated acceptance plan

The following is the required test implementation plan. “Not ready” is
intentional: it prevents a configuration flip before coverage exists.

| Type | Unit | Security | Workflow | Browser | Export | Audit | Ready? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Order Confirmation | Add required-field/catalogue/create tests | Owner, member, outsider, revoked-user, cross-workspace and search tests | Published commercial route plus invalid transition | New request → record/document → review in isolated workspace | Authorized/denied export | Create/type/workflow/export event assertions | No |
| Purchase Order | Same, independently parameterized | Same, independently parameterized | Same commercial route; prove configuration binding | Same | Same | Same | No |
| SOW | Scope/deliverable metadata and catalogue tests | Same isolation/search suite | SOW route and parent-relationship decision test | Same | Same | Same | No |
| Vendor Agreement | Procurement metadata/risk tests | Same isolation/search suite | Procurement/legal and high-risk route | Same | Same | Same | No |
| SaaS Agreement | Security/data-processing metadata tests | Same isolation/search suite | Security/privacy route | Same | Same | Same | No |
| Amendment | Parent relation and content-required tests | Same isolation/search suite | Approval-reset/parent-reuse behavior | Same | Same | Same | No |
| Custom (`OTHER`) | Do not add activation tests; add only guard tests | Verify unmapped values remain `OTHER` and unavailable | N/A | N/A | N/A | N/A | No — Class C remediation required |
| Generic/quarantine upload | Clean/reject/scan-error/release tests | Uploader/admin only, cross-workspace denial and abort-state tests | Add explicit workflow-handoff test before activation | Add end-to-end browser journey before activation | Export test after contract/document export design | Quarantine, release, provenance/version events | No — Class C remediation required |
| CSV/inbound/integration import | Existing behavior regression only | Denial/default-off tests | N/A until approved | N/A | N/A | Import audit only | No — excluded |

Test fixtures must use disposable isolated workspaces, no PayrollMinds or
customer data, and must remove/archive only fixture data under the test
transaction or explicit compensating cleanup. Add Playwright coverage to the
repository's browser manifest rather than relying on a manual walkthrough.

## 8. Implementation sequence and release gate

1. **Resolve authority:** accept PDR-0013, which reconciles the conflicting
   three-type lists and names the exact first technical cohort. No code change
   yet.
2. **Close configuration gaps:** create/approve immutable workflow versions
   and governed metadata definitions; do not add ad hoc types, fields, roles,
   statuses or permissions.
3. **Implement tests before exposure:** land each complete Batch 1 acceptance
   pack with flags default-off. Correct the picker so controlled-pilot users
   do not see cards that lead only to a scope redirect.
4. **Validate release evidence:** product, architecture, security/privacy,
   quality and operations evidence on the exact unchanged SHA, including
   backup/restore, operator abort and rollback controls.
5. **Activate one batch only after the applicable gate:** production activation
   requires independent Product, Engineering and Security GitHub approvals,
   green CI for the immutable reviewed SHA, and a release record. Observe in
   the named environment, then proceed to the next batch only through a new
   evidence decision.

Rollback never deletes customer records, immutable document versions or audit
evidence. It disables only new entry/launch exposure, preserves access and
audit controls, and uses the approved compensating/archive procedure for data
created by a reversible import path.

## 9. Decision required

Approve, amend, or reject this proposed package through the applicable GitHub
review and decision-record process. The first approval must explicitly answer:

1. Which conflicting existing three-type list is superseded?
2. Is the first PDR-0013 Batch 2 technical cohort exactly Order Confirmation
   and Purchase Order, or is a different narrow list required?
3. Which approved workflow versions and metadata definitions govern each
   Batch 1 type?
4. What contract/document export path meets the expanded-scope export gate?

Until those answers and the type-specific evidence exist, every additional
type and every Class C intake path remains disabled for PayrollMinds.
