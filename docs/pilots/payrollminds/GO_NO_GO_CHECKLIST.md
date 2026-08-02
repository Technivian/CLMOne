# PayrollMinds Pilot Go / No-Go Checklist

**Status:** Proposed — all boxes are currently unverified
**Decision:** **NO-GO until every applicable item is evidenced.**

## Release identity and governance

- [ ] Immutable release SHA selected from a clean branch; no unrelated worktree changes.
- [ ] Submitted GitHub reviews satisfy the active Charter for the exact SHA.
- [ ] Required CI is green for that unchanged SHA; release/operator record exists.
- [ ] Pilot scope, named-user list, contract-type list, launch owner and support channel are approved and recorded.
- [ ] No prohibited exception is active; any approved temporary exception has a hard expiry and exit plan.

## Product and access

- [ ] One isolated PayrollMinds workspace; no more than 10 named active users.
- [ ] Object-level/private-by-default server-side access is active and tested, including direct URL, search, facets/counts, export, API and access revocation.
- [ ] Manual/bulk upload → quarantine → clean release → document/version → provenance-bearing contract record works with usable failure/retry states.
- [ ] Required metadata is entered or human-verified; no AI output is authoritative.
- [ ] Search, dates, renewal/expiry/notice reminders and controlled audit/export paths pass synthetic UAT.
- [ ] Excluded capabilities are disabled: AI, email forwarding, external users, signatures, integrations, SAML/SCIM and advanced analytics.

## Security and privacy

- [ ] ADR-0016 ingestion gate is active only with approved private quarantine storage, scanner/type validation and fail-closed outage behavior.
- [ ] Production storage is private; signed access, document revocation and restricted-metadata no-leak tests pass.
- [ ] Authentication/session/MFA policy, secrets, dependency/static scans, CSP/security headers and rate limiting are evidenced for the candidate environment.
- [ ] PayrollMinds privacy package is complete: purpose, DPA, subprocessors, data location/transfers, retention, deletion, export/offboarding and incident contacts.
- [ ] Prohibited payroll/employee data controls and incident response are rehearsed.
- [ ] AI remains disabled and no provider receives pilot data.

## Operations and quality

- [ ] Separate pre-production and production environments are configured; deployment does not seed demo data.
- [ ] PostgreSQL, private object storage, Redis workers/schedulers, SMTP, monitoring/error reporting and alerts are configured and tested.
- [ ] Verified backup and successful restoration drill are recorded; migration and rollback/compensating action are rehearsed.
- [ ] Incident owner, support channel, release runbook and rollback triggers are named and tested.
- [ ] Full suite, critical end-to-end paths, accessibility checks and authorization negative tests are green for the release SHA.

## Activation and closure

- [ ] Final preflight evidence is reviewed by the applicable authorities; production approval is separately recorded.
- [ ] First batch is within the approved type/volume/data limits and has explicit launch-owner authorization.
- [ ] Post-activation smoke, monitoring and audit evidence are captured.
- [ ] End-date/offboarding plan, access revocation, export and retention procedures are ready before the first real upload.

## Evidence record

Do not enter approvals or approval dates here. Link the GitHub PR/review/CI,
immutable SHA, deployment/operator record, privacy records and drills in the
authoritative evidence system when they exist.
