# Document ingestion operations

## Browser batch import

Authenticated workspace users can open `/contracts/import/` to import up to 50
existing agreements in one request. Each attachment becomes a separate Contract
Record and immutable Document Version. The record is created as `IN_PROGRESS`
at the `INTAKE` lifecycle stage with `IMPORT_INBOUND` provenance.

Readable text is automatically inspected for metadata. The results are saved on
the linked Document Review Run as `extracted_unverified`; they do not update
authoritative contract fields, start AI review, or advance lifecycle state.
Reviewers must confirm the information in the Contract Review workspace.

## Email-forwarded attachments

Email forwarding is deliberately disabled by default:

```text
EMAIL_FORWARDED_INGESTION_ENABLED=false
```

After the applicable integration release controls are complete, an operator may
enable it and configure the mail provider to POST multipart attachments to:

```text
POST /contracts/api/integrations/email-forwarding/ingest/
Authorization: Bearer <scoped contracts:write token>
X-Message-Id: <provider's stable original message id>
attachments: <one or more files>
```

Provision a dedicated, revocable `contracts:write` token through workspace
Identity settings. Do not use a broad `api:*` token. The endpoint does not
persist message body, subject, or sender. It records only imported document
evidence, a hashed source-message identifier, and content-free audit events.

The same Message-ID is idempotent per attachment position. A retry returns the
attachment as skipped rather than creating another record. Disable the setting
to stop ingress immediately; existing records and audit evidence are preserved.
