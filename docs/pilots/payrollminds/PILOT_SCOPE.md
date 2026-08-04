# PayrollMinds Pilot Scope

**Status:** Proposed
**Related:** [Pilot Charter](PILOT_CHARTER.md), [Success Criteria](SUCCESS_CRITERIA.md), [Go/No-Go Checklist](GO_NO_GO_CHECKLIST.md)

## In scope

| Capability | Boundary | Required evidence before use |
|---|---|---|
| Workspace | One isolated PayrollMinds workspace, maximum 10 named users. | Approved user list; server-side membership and object-read tests. |
| Agreement types | MSA, Order Confirmation and Mutual NDA only; maximum 50 initial records. | Approved type list and synthetic UAT for each used type. |
| Ingest | Manual and bulk browser upload only. | ADR-0016 gate active, private quarantine storage/scanner evidence, generic failure states. |
| Contract records | Imported records may become durable records without workflow origin, but provenance is mandatory. | Provenance, document-version and tenant isolation tests. |
| Metadata | Entered or extracted as non-authoritative suggestions and verified by an authorized human. | Verification audit evidence and reviewer authorization. |
| Search and dates | Authorized contract search/filtering, effective/expiry/renewal/notice dates and reminders. | Object-read, count/facet, reminder failure/retry and access-revocation tests. |
| Evidence | Authorized audit inspection and controlled export. | Append-only/integrity proof, export authorization and export audit event. |

## Explicitly out of scope

- payroll or employee-data processing;
- email forwarding, APIs, webhooks, Salesforce, NetSuite and other large integrations;
- AI of any kind, including provider calls and semantic retrieval;
- external users, collaboration portals and e-signature;
- SAML/SCIM, automated provisioning and advanced groups;
- advanced negotiation, redlining, analytics and broad reporting;
- changes to roles, permissions, lifecycle stages, contract types, core domain
  objects, or canonical workflow authority.

## Scope-control rules

1. A page, model, flag, route or existing code path is not approval to use it.
2. A change may only close a named blocker in the readiness report or this
   package; scope expansion requires a proposed amendment and applicable
   approval.
3. No real data is loaded before every applicable go/no-go item is evidenced.
4. No production deployment, feature activation, data import, security-risk
   acceptance or PR merge is authorized by this document.
5. The pilot remains stopped when a stop condition in the charter occurs.

## Scope change procedure

The Product Owner records a proposed change with the affected data, users,
permissions, operational impact, test/rollback plan and required decision
record. It becomes effective only after the appropriate GitHub review, exact
SHA CI and operator/release evidence required by the active Charter.
