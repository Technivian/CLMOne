# PayrollMinds target environment inventory

**Status: PARTIALLY PROVISIONED (database only).** This is a documentation
cross-reference, not a live infrastructure audit. One component — the
production PostgreSQL database — has been provisioned and confirmed by the
pilot sponsor directly (outside this task's sandboxed environment, which
has no cloud account access of its own). Every other component in §1
remains unselected. See §1a for the database decision and §3 for this
task's own (still-negative) infrastructure-access verification.

## 1. What is documented (proposed, not provisioned)

`docs/pilots/payrollminds/PRODUCTION_INFRASTRUCTURE_PLAN.md` (status:
"Proposed — no resources provisioned, public endpoint activated, or
customer data accepted") describes an intended EU-region topology:

| Component | Documented intent | Provider/account | Verified live? |
|---|---|---|---|
| Application runtime | Django/Gunicorn web service | Unselected — "Decision dependency: Proposed ADR-0018" | No |
| Database | Managed PostgreSQL, TLS-required, dedicated | **Neon, project in `eu-central-1` (AWS Frankfurt, DE)** — see §1a | Confirmed by pilot sponsor; connectivity not independently verifiable from this sandboxed task (§1a) |
| Cache/queue | Isolated Redis | Unselected | No |
| Released document storage | Private S3-compatible bucket, encrypted, versioned, signed URLs | Unselected | No |
| Quarantine storage | Separate private bucket/prefix, worker-only identity | Unselected | No |
| Secret management | Provider secret injection only | Unselected | No |
| DNS/TLS | Approved domain, managed TLS | Unselected | No |
| Backup | Operator-only backup store, immutable retention | Unselected | No |
| Logging/monitoring | Structured logs + error-reporting sink | Unselected | No |
| Region/residency | "Frankfurt/EU where available" | Not confirmed by any provider contract | No |

`docs/pilots/payrollminds/PRODUCTION_ENVIRONMENT_VARIABLE_INVENTORY.md`
confirms the same status ("Proposed. This inventory names configuration
only; it contains no values, resource identifiers, endpoints, domains, or
credentials") and explicitly states: "A new operator-maintained inventory
must be created in the selected secret manager before activation."

**No provider, account/subscription/project identifier, region commitment,
or data-residency confirmation exists anywhere in this repository or this
task's environment.** ADR-0018 (the decision dependency named by the
infrastructure plan) has not been located as an accepted decision record.

## 1a. Database decision — confirmed 2026-08-08

The pilot sponsor supplied a live Neon PostgreSQL connection string
directly in conversation and confirmed:

1. This is the actual intended production database for the pilot (not a
   placeholder or test instance).
2. It satisfies the "Frankfurt/EU where available" residency intent from
   `PRODUCTION_INFRASTRUCTURE_PLAN.md` — the Neon project region is
   `eu-central-1`, which is AWS Frankfurt, Germany: genuinely EU-proper,
   not merely EU-adjacent.
3. The database is new and empty; no data migration occurred or is
   required.

**A prior candidate is superseded.** An earlier connection string supplied
in the same conversation pointed to a Neon project in `eu-west-2` (AWS
London, UK). This was flagged back to the sponsor as not satisfying an
EU-region requirement — the UK is not in the EU post-Brexit, a material
distinction for GDPR/data-residency purposes. The sponsor then created a
new, separate Neon project in `eu-central-1` rather than migrating the
London one. **Disposition of the superseded `eu-west-2` project (decommission
vs. retain) has been asked of the sponsor and is awaiting an answer as of
this writing — no action has been taken on it.**

**Handling of the credential itself:** the connection string (which embeds
a username and password) was received in this task's chat transcript only.
It has not been, and will not be, written to any file, commit, log, or
environment variable in this repository or its CI. Nothing beyond
provider name, region, and confirmation status is recorded here or
anywhere else in version control.

**Independent verification not possible from this task's environment:** an
attempt to open a direct PostgreSQL connection to the new host from this
sandboxed session did not succeed — the connection attempt produced no
response at all (neither data nor an error) within a combined ~210 seconds
before being cancelled, consistent with this environment's outbound network
policy silently dropping raw TCP egress to arbitrary external hosts/ports
(this task's environment otherwise only reaches the internet through an
HTTP(S) proxy to an explicit allowlist, as documented for other components
throughout this pilot's phases — see `VERIFIED_SECRET_TRIAGE.md` §"Egress
policy" for the analogous HTTPS case). This is a limitation of the task's
own sandbox, not evidence about the database's real reachability. The
sponsor's account of the database (new, empty, correct region) is taken at
face value; nothing destructive or data-bearing depends on that trust here.

**What this does and does not unblock:** one line of
`PRODUCTION_INFRASTRUCTURE_PLAN.md`'s topology table (Database) now has a
real, confirmed answer. Every other row — application runtime, cache/queue,
object storage (released + quarantine), secret management, DNS/TLS, backup
target, logging/monitoring sink — remains "Unselected." A single
provisioned datastore does not constitute a commissioned target
environment; §2's overall BLOCKED status is unchanged, and
`PRODUCTION_TARGET_COMMISSIONING.md` §2 has been updated to reflect this
partial, database-only progress rather than treated as resolving the phase.

## 2. What this task's environment actually has access to

This coding session runs in an ephemeral, sandboxed container with:
- A git working copy of `technivian/clmone` and push access to GitHub via a
  scoped app token.
- A local SQLite in-memory test database (`config.settings_test`) — used for
  all Django `TestCase` work throughout this pilot's engineering phases.
- No installed cloud CLI of any kind: `aws`, `gcloud`, `az`, `render`,
  `doctl`, `heroku`, `terraform`, `pulumi`, and `kubectl` were all checked
  and none are present.
- `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` environment variables are set,
  but resolve to invalid credentials — `boto3.client('sts').get_caller_identity()`
  returns `InvalidClientTokenId: The security token included in the request
  is invalid`. These are not real, usable AWS credentials for any account,
  let alone PayrollMinds' intended production one; `moto` (an AWS-mocking
  test library already in `requirements/runtime.txt`) is the only consumer
  of AWS-shaped configuration anywhere in this repository's own test suite.
- No `DATABASE_URL`, `REDIS_URL`, or any other production-shaped connection
  string is set as an environment variable or committed anywhere in this
  repository. (The sponsor-supplied Neon connection string discussed in
  §1a exists only in this task's chat transcript, never as a file or env
  var here, and a direct-connection attempt from this sandbox to it
  received no response — see §1a.)
- No deployment webhook, Render/Railway/Fly/Heroku API token, or any other
  hosting-provider credential is present.

## 3. Verification method

```
$ which aws gcloud az render doctl heroku terraform pulumi kubectl
(no output — none installed)

$ .venv/bin/python -c "import boto3; print(boto3.client('sts').get_caller_identity())"
botocore.exceptions.ClientError: An error occurred (InvalidClientTokenId)
when calling the GetCallerIdentity operation: The security token included
in the request is invalid.
```

## 4. Conclusion

As of 2026-08-08, one real component exists: a Neon PostgreSQL database in
`eu-central-1`, confirmed by the pilot sponsor as the intended production
database (§1a). This task's own environment still cannot independently
reach or verify it (no cloud CLI, invalid AWS credentials, and — newly
confirmed — no usable raw TCP egress to arbitrary external hosts from this
sandbox). Every other component named in `PRODUCTION_INFRASTRUCTURE_PLAN.md`
(application runtime, cache/queue, released and quarantine storage, secret
management, DNS/TLS, backup target, logging/monitoring sink) remains
unselected, and ADR-0018 remains unaccepted. A single provisioned datastore
is real progress but does not amount to an "actual intended production
target environment" being identified, commissioned, or verified end to end.
Phases 2–16 of the production-infrastructure commissioning task
(`PRODUCTION_TARGET_COMMISSIONING.md`, `BACKUP_RESTORE_DRILL.md`,
`PRODUCTION_OPERATIONS_READINESS.md`) remain reported **BLOCKED** overall,
not fabricated, on this basis — §2 of `PRODUCTION_TARGET_COMMISSIONING.md`
notes the database-specific exception.
