# PayrollMinds UAT role-based test matrix

| Role | Permitted synthetic activity | Required negative proof |
|---|---|---|
| Workspace owner/admin | create/release a permitted synthetic record, view owned record, controlled evidence export, manage members | no provider AI in pilot; export remains audited; cannot bypass offboarding/legal hold controls |
| Contract owner | enter/verify manual metadata, correct dates, view own documents/reminders | cannot reveal another record/workspace; cannot grant privileges not defined by policy |
| Member/reviewer | view only explicitly eligible synthetic records and conduct allowed human review | direct URLs, API, download, export, search, counts, metadata and bulk actions deny without leakage |
| Revoked user | none after membership/session revocation | existing URL/API/search/download/export requests fail without object disclosure |
| Background worker | local OCR/reminder/job processing only | no unattended external-AI submission; failure/retry/dead-letter state is explicit |
| Release operator | execute only approved synthetic pre-production checks | no public activation, real-data loading, credential disclosure, or unreviewed migration |

The matrix does not create roles or permissions. It maps existing tested
workspace, object-read, export and job boundaries to UAT evidence.
