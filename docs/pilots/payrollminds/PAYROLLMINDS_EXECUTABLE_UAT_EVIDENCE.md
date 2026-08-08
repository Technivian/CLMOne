# PayrollMinds executable UAT evidence

**Status: EXECUTABLE UAT GREEN.** This is not production authorization. See
§25 for the full recommendation basis.

## 1. Source/base SHA

`68a1f568292d3a26dad8dc6f7ec80e91bd607349` — current `main`, which already
contains the security repair (PR #167) and the reconstructed release stack
(PR #168), both merged in the prior session turn on the user's explicit
instruction. The prompt's "authoritative reconstructed SHA" `2abf292d` is a
verified ancestor of this commit (`git merge-base --is-ancestor 2abf292d
HEAD` returns true).

## 2. UAT branch/PR

Branch: `codex/payrollminds-executable-uat`
Draft PR: [#169](https://github.com/Technivian/CLMOne/pull/169)

## 3. Relationship to PR #168

Built directly from `main` at `68a1f568` (PR #168's merge commit), not from
a stale or divergent base. No rebase or cherry-pick was required — `main`
already is the reconstructed, security-repaired stack this task's starting
state describes.

## 4. Old PR #152 evidence reconciliation

PR #152 ("PayrollMinds: integrate pilot hardening and synthetic UAT
evidence", merged 2026-08-04) added both documentation-only evidence
(`UAT_SCRIPT.md`, `UAT_ACCEPTANCE_SHEET.md`, `UAT_DEFECT_REGISTER.md`,
`UAT_GO_NO_GO_RECOMMENDATION.md`, etc.) and some real executable coverage
(`tests/test_payrollminds_pilot_product_path.py`,
`tests/test_payrollminds_ai_governance_gate.py`, plus additions to
`tests/test_document_ingestion_security.py`,
`tests/test_organization_invitations.py`,
`tests/test_upload_ocr_pipeline.py`). Its own final recommendation was
**NO-GO**, citing seven unresolved critical/high defects (PM-UAT-01–07:
target-environment object-level evidence, quarantine/malware evidence,
reviewed CI SHA, private storage/IAM, isolated operations, AI governance,
privacy/offboarding) and three infrastructure-blocked rows (backup/restore,
production-like deployment, offboarding rehearsal).

| UAT criterion (historical ID) | Existing evidence (PR #152) | Executable today? | New coverage required? |
|---|---|---|---|
| 01–02 authorized/blocked upload | `test_document_ingestion_security.py` additions | Yes — reconfirmed | PM-UAT-002 adds the full HTTP quarantine→release path and canonical-chain provenance assertions PR #152 did not add |
| 03–04 bulk/duplicate import | Repository CSV import tests (pre-existing) | Yes | Out of this suite's scope — CSV import is not part of the PayrollMinds pilot's approved intake path (`PILOT_SCOPE.md`: "Manual and bulk browser upload only") |
| 05–06 unsupported/oversized file | `test_document_ingestion_security.py` validation tests | Yes | PM-UAT-016 adds the malicious-verdict-never-releasable path specifically |
| 07–08 extraction success/fallback | Local deterministic metadata-preview tests | Yes | PM-UAT-003 reconfirms `governance_sources` on a UAT-owned contract |
| 09 human verification | `DocumentReviewRun.governance_sources` assertions | Yes | PM-UAT-003 |
| 10 rejected AI suggestion | `test_payrollminds_ai_governance_gate.py` | Yes | PM-UAT-012 reconfirms against a UAT-owned contract with AI explicitly configured-but-blocked |
| 11 provenance | Provenance service tests, synthetic seed records | Yes | PM-UAT-002 |
| 12–14 private access/tenant denial/revocation | `test_payrollminds_pilot_product_path.py` (object-read/private-document tests) | Yes | PM-UAT-008/009/010/011 add a second ordinary member, a second workspace, and a direct-identifier bypass attempt, none of which PR #152's own suite exercised together |
| 15 permission-aware search | Search/repository enforcement tests | Yes | PM-UAT-005 |
| 16–18 date correction/renewal/overdue reminder | **PARTIAL in PR #152** — "local obligation/renewal tests cover modeled states; no real worker/email delivery evidence" | Partially — see known limitation below | PM-UAT-006 adds real HTTP creation via `deadline_create` (PR #152 did not) and discovers/documents that the dedicated Obligations UI route is currently outside `CONTROLLED_PILOT_ENABLED=true` route scope |
| 19 export authorization | Owner/member `organization_security_export` tests | Yes, but that route is **MFA-gated** and out of this task's "do not activate MFA" boundary | PM-UAT-007 uses `organization_activity_export` instead — the pilot's actual purpose-bound, audit-logged "controlled export" capability, which requires no MFA |
| 20 audit evidence | `test_audit_integrity.py` hash-chain tests | Yes | PM-UAT-017 builds a machine-verifiable, per-contract audit timeline (not present in PR #152) and reconfirms append-only enforcement |
| 21 job failure/retry | Async job tests (pre-existing) | Yes | Out of this suite's scope — not part of the pilot's user-facing acceptance surface |
| 22 backup/restore | Restore-service tests pass locally; **BLOCKED**, no real drill | No | Out of scope — requires real infrastructure (§ below) |
| 23 production-like deploy | **BLOCKED**, no isolated pre-production | No | Out of scope — requires real infrastructure |
| 24 offboarding/export rehearsal | **BLOCKED**, no target-environment rehearsal | No | Out of scope — requires real infrastructure |

No historical "PASS" claim was reused as evidence in this document without a
runnable test backing it; every row above traces to an actual test method in
either the pre-existing suite or `tests/test_payrollminds_executable_uat.py`.

## 5. Full UAT matrix

See `docs/pilots/payrollminds/PAYROLLMINDS_EXECUTABLE_UAT_MATRIX.md` — 18
scenarios (PM-UAT-001..018), each with business purpose, actor, and mapped
historical ID.

## 6. Scenario IDs

PM-UAT-001 through PM-UAT-018 (see matrix). Machine-readable status for each
is in `docs/pilots/payrollminds/release-baseline/executable-uat-results.json`.

## 7. Synthetic actors

- `payrollminds-uat-owner` — OWNER role, `payrollminds-uat` workspace.
- `payrollminds-uat-member-b` — MEMBER role, same workspace, owns/creates nothing.
- `payrollminds-uat-outsider` — OWNER role, `payrollminds-uat-other` workspace (a wholly separate organization for cross-workspace scenarios).

## 8. Synthetic data definition

Every fixture (contract title, counterparty, deadline title, invite emails,
signer name/email) is a literal, obviously-synthetic string prefixed or
labeled `payrollminds-uat`/`PayrollMinds UAT` — e.g. "PayrollMinds UAT
synthetic agreement", "payrollminds-uat-invitee@example.com". No real
PayrollMinds/customer/employee/payroll/salary data appears anywhere in the
suite.

## 9. Happy-path result

PM-UAT-001 through PM-UAT-007 (workspace entry, governed intake, metadata
review, NDA workflow progression, authorized search, operational tracking,
controlled export) — **all pass**, 9 test methods, 0 failures.

## 10. Negative/control results

PM-UAT-008 through PM-UAT-016 (private access denial, cross-workspace
denial, direct-identifier bypass denial, revocation, AI/inbound-email/
signature/integration disabled, malicious-file rejection) — **all pass**, 10
test methods, 0 failures.

## 11. Access/security results

Every negative-control scenario above is an access/security result by
construction. Additionally: the full `tests.test_cross_tenant_isolation`
(75 tests) and `tests.test_permission_matrix` (2 tests) suites pass
unchanged on this branch.

## 12. Canonical object/provenance proof

PM-UAT-002 proves, via both the direct service call and the real HTTP
quarantine→release API: a clean upload atomically creates exactly one
`Contract`, `Document`, and immutable `DocumentVersion`, with
`contract.origin_kind == UPLOAD`, `contract.provenance_locked_at` set, and
matching `AuditLog` entries for `contract.record.created` and
`document.version.created`.

## 13. Audit timeline

PM-UAT-017 collects every `AuditLog` row for the UAT organization across the
happy-path contract's lifecycle (intake release, document/version creation,
controlled export) and verifies: every event carries the correct
`organization_id` and a timestamp; every hash-chained (`hash_version == 2`)
event carries a non-empty `entry_hash` and a `seq`; and the ORM-level
append-only guarantee is structurally enforced (`AuditLog.objects.filter(...).update()`
and `.delete()` both raise `AuditWriteError`, not merely return an error
response). No audit event is manually fabricated — every one is a real
side effect of a real HTTP/service call.

## 14. Controlled-export proof

PM-UAT-007: the workspace owner exports `organization_activity_export`
(CSV), the exported body contains the invite the test actually created, and
a matching `organization.activity_exported` `AuditLog` entry exists. An
ordinary member is denied (403). A second test proves the export from one
workspace never contains another workspace's rows, even when both
workspaces performed the same action around the same time.

## 15. Disabled-capability proof

- **External AI** (PM-UAT-012): `contract_ai_extract_api` returns 403 with a
  manual-fallback message, and the AI client (`ai_extraction._get_client`)
  is never called — even with `GEMINI_AI_ENABLED=True` and a configured
  `GEMINI_API_KEY`.
- **Inbound email** (PM-UAT-013): no URL name resolves for any plausible
  email-ingestion route, and `DocumentIngestionAttempt` has no `source`
  field of any kind — there is structurally one intake path, the governed
  upload API.
- **Signature** (PM-UAT-014): `ControlledPilotScopeMiddleware` blocks every
  `/contracts/signatures/*` route outright (`reason=signatures_out_of_scope`)
  under the pilot's real deployment setting (`CONTROLLED_PILOT_ENABLED=true`,
  confirmed live in the CI job log — see §18); the `SignatureRequest` never
  transitions out of `PENDING`. Defense in depth: the pilot's actual
  deployment configures no `ESIGN_PROVIDER`, so even a reachable route would
  resolve to the inert, purely-local `NullSignatureProvider`.
- **External portal/integration** (PM-UAT-015): no `WebhookEndpoint` exists
  and no `WebhookDelivery` is ever created for the pilot workspace across
  the full UAT run.

## 16. Isolation/cleanup result

PM-UAT-018: the UAT organization slug (`payrollminds-uat`) is verified
distinct from `payrollminds-pilot` (used by the pre-existing product-path
tests) and `payrollminds-demo` (the presenter/demo workspace). A UAT
contract is verified invisible from the second UAT workspace's own
repository query. A dedicated companion test
(`test_pm_uat_018_previous_test_left_no_residue`) queries for any
`payrollminds-uat*`-scoped `Contract` or `DocumentIngestionAttempt` at the
very start of its own transaction and finds none — proving Django
`TestCase`'s per-test transactional rollback, not merely method-call order,
is what keeps every scenario's mutations from leaking into any other test
in the same run (including the pre-existing browser/visual suite, which
this branch does not touch at all).

## 17. Local/Linux UAT totals

`tests.test_payrollminds_executable_uat`: **24/24 passed**, 0 failed, 0
errors, 0 skipped, 2.5s (`.venv/bin/python manage.py test
tests.test_payrollminds_executable_uat -v 1`, `config.settings_test`,
SQLite in-memory).

## 18. GitHub authoritative UAT totals

PR #169, workflow run
[31220152961](https://github.com/Technivian/CLMOne/actions/runs/31220152961),
job `quality-and-tenancy` (id `93002721771`), step "PayrollMinds executable
UAT", commit `c5f83238be862999f8a70ef692e9f954834f06c1`:

```
Ran 24 tests in 24.298s

OK
```

**24/24 passed, 0 failed, 0 errors, 0 skipped.** The same job log shows live,
real middleware decisions matching the suite's own assertions:
`pilot_scope_denied path=/contracts/api/contracts/1/ai-extract/
reason=ai_out_of_scope` and `pilot_scope_denied
path=/contracts/signatures/1/send/ reason=signatures_out_of_scope`.

## 19. Full browser regression totals

Same PR #169, commit `c5f83238`, workflow run
[31220154272](https://github.com/Technivian/CLMOne/actions/runs/31220154272):
all 8 `verify-ui-browser` shards report `success`; `verify-ui-scope`,
`verify-ui-integrity`, and the `verify-ui` aggregate gate all report
`success`. `get_job_logs(run_id=31220154272, failed_only=true)` →
`{"failed_jobs":0,"total_jobs":11}`. This branch touches no
`client/tests/e2e/*` file, so the manifest is unchanged from the
previously-verified **94/94** result (PR #168, run `31214434868`); zero
failures across all 11 browser-related jobs on this branch's own run
corroborates that nothing regressed.

## 20. Security regression totals

Combined local battery — `test_cross_tenant_isolation`,
`test_permission_matrix`, `test_par_sec_002_search_enforcement`,
`test_par_sec_002_repository_enforcement`, `test_private_document_repository`,
`test_payrollminds_pilot_product_path`, `test_document_ingestion_security`,
`test_payrollminds_ai_governance_gate`, `test_organization_security_export`,
`test_upload_ocr_pipeline`, `test_payrollminds_executable_uat`,
`test_organization_invitations` — **all passing** (245 tests, 1 pre-existing
and unrelated failure in `tests.test_nda_workflow`, see §23). `pr-release-evidence`
and `security-scans` both passed in CI on the final commit.

## 21. Dependency/security scans

- **Bandit** (`security-scans` job, `bandit -q -r contracts config -lll`) — passed.
- **Secret scan** (TruffleHog) — passed, 0 verified/unverified secrets.
- **pip-audit** — passed, no known vulnerabilities (`requirements/runtime.txt`).
- **npm audit baseline gate** — **initially failed** on this PR's first CI run (commit `b18b708a`): `client: nanoid` flagged for `GHSA-2v37-7h3g-55p8` (high, indefinite loop with a zero-size custom generator), a real, pre-existing, unrelated advisory that surfaced between PR #168's clean scan and this run. Remediated in commit `c5f83238` (`nanoid` `3.3.16` → `3.3.18`, via `npm audit fix`). **Passed** on the re-run (workflow run `31220152961`).

## 22. Migrations

None introduced. `makemigrations --check --dry-run` reports no changes,
verified before pushing.

## 23. Known limitations

1. **Obligations UI route currently out of pilot scope.** Under the pilot's
   real deployment setting (`CONTROLLED_PILOT_ENABLED=true`),
   `ControlledPilotScopeMiddleware` blocks the dedicated
   `/contracts/obligations/` UI route outright
   (`reason=obligations_out_of_scope`), even though `PILOT_SCOPE.md` lists
   "effective/expiry/renewal/notice dates and reminders" as an in-scope
   pilot capability. PM-UAT-006 proves and documents this discrepancy rather
   than working around it (`test_pm_uat_006_obligations_ui_currently_out_of_pilot_route_scope`).
   The underlying `Deadline` data model, creation path (`/contracts/deadlines/new/`,
   which is *not* blocked), object-read authorization, and audit evidence
   all function correctly and are proven separately
   (`test_pm_uat_006_operational_tracking_deadline`, with
   `CONTROLLED_PILOT_ENABLED=False` to isolate that boundary from the route
   allowlist, mirroring the precedent already set by
   `test_payrollminds_pilot_product_path.py`). This is a scope/route-allowlist
   gap between documentation and the middleware's current prefix list, not a
   security defect — nothing is exposed that shouldn't be; a capability
   documented as in-scope is presently less reachable via the dedicated UI
   than the charter describes. Recommend the pilot's product owner either
   updates `PILOT_SCOPE.md` to reflect the current, narrower route allowlist,
   or removes `/contracts/obligations` from `ControlledPilotScopeMiddleware`'s
   out-of-scope prefix list, before UAT sign-off with a real pilot operator.
2. **CSV bulk import and async job failure/retry** (historical UAT-03/04,
   UAT-21) are proven by pre-existing test suites but are not included as
   PM-UAT scenarios in this matrix; CSV import is not part of the pilot's
   approved intake path per `PILOT_SCOPE.md`, and job failure/retry is not
   part of the pilot's user-facing acceptance surface.
3. **`tests.test_nda_workflow.NDAWorkflowBuilderIntegrationTests
   .test_command_center_row_links_back_to_generated_workspace`** fails on
   plain `main` (`68a1f568`), reproduced in isolation with no files from
   this branch involved. Pre-existing, unrelated to PayrollMinds pilot
   scope (a Command Center row's "Self-serve eligible" label text), not
   introduced or touched by this work. Not part of this UAT's scope; noted
   here for completeness rather than silently omitted.
4. Backup/restore, production-like deployment, and offboarding rehearsal
   (historical UAT-22/23/24) remain infrastructure-blocked, as carried
   forward unchanged from PR #152 — see §4.

## 24. Artifacts

- `docs/pilots/payrollminds/PAYROLLMINDS_EXECUTABLE_UAT_MATRIX.md`
- `tests/test_payrollminds_executable_uat.py`
- `docs/pilots/payrollminds/release-baseline/executable-uat-results.json`
- `.github/workflows/platform-guardrails.yml` (new `quality-and-tenancy` step)
- GitHub Actions workflow runs [31220152961](https://github.com/Technivian/CLMOne/actions/runs/31220152961) (UAT + full battery) and [31220154272](https://github.com/Technivian/CLMOne/actions/runs/31220154272) (browser suite), PR #169, commit `c5f83238`.

## 25. Recommendation

**EXECUTABLE UAT GREEN.** All success criteria are met: historical PR #152
evidence is reconciled honestly (§4), with every reused claim backed by a
runnable test and every partial/blocked claim carried forward as such; all
18 mandatory pilot acceptance scenarios (PM-UAT-001..018) are executable and
pass both locally (24/24, §17) and in authoritative GitHub CI (24/24, §18);
authorization-negative scenarios pass (§10-11); audit/provenance evidence is
machine-verifiable (§13); every externally-disabled capability is proven
disabled by real code, not merely asserted (§15); UAT test data is isolated
by dedicated namespace and Django's own transactional rollback (§16); the
complete 94-test browser regression remains fully green (§19); the security
battery remains fully green (§20-21); no new critical/high security issue
exists (the one npm finding was fixed, §21); and migration drift is zero
(§22). One known, honestly-documented scope/route-allowlist gap exists
(§23.1) and does not block this recommendation — it does not weaken any
security or access control, and PM-UAT-006 proves the underlying data model
and authorization boundary work correctly independent of it.

Nothing in this branch was merged or deployed. No real customer data was
used. PR #162/MFA remained excluded and inactive throughout (this suite
deliberately avoids the one MFA-gated export route and uses the
non-MFA-gated `organization_activity_export` instead, precisely so MFA
activation is never required to prove controlled export).
