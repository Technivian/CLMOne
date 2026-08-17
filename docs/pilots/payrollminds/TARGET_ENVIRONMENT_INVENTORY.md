# PayrollMinds target environment inventory

**Status: LIVE.** A real pilot deployment exists, is running, and has been
configured to the pilot's approved scope — this is no longer a proposal.
It surfaced mid-conversation (§1c) as a pre-existing Render deployment the
sponsor had already stood up outside this task's visibility, not something
commissioned through this document's own phased process. This is a
documentation cross-reference, not a live infrastructure audit — every
fact below is either sponsor-reported (from terminal output/logs the
sponsor pasted) or inferable from this repository's own code (e.g., "the
app booted, therefore these settings-import-time guards must have already
been satisfied"); this task's own sandboxed environment still has zero
direct access to any of it (§2/§3). See §1a (database), §1b (hostname/
authority/storage decisions and free-tier research, now partly superseded),
and §1c (the live Render deployment, migration, and hardening) for the
full record.

## 1. Current topology (live, unless marked otherwise)

`docs/pilots/payrollminds/PRODUCTION_INFRASTRUCTURE_PLAN.md` (status still
formally "Proposed" — not yet updated to match reality) describes an
intended EU-region topology. Actual state as of 2026-08-08:

| Component | Documented intent | Provider/account | Verified live? |
|---|---|---|---|
| Application runtime | Django/Gunicorn web service | **Render, Frankfurt (EU) region** — pre-existing deployment, discovered §1c | Live at `clmone.com`; sponsor-confirmed loading and functional after hardening (§1c) |
| Database | Managed PostgreSQL, TLS-required, dedicated | **Neon, `eu-central-1` (AWS Frankfurt, DE)** — see §1a | Live; migrated from a prior Render Postgres instance and verified via full row-count comparison across all 122 tables (§1c) |
| Cache/queue | Isolated Redis | **Not configured** — `REDIS_URL` unset on Render | No — degrades gracefully (in-process cache, synchronous background jobs) rather than crashing, but not the designed operating mode (§1c) |
| Released document storage | Private S3-compatible bucket, encrypted, versioned, signed URLs | **Cloudflare R2**, wired via `MEDIA_STORAGE_BACKEND=s3` | Live — confirmed indirectly: `settings_production.py` refuses to boot at all unless this is `s3`, and the app is serving requests (§1c) |
| Quarantine storage | Separate private bucket/prefix, worker-only identity | **Cloudflare R2, separate bucket + separate Account API token**, configured 2026-08-08 | Configured; not independently verified from this task (§1c) |
| Secret management | Provider secret injection only | Render's own environment-variable store (not a dedicated secret manager/vault) | Live, but see §1c for the caveat: two database credentials were briefly exposed in this task's chat transcript and were rotated as remediation |
| DNS/TLS | Approved domain, managed TLS | `clmone.com` pointed **directly at Render** (not proxied through Cloudflare); TLS via Render's own managed certificate | Live |
| Backup | Operator-only backup store, immutable retention | Neon built-in point-in-time recovery (database only); free tier retention is **6 hours**, not a long-term backup store | Exists, but no real restore drill has been performed against the live database (§1c) — this is a genuine, unresolved gap now that real data exists |
| Logging/monitoring | Structured logs + error-reporting sink | **Not configured** — `SENTRY_DSN` unset | No — `sentry-sdk` is already a dependency and silently no-ops without a DSN; low-effort fix, not yet done |
| Region/residency | "Frankfurt/EU where available" | **Both application runtime (Render) and database (Neon) confirmed Frankfurt/EU-proper** | Yes — the one part of the original intent that ended up fully satisfied |

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
created and confirmed). At the time this was written, this was reported
as the one open topology gap.

**Superseded, 2026-08-08 (same day, later in conversation): this research
turned out to be moot.** The sponsor already had a live Render deployment
running in Frankfurt — see §1c. The research above is left in place as an
accurate record of what was actually checked and why each alternative was
rejected or uncertain (Render's own free-tier status was the one item this
task could not resolve by search, which is exactly the item that turned
out to already be running the pilot). It should not be read as describing
the current state of the application-runtime row in §1's table.

**Backup retention caveat:** Neon's free-tier point-in-time recovery window
is 6 hours (verified via current documentation, not assumed) — materially
short of what
`PAYROLLMINDS_PRODUCTION_OPERATIONS_READINESS.md`/§7 of
`PRODUCTION_TARGET_COMMISSIONING.md` would need for a real backup/restore
drill with a meaningful RPO. This is flagged here rather than left implicit
in the "Neon has PITR" statement.

## 1c. Discovery of a pre-existing live deployment, migration, and hardening — 2026-08-08

While asking whether the old, superseded `eu-west-2` Neon database (§1a)
should be decommissioned, the sponsor mentioned it had a Render PostgreSQL
service already holding real data and due to expire (Render deletes free
databases that aren't upgraded within a set window). Follow-up questions
established that a full PayrollMinds Django application had been running
live on Render — Frankfurt region, at `clmone.com` — this whole time,
entirely outside this task's own visibility (this task's sandboxed
environment has no access to any cloud account; see §2). The sponsor
described it as "real pilot go-live," used only by the sponsor so far (no
other users yet).

**What this means for every prior phase in this document set:** phases
that reported infrastructure as wholly unprovisioned were accurate about
what this task's own sandbox could see and verify, not fabricated — but
they did not know about, and could not have known about, infrastructure
the sponsor had set up independently outside this conversation. This
section records what was found and fixed once it came to light.

**Database migration (Render → Neon).** The Render Postgres instance held
real (non-trivial, though not real PayrollMinds customer/payroll data —
sponsor-only usage) application data: 122 tables, the largest holding 441
rows. The sponsor ran the migration from Google Cloud Shell (this task's
own sandbox cannot make raw PostgreSQL connections to any external host,
so it could not perform this itself — see §2):
```
pg_dump "$RENDER_DATABASE_URL" --no-owner --no-privileges -Fc -f render_backup.dump
pg_restore --no-owner --no-privileges -d "$NEON_DATABASE_URL" render_backup.dump
```
**Verified, not assumed:** the sponsor ran
`SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;`
against both databases and pasted both full result sets into this task's
chat. Every one of the 122 tables was compared row by row — all 34
non-empty tables matched exactly (e.g. `auth_permission` 441=441 on both
sides, down through `contracts_dpariskitem` 1=1), and both sides listed
the same 122 tables with the same empty/non-empty pattern. A second,
final dump/restore pass (`pg_restore --clean --if-exists`) was run
immediately before cutover to catch any writes made between the first
verification and the actual `DATABASE_URL` swap. The app's `DATABASE_URL`
environment variable on Render was then updated to point at Neon; the
deploy log's `Database: ...neon.tech (deployed platform, env=production)`
line confirmed the swap took effect.

**Credential exposure and rotation.** In the course of this migration, the
sponsor pasted terminal output into this task's chat that included both
databases' full connection strings (username and password in plaintext)
on two separate occasions. This is disclosed here rather than omitted.
Remediation: the sponsor rotated the Neon database password immediately
after migration was confirmed (the Render password mattered less, since
that database was already scheduled for deletion). Neither credential was
ever written to this repository, any commit, or any file — only to this
task's own chat transcript, which is outside this document's control.

**Pilot-scope and security hardening.** The live deployment was found to
be missing several settings this pilot's own engineering work depends on.
None of these were guessed at — each was confirmed against this
repository's actual code (`contracts/middleware.py`, `config/settings_base.py`,
`config/settings_production.py`) before being recommended, and the sponsor
confirmed each fix afterward:

- `CONTROLLED_PILOT_ENABLED` was not set. Per `ControlledPilotScopeMiddleware`'s
  own docstring, "when `CONTROLLED_PILOT_ENABLED` is false, only the
  existing billing/trust kill switches apply" — and those (`BILLING_SELF_SERVE_ENABLED`,
  `TRUST_ACCOUNTING_ENABLED`) default to `True` when unset, not `False`.
  Practical effect before the fix: the pilot-scope denylist (billing,
  trust accounting, clients, matters, invoices, signatures, freeform
  contract creation, upload review, DPA review packs, workflow-template
  builder, approval-rule authoring) was **not enforced** on the live
  deployment. Fixed by setting `CONTROLLED_PILOT_ENABLED=true`,
  `BILLING_SELF_SERVE_ENABLED=false`, `TRUST_ACCOUNTING_ENABLED=false`,
  `GEMINI_AI_ENABLED=false`.
- `ALLOWED_HOSTS` did not include `www.clmone.com`, causing Django to
  reject every request — including Render's own health checks — with
  `DisallowedHost`, visible in the deploy logs as a repeating 400 every
  ~10 seconds. Fixed: `ALLOWED_HOSTS=clmone.com,www.clmone.com`.
- `CSRF_TRUSTED_ORIGINS` was set to `https://*.onrender.com` (a leftover
  from before the custom domain was attached) and, in an intermediate
  state, to bare domains without a URL scheme — Django compares this
  setting against the browser's `Origin` header, which always includes
  a scheme, so a bare-domain entry silently fails to match. Fixed:
  `CSRF_TRUSTED_ORIGINS=https://clmone.com,https://www.clmone.com`.
