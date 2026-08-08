# PayrollMinds target environment inventory

**Status: PARTIALLY PROVISIONED.** This is a documentation cross-reference,
not a live infrastructure audit. Database, object storage, DNS/TLS domain,
and named provisioning authority have been decided by the pilot sponsor
directly (outside this task's sandboxed environment, which has no cloud
account access of its own). Application runtime, cache/queue, secret
management, and backup/monitoring remain open — see §1b for why "free" and
"EU region" don't cleanly co-exist for compute today. See §1a/§1b for the
decisions and §3 for this task's own (still-negative) infrastructure-access
verification.

## 1. What is documented (proposed, not provisioned)

`docs/pilots/payrollminds/PRODUCTION_INFRASTRUCTURE_PLAN.md` (status:
"Proposed — no resources provisioned, public endpoint activated, or
customer data accepted") describes an intended EU-region topology:

| Component | Documented intent | Provider/account | Verified live? |
|---|---|---|---|
| Application runtime | Django/Gunicorn web service | **Open — see §1b; no free+EU+indefinite option verified yet** | No |
| Database | Managed PostgreSQL, TLS-required, dedicated | **Neon, project in `eu-central-1` (AWS Frankfurt, DE)** — see §1a | Confirmed by pilot sponsor; connectivity not independently verifiable from this sandboxed task (§1a) |
| Cache/queue | Isolated Redis | Proposed: Upstash Redis (free tier), region TBD at signup — see §1b | No — not yet created |
| Released document storage | Private S3-compatible bucket, encrypted, versioned, signed URLs | **Cloudflare R2** — confirmed by pilot sponsor 2026-08-08, see §1b | Existing sponsor account; EU jurisdictional restriction not yet confirmed configured |
| Quarantine storage | Separate private bucket/prefix, worker-only identity | Proposed: separate bucket/prefix in the same Cloudflare R2 account | No — not yet created |
| Secret management | Provider secret injection only | Deferred pending application-runtime platform choice | No |
| DNS/TLS | Approved domain, managed TLS | **Cloudflare (existing account); domain `clmone.com`** — confirmed 2026-08-08, see §1b | No — DNS record/proxying not yet configured |
| Backup | Operator-only backup store, immutable retention | Neon built-in point-in-time recovery (database only); free tier retention is **6 hours**, not a long-term backup store — see §1b | Not independently verified (§1a) |
| Logging/monitoring | Structured logs + error-reporting sink | Proposed: Sentry free "Developer" tier (`sentry-sdk` already a runtime dependency) | No — not yet created |
| Region/residency | "Frankfurt/EU where available" | Database confirmed EU (`eu-central-1`); everything else TBD, see §1b for why compute is the hard case | Partial |

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

**A prior candidate was superseded and has now been decommissioned.** An
earlier connection string supplied in the same conversation pointed to a
Neon project in `eu-west-2` (AWS London, UK). This was flagged back to the
sponsor as not satisfying an EU-region requirement — the UK is not in the
EU post-Brexit, a material distinction for GDPR/data-residency purposes.
The sponsor created a new, separate Neon project in `eu-central-1` rather
than migrating the London one, and on 2026-08-08 confirmed the `eu-west-2`
project has been deleted directly through their own Neon account. This
task's environment had no ability to perform or verify that deletion
itself — it has no Neon account, dashboard, or API access, and (separately)
this sandbox cannot make raw PostgreSQL connections to any external host
regardless of credentials (confirmed empirically when attempting to reach
the `eu-central-1` database — see below). The sponsor's confirmation is
taken at face value, consistent with how the database's existence and
region were established in the first place. No data migration was reported
or requested as part of the deletion.

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

## 1b. Hostname, provisioning authority, and free-tier stack research — 2026-08-08

**Hostname confirmed:** `clmone.com`, supplied directly by the pilot
sponsor.

**Provisioning authority confirmed:** Haroon Wahed, supplied directly by
the pilot sponsor. This maps to the "Infrastructure operator" role in
`PRODUCTION_OPERATIONS_RUNBOOK.md`'s service-ownership table (accountable
for "PostgreSQL, Redis, storage, DNS/TLS, backup" — matching exactly what
was asked and confirmed: authority to create production resources and run
backup/restore drills). Recorded there; see that document. The other named
roles in that table (Engineering/Release Authority, Security owner,
Privacy/Product owner, PayrollMinds support owner) remain unnamed.

