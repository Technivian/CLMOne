# Production Cutover Run Log Template

Date:
Window:
Release commit:
Operator(s):
Approver:
Environment host:

## Command Execution Log

| Step | Timestamp (UTC) | Command / Action | Result (Pass/Fail) | Evidence Path / Link | Notes |
|---|---|---|---|---|---|
| Confirm target commit | | `git rev-parse HEAD` | | | |
| Confirm DB engine | | `python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])"` | | | |
| Fresh backup created | | `pg_dump -Fc "$PGDATABASE" > ...` | | | |
| Traffic drained | | Platform action | | | |
| Deploy release commit | | `git checkout <sha>` | | | |
| Migrations | | `python manage.py migrate --noinput` | | | |
| Null org audit | | `python manage.py audit_null_organizations` | | | |
| Postgres cutover check | | `python manage.py verify_postgres_cutover` | | | |
| Release gate | | `python manage.py generate_release_gate_report --fail-on-no-go` | | | |
| Live smoke | | Manual checklist run | | | |
| Traffic restored | | Platform action | | | |
| Final null org audit | | `python manage.py audit_null_organizations` | | | |
| Final release gate | | `python manage.py generate_release_gate_report --fail-on-no-go` | | | |

## Smoke Checklist Outcome

- Anonymous dashboard redirect works: [ ]
- Org A/B isolation confirmed: [ ]
- Cross-org contract access denied: [ ]
- Admin/team flows pass: [ ]
- Search isolation passes: [ ]

## Artifact Checklist

- [ ] `release-gate-report.json` (GO)
- [ ] `sprint3-integration-report.json` (GO on live data)
- [ ] `esign-integration-report.json` (GO on live data)
- [ ] Webhook SENT evidence in cutover window
- [ ] Backup path + checksum/size logged
- [ ] Manual smoke signoff attached
- [ ] Final gate output attached

## Decision

- Go live: [ ] YES [ ] NO
- If NO, rollback initiated: [ ] YES [ ] NO
- Rollback reference: `docs/ROLLBACK_RUNBOOK.md`

## Signoff

- Operator:
- Tech lead:
- QA:
- Security:
