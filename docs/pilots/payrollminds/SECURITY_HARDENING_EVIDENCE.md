# PayrollMinds security hardening evidence

**Status:** Proposed evidence record. It does not approve a production launch,
enable a feature, grant access, or accept residual risk.

## Scope and source

This stacked PR addresses the remaining application-level metadata-leak route
under PM-SEC-01 from the PayrollMinds launch-readiness report. It depends on
the default-off quarantine and private-record controls in the parent pilot-path
PR. No new domain, access, audit, or ingestion model is introduced.

## Threat summary

| Threat | Control in this PR | Verification |
|---|---|---|
| Ordinary workspace member enumerates a private counterparty or matter through list/detail routes | Existing object-read policy now filters Client and Matter list/detail querysets and their counts | Member gets generic `404`/empty results; owner path remains available |
| Search exposes private relationship metadata | The existing search policy uses the same Client/Matter evaluator | Search results contain no private contract, client, matter, or document row |
| Former member retains record access | Existing active-membership evaluation fails closed | Deactivation removes repository results and direct access |
| Download or export bypasses policy | Existing parent controls require permission and append audit evidence; regression tests cover protected document download and owner/admin-only audit export | Focused security suite |
| Credential is committed | `platform-guardrails` now runs pinned TruffleHog OSS on PRs and main pushes | Workflow validation pending CI for this exact SHA |

## Email-ingestion boundary

No enabled forwarded-email ingestion endpoint, setting, worker, or destination
credential exists in this candidate. Email ingestion is therefore excluded and
must remain unavailable. It is not safe to enable merely by configuring SMTP.

Before any future email-ingestion activation, a separately authorized design
must prove sender and destination allowlists, bounded attachment size and file
types, message/attachment idempotency, quarantine-first malware scanning,
retry/dead-letter handling, content-free failure messages, and append-only
audit events. This PR neither implements nor authorizes those capabilities.

## Checks and no-migration statement

- Django system checks and migration detection are run for the candidate.
- Focused negative-path tests cover cross-workspace access, direct URLs,
  repository/document/search/count non-leakage, member revocation, downloads,
  exports, and audit append-only behavior.
- `pip-audit --disable-pip --no-deps -r requirements/runtime.txt` reports no
  known vulnerabilities in the local dependency resolution.
- `bandit -q -r contracts config -lll` exits successfully locally.
- No schema or data migration is included. Rollback is a code rollback plus
  the parent PR's existing fail-closed quarantine/repository abort switches;
  never delete audit or document evidence as a rollback action.

## Remaining release blockers requiring external evidence

PM-SEC-04 (private bucket/IAM and deployed signed-download/revocation proof),
PM-SEC-05 (non-demo deployment), PM-OPS-01/02 (worker, monitoring, backup and
restore evidence), PM-PRIV-01 (privacy/customer controls), and PM-QLT-01
(full-green release gate) remain unresolved. No code change can truthfully
close them without an approved environment, operator records, and customer or
release-owner action.