- Quarantine storage (`DOCUMENT_QUARANTINE_STORAGE_BACKEND` and related
  vars) was unset, falling back to Render's local filesystem — ephemeral,
  wiped on every redeploy. A second, separate Cloudflare R2 bucket was
  created with its own Account API token (deliberately not a User token,
  and deliberately not reusing the main bucket's credential, preserving
  the intended worker-only-identity isolation between released and
  quarantined documents) and wired via
  `DOCUMENT_QUARANTINE_STORAGE_BACKEND=s3` plus the matching
  `DOCUMENT_QUARANTINE_*` variables.

**What was already correct, verified by inference rather than direct
access.** `config/settings_production.py` raises `ImproperlyConfigured` at
Django's settings-import time (crash-looping the whole process, not just
failing one request) if `DEBUG` is true, `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`
are empty, `DEFAULT_FROM_EMAIL`/`OPERATOR_ALERT_EMAIL` are unset or
placeholder values, `APP_BASE_URL` isn't a valid public HTTPS origin, or
`SECRET_KEY` is short or contains an insecure-default marker. Because the
deployed process was already running and serving HTTP responses (even
wrongly-rejected ones) before this task ever became aware of it, every one
of those guards must already have been satisfied — so `DEBUG=False` and a
strong `SECRET_KEY` are treated as already-confirmed facts here, not
verified by direct inspection (this task has no access to actually read
Render's environment variables).

**Remaining gaps, honestly still open:**
- `REDIS_URL` is unset. This degrades gracefully rather than crashing —
  cache falls back to per-process in-memory (`LocMemCache`), and
  `django-rq` background jobs run synchronously inline instead of queued
  (`RQ_QUEUES['default']['ASYNC'] = False` when `REDIS_URL` is empty). Not
  broken today (the deploy log shows `WEB_CONCURRENCY=1`, a single
  process, so there's no cross-worker cache inconsistency yet), but it is
  not the designed operating mode, and anything meant to run as a
  background job now blocks the request instead.
- `SENTRY_DSN` is unset — no error-reporting/monitoring sink exists yet.
- No real backup/restore drill has ever been performed against the live
  Neon database — only Neon's own 6-hour point-in-time-recovery window
  exists, untested by this pilot.
- The old Render Postgres database still exists as of this writing, no
  longer referenced by the live app's `DATABASE_URL`, pending either
  manual deletion or its scheduled 2026-08-14 auto-expiration.
- DNS for `clmone.com` is pointed directly at Render, not proxied through
  Cloudflare — Cloudflare is used for R2 object storage only in this
  setup, not as a CDN/WAF layer in front of the app.

None of this section's facts were independently verified by this task's
own tooling — every claim here is either something the sponsor pasted
directly (logs, query output) or a logical inference from this
repository's own code (e.g., "the app booted, therefore these specific
settings-import guards must already pass"). Where that distinction
matters, it is stated explicitly above rather than left ambiguous.

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

As of 2026-08-08, the situation this document set was written to assess
has fundamentally changed. A real target environment exists: Render
(Frankfurt) running the application, Neon (`eu-central-1`/Frankfurt) as
its database, Cloudflare R2 for both released and quarantine document
storage, `clmone.com` live with TLS, and a named provisioning authority
(Haroon Wahed). It was not commissioned through this document's own
phased process (Phases 2–16 of `PRODUCTION_TARGET_COMMISSIONING.md`) —
it was discovered mid-conversation as something the sponsor had already
stood up independently, then verified, migrated, and hardened in place
(§1c) once that came to light. This task's own sandboxed environment
still has zero direct access to any of it — every fact in §1c is either
sponsor-reported (pasted terminal output, query results) or a logical
inference from this repository's own code, never independently confirmed
by this task's own tooling (§2/§3 remain unchanged and still describe a
completely credential-less sandbox).

Real, honest gaps remain: no `REDIS_URL` (background jobs run
synchronously rather than queued), no `SENTRY_DSN` (no error-reporting
sink), no backup/restore drill ever performed against the live database
(only Neon's untested 6-hour point-in-time-recovery window exists), and
several named operational roles beyond the infrastructure operator
(Engineering/Release Authority, Security owner, Privacy/Product owner,
PayrollMinds support owner) are still unnamed. ADR-0018 remains
unaccepted as a formal decision record, even though its substance has now
mostly happened in practice.

Given this, "NO-GO" as a blanket description of infrastructure readiness
is no longer accurate — a real, correctly-scoped, security-hardened pilot
deployment is live. But "GO" would overstate it too: no restore drill, no
monitoring, and incomplete named ownership are not cosmetic gaps for a
system now holding real (if sponsor-only, non-customer) data. See
`PRODUCTION_TARGET_COMMISSIONING.md`'s own updated recommendation for how
this document set now characterizes the overall state, phase by phase,
rather than repeating a single verdict here that a two-word label cannot
honestly carry.
