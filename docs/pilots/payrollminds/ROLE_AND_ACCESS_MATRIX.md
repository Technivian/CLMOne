# PayrollMinds Pilot Role and Access Matrix

**Status:** Proposed
**Authority boundary:** Existing workspace roles are used. This document does not create a role, permission, entitlement or workflow authority and cannot compensate for missing server-side object-read enforcement.

## Workspace roles

| Existing role | Pilot assignment | Permitted pilot activities after object-read enforcement | Not permitted by this matrix |
|---|---|---|---|
| `OWNER` | Maximum one named launch/business owner; identity TBD | Workspace administration, user approval within existing policy, controlled export, audit review, pilot closure. | Bypass object-read policy, approve own release, waive critical security controls, change retention without authority. |
| `ADMIN` | Named administrators only; identities TBD | Workspace configuration within approved pilot scope, named-user administration, record operations permitted by existing server-side checks, audit/support triage. | Grant new permissions/roles, bypass object-read policy, activate excluded features, approve production release. |
| `MEMBER` | Named contract users only; identities TBD | Read/edit/review only on records explicitly eligible under the future object-read policy and existing action checks; create/verify metadata where separately authorized. | Workspace administration, role management, controlled export, access to ineligible records, AI, external sharing. |

## Required access controls

| Control | Required pilot behaviour | Evidence needed |
|---|---|---|
| Authentication | Individually named accounts; no shared credentials; session controls active. | User inventory, session/security tests and operator check. |
| Membership | Active membership in the dedicated workspace is necessary but not sufficient. | Invite/activation/deactivation audit evidence. |
| Object read | Contract/document/metadata/search/count/export/AI access is private by default and evaluated server-side. | Accepted PDR-0008 implementation, negative tests and activation record. |
| Object write | Existing server-side action checks plus owner/accountability rules apply; no client-side-only controls. | Route/service tests and audit evidence. |
| Revocation | Deactivation or object-access removal immediately prevents subsequent read, search, download, export and reminder assignment access. | Revocation regression and production smoke evidence. |
| Export | Owner/admin only under existing policy, purpose-bound and logged; no bulk export beyond approved scope. | Authorization, logging and operator evidence. |
| Audit | Authentication where available, creation, upload/release, verification, access where required, permission change, export, reminder and administration actions are recorded. | Audit coverage/integrity evidence. |

## Separation of responsibilities

Workspace permission is not a workflow role. Contract owner, reviewer,
approver, privacy reviewer and signer are process responsibilities, not new
workspace roles. The pilot does not activate signature, advanced approval or
external workflow authority. Release approval remains governed by the active
Charter and must not be performed by a person merely because they are a
workspace owner or administrator.

## Access provisioning and removal

Before activation, the launch owner must provide the proposed named-user list,
role justification, least-privilege rationale and removal contact. Each
provision/change/removal is server-side, auditable and tested. At pilot end or
on stop, remove access first, then perform approved export/retention actions.
