# PayrollMinds data export, offboarding, and deletion procedure

**Status:** Proposed. This is a controlled procedure, not evidence of a
customer commitment, retention period, deletion completion, or legal advice.

## Export

1. Receive an authorized request through the approved support route. Verify
   requester identity, workspace authority, scope, legal holds, and applicable
   data-processing terms.
2. Use only existing permission-controlled export paths. Record the requester,
   workspace, scope, authorizer, generation time, checksum/manifest, expiry,
   and delivery method in the immutable audit record. Do not create a bypass
   export or attach records to an unverified email destination.
3. Deliver through an approved encrypted/authenticated channel. Provide the
   data dictionary, manifest, limitations, and expiry to the customer; retain
   the export evidence according to the approved retention schedule.
4. Verify that restricted records, document metadata, object keys, credentials,
   audit-private data, and other workspaces were not included. Failed/denied
   exports must also be audited.

## Offboarding and deletion

1. Open an offboarding record with owner, authorized requester, requested end
   date, export decision, legal-hold check, retention basis, affected services,
   and customer acknowledgement. Do not assume a retention/deletion period.
2. Immediately revoke user sessions, API/integration access, invitations, and
   provider credentials associated with the pilot. Preserve audit evidence.
3. Produce the authorized export before deletion when required. Confirm secure
   delivery and expiry/revocation of any transfer link.
4. Apply the approved retention/legal-hold policy to database records, released
   objects, quarantine objects, backups, logs, error-reporting events, email
   provider data, and analytics. Legal hold overrides deletion.
5. Execute deletion only through approved services/provider procedures. Record
   redacted completion evidence, including backup-expiry treatment; never claim
   immediate erasure from immutable backups without the provider's verified
   lifecycle evidence.
6. Delete/disable environment-specific customer configuration and DNS only
   after export, legal/privacy, incident, and backup-retention obligations are
   fulfilled. Retain the minimum necessary audit/release evidence.

## Completion evidence required

| Control | Status in this PR |
|---|---|
| Authorized support route and contacts | Not supplied |
| Customer retention/offboarding terms | Not supplied |
| Permission-controlled export rehearsal | Not performed in target environment |
| Session/API/provider credential revocation rehearsal | Not performed in target environment |
| Database/object/log/email/backup deletion evidence | Not performed |
| Legal-hold and backup-expiry review | Not supplied |

All unresolved rows remain launch blockers under PM-PRIV-01 and PM-OPS-01.