**Object storage confirmed:** Cloudflare R2, an account the sponsor already
holds. Unlike the database, this was not established via a live credential
exchange — the sponsor referenced the existing account and this task
confirmed via its own prior research (web search, not fabricated) that R2
is broadly suitable (S3-compatible API, zero egress fees, optional
jurisdictional restrictions for EU data residency). **The EU jurisdictional
restriction is a setting that must be explicitly configured per bucket — it
is not a default, and this task has no way to verify whether it has been
turned on for this account.**

**Application runtime — researched, deliberately left open.** Asked to
find a way to "keep things free" while satisfying the EU-region intent,
this task ran current (2026-08-08) web searches rather than rely on
possibly-stale assumptions, and found no compute option that is
simultaneously free, EU-region, and available indefinitely:

- **Google Cloud Run** — Always Free tier is real (2M requests/month) but
  restricted to three US regions (`us-central1`, `us-east1`, `us-west1`);
  does not satisfy EU residency. A billing account is now also required
  (Feb 2026 policy change) even to use the free tier.
- **Fly.io** — the free tier was removed in October 2024; the smallest
  always-on machine now costs roughly $1.94/month.
- **Cloudflare Containers** (available under the same account as R2) —
  requires the $5/month Workers Paid plan; no free tier exists, and the
  product is designed for bursty/scale-to-zero workloads rather than a
  persistently-running Django process with a background worker.
- **Azure App Service, F1 (free) tier** — West Europe has a documented
  capacity shortage as of February 2026, and F1 does not support a custom
  domain with SSL at all, which would block serving `clmone.com` over
  HTTPS on it.
- **AWS EC2 free tier** — time-limited, not indefinite (12 months of
  750 hours/month for AWS accounts opened before 2025-07-15, or a 6-month
  $200 credit for newer accounts) — and this task's own environment has no
  valid AWS credentials to begin with (`InvalidClientTokenId`, §2).
- **Render.com** — confirmed to offer a Frankfurt EU region across all its
  services, but search results conflicted on whether its free web-service
  tier still exists in 2026 (some sources say it ended November 2024,
  others say 750 free hours/month remains active). This could not be
  resolved from this task's environment and needs live verification at
  `render.com` directly before being relied on.

No application-runtime decision was recorded as confirmed on the strength
of this research, because none of it rises to the same evidentiary bar as
the database/storage/DNS decisions above (a live account the sponsor
created and confirmed). The honest state is: this remains the one open
topology gap, and the realistic expectation is that it may require a small
non-zero monthly cost (~$5–7) rather than being free, even though every
other component here can be.

**Backup retention caveat:** Neon's free-tier point-in-time recovery window
is 6 hours (verified via current documentation, not assumed) — materially
short of what `PRODUCTION_OPERATIONS_READINESS.md`/§7 of
`PRODUCTION_TARGET_COMMISSIONING.md` would need for a real backup/restore
drill with a meaningful RPO. This is flagged here rather than left implicit
in the "Neon has PITR" statement.

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

As of 2026-08-08, several real decisions exist: a Neon PostgreSQL database
in `eu-central-1` (§1a), Cloudflare R2 for object storage, a `clmone.com`
hostname on the sponsor's existing Cloudflare account, and a named
provisioning authority — Haroon Wahed (§1b). This task's own environment
still cannot independently reach or verify most of these (no cloud CLI,
invalid AWS credentials, no usable raw TCP egress to arbitrary external
hosts from this sandbox). The application runtime remains the one
topology component this task could not responsibly resolve: current
research (§1b) found no compute option that is simultaneously free,
EU-region, and available indefinitely, so it is reported open rather than
assigned a provider on weaker evidence than the rest of this document
uses. Cache/queue, secret management, and true long-retention backup also
remain unselected or only partially answered (Neon's free-tier
point-in-time recovery window is 6 hours, not a long-term backup store).
ADR-0018 remains unaccepted. This is real progress but does not amount to
an "actual intended production target environment" being identified,
commissioned, or verified end to end. Phases 2–16 of the
production-infrastructure commissioning task
(`PRODUCTION_TARGET_COMMISSIONING.md`, `BACKUP_RESTORE_DRILL.md`,
`PRODUCTION_OPERATIONS_READINESS.md`) remain reported **BLOCKED** overall,
not fabricated, on this basis — §2 of `PRODUCTION_TARGET_COMMISSIONING.md`
notes the specific exceptions.
