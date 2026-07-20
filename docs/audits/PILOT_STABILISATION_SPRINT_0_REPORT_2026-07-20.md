# Pilot Stabilisation Sprint 0 — Final Report

Date: 2026-07-20  
Scope: Seven workstreams to make the governed contract path trustworthy enough for controlled internal pilot reassessment.  
Verdict: **Evidence delivered for reassessment — not a pilot readiness claim.**

---

## Executive summary

Sprint 0 addressed the P0 defects identified in the 2026-07-20 application audit. Governance authority, Finance threshold unification, semantic-search safety, login rate limiting, NDA deceptive CTAs, honest audit history, and Stage/Status definitions were implemented with tests and decision records.

**Outcome labels used below:** Resolved · Mitigated for pilot · Deferred and hidden · Still blocked · Unverified

| Workstream | Outcome |
|---|---|
| 1 Governance authority | **Resolved** |
| 2 Finance threshold | **Resolved** |
| 3 Semantic search | **Resolved** |
| 4 Login rate limiting | **Resolved** (root cause documented) |
| 5 NDA deceptive UI | **Deferred and hidden** |
| 6 Honest audit history | **Resolved** |
| 7 Stage vs Status | **Mitigated for pilot** |

---

## Files changed

### Governance
- `GOVERNANCE_CHARTER.md` (new canonical charter, v2.0)
- `DESIGN_CONSTITUTION.md` (historical supersession banner)
- `docs/adr/0009-governance-charter-supersession.md`
- `docs/design-system/README.md`
- `README.md`
- `scripts/check_brand_regression.sh` (traceability comment only)

### Finance threshold
- `contracts/services/finance_approval_policy.py` (new single source)
- `docs/pdr/0001-finance-approval-threshold.md`
- `contracts/services/contract_launch_setup.py`
- `contracts/services/intake_routing.py`
- `contracts/services/intake_risk.py`
- `contracts/services/msa_workflow.py`
- `contracts/services/workflow_routing.py`
- `contracts/views_domains/msa_workflow.py`
- `theme/templates/contracts/msa_workflow_builder.html`

### Semantic search
- `contracts/services/semantic_search.py`
- `tests/test_semantic_search_responses.py`

### Login rate limiting
- `contracts/middleware.py`
- `tests/test_security_guardrails.py`

### NDA / audit UI
- `theme/templates/contracts/nda_contract_workspace.html`
- `theme/templates/contracts/dpa_contract_workspace.html`
- `contracts/views_domains/workflow_management.py`
- `client/tests/e2e/nda-workflow.spec.js`
- `client/tests/e2e/msa-workflow.spec.js`

### Stage / Status
- `docs/pdr/0002-contract-stage-and-status.md`
- `contracts/services/contract_lifecycle.py`
- `contracts/api/documents_ai.py`
- `contracts/services/repository.py`
- `theme/templates/contracts/repository.html`
- `theme/static/js/clmone-repository.js`

### Tests updated
- `tests/test_finance_approval_policy.py`
- `tests/test_contract_launch_setup.py`
- `tests/test_dpa_workflow.py`
- `tests/test_nda_workflow.py`
- `tests/test_workflow_cockpit_regression.py`

---

## Governance records added or amended

| Record | Action |
|---|---|
| `GOVERNANCE_CHARTER.md` | Created — canonical CLM One Governance Charter v2.0 |
| `DESIGN_CONSTITUTION.md` | Marked historical; superseded by charter + ADR-0009 |
| `docs/adr/0009-governance-charter-supersession.md` | Created |
| `docs/pdr/0001-finance-approval-threshold.md` | Created |
| `docs/pdr/0002-contract-stage-and-status.md` | Created |

Dark-theme parity from the superseded CMS Aegis document is explicitly **deferred post-pilot** in the new charter. No dark mode was implemented.

---

## Defect root causes and before/after behaviour

### 1. Split Finance threshold ($100k vs $250k)
- **Root cause:** Duplicated constants in `contract_launch_setup`, `msa_workflow`, `workflow_routing`, and MSA builder JS.
- **Before:** MSA risk at $250k; intake/launch at $100k — inconsistent Finance routing and UI copy.
- **After:** `finance_approval_policy.py` owns `$100,000`; all workflow/intake/MSA paths and builder JS read from it; audit metadata includes threshold and routing reason.

### 2. Semantic search crash
- **Root cause:** `data.get("ranked_indices")` on JSON list responses → `AttributeError`; provider enabled without `GEMINI_AI_ENABLED` check.
- **Before:** Global search could 500 when Gemini returned a list payload.
- **After:** Response normalisation for dict/list/object-list shapes; respects `GEMINI_AI_ENABLED`; any failure falls back to tenant-scoped keyword rank inside the existing queryset.

### 3. Login rate limit test failure
- **Root cause:** Original audit failure reproduced when running against non-hermetic settings or counting all POSTs before view execution. Hermetic `settings_test` passed pre-fix; logic improved to count **failed** logins only, allow successful login to clear the bucket, and return 429 on subsequent failures after threshold.
- **Before:** Pre-request increment could block valid login after failures; inconsistent semantics vs security intent.
- **After:** Failed attempts increment post-response; successful login clears counter; third failed attempt returns 429 with `Retry-After`.

### 4. NDA deceptive CTAs
- **Root cause:** `type="button"` controls with no server actions in `nda_contract_workspace.html`.
- **Before:** Send for signature / Legal / summary / export appeared actionable but did nothing.
- **After:** Unsupported actions **hidden** for pilot; only “View contract record” remains. Next-action copy changed from “Send for signature” to “Review generated NDA draft”.

### 5. Synthetic DPA/NDA audit panels
- **Root cause:** `_dpa_audit_preview` / `_nda_audit_preview` returned hardcoded five-step narratives.
- **Before:** UI implied completed historical events that were never persisted.
- **After:** Shared `_workflow_audit_history()` queries `AuditLog` (same pattern as MSA); empty state when no events; section renamed “Audit history”.

### 6. Stage column sorted by Status
- **Root cause:** Repository header labelled “Stage” but `data-sort="status"` and repository service sorted on `contract.status`.
- **Before:** Users saw lifecycle stage badges but sorted/filtered operational status.
- **After:** Stage column sorts on `lifecycle_stage`; PDR defines Stage vs Status; AI document review routes lifecycle changes through `apply_contract_operational_position()`.

---

## Tests added

| Test module | Coverage |
|---|---|
| `tests/test_finance_approval_policy.py` | below/equal/above/unknown/confirmed/TCV/settings override |
| `tests/test_semantic_search_responses.py` | dict/list/malformed/provider error/disabled provider |
| `tests/test_security_guardrails.py` | successful login clears failure counter |
| Updated workflow/integration tests | honest audit, hidden NDA CTAs, finance copy |

### E2E updates (not executed in this report run)
- `client/tests/e2e/nda-workflow.spec.js` — asserts unsupported NDA buttons absent
- `client/tests/e2e/msa-workflow.spec.js` — clicks Legal, Finance, Export Word

---

## Exact test results

### Sprint-focused subset (82 tests)
```
Ran 82 tests in 1.512s — OK
```
Includes: finance policy, semantic search, security guardrails, cross-tenant search isolation, MSA/NDA/DPA workflow integration.

### Full Django suite
```
Ran 2067 tests in 53.253s — FAILED (failures=8, skipped=32)
```
**2059 passed** (including all sprint-targeted isolation, lifecycle, MSA, NDA, DPA, and guardrail tests).

### Remaining failures (pre-existing / out of sprint scope)

| Test | Likely category |
|---|---|
| `test_contract_workspace_exposes_governed_review_state` | AI clause review UI copy drift |
| `test_contract_documents_tab_shows_a_completed_clear_upload_review` | Upload review UI |
| `test_create_audit_records_derived_risk_and_routing` | Contract detail missing “Preliminary Low risk” copy |
| `test_case_flow_semantics_on_high_traffic_pages` | UI click integrity |
| `test_canonical_assets_are_exact_approved_files` | Brand asset hash drift |
| `test_phase_three_b_standard_lists_use_the_shell_header_and_scaffold` (×3) | Design-system list scaffold drift |

### Playwright critical suite
**Unverified in this run** — requires live server + seeded E2E user. Specs were updated; execution deferred to CI/local `npm run test:e2e`.

---

## Remaining unsupported functionality

| Area | Status |
|---|---|
| NDA Send for signature | **Deferred and hidden** |
| NDA Send to Legal Review | **Deferred and hidden** |
| NDA Generate summary | **Deferred and hidden** |
| NDA Export Word | **Deferred and hidden** |
| DPA inert header buttons (Legal/DPO/memo/export) | **Still blocked** — not in sprint NDA scope; remain visible |
| Dark theme | **Deferred** per charter amendment |
| DPA signature/export paths | Unchanged |

---

## Screenshots

Screenshots were **not captured** in this automated run. Recommended manual captures for reassessment:
- NDA workspace (only View contract record action)
- DPA/NDA audit history with real `AuditLog` row or empty state
- Repository Stage column sort
- MSA Actions menu after Legal/Finance/export clicks

---

## Unresolved risks

1. **Eight full-suite failures** unrelated to sprint code paths may block CI green — triage separately.
2. **DPA workspace** still exposes inert CTAs (same class of defect as pre-sprint NDA).
3. **Playwright suite unverified** locally in this session.
4. **Redis-backed rate limiting in multi-worker production** — logic is cache-backend agnostic; pilot should confirm shared Redis behaviour under load.
5. **Stage/Status matrix enforcement** — PDR + service routing added; not all legacy writers audited beyond `documents_ai.py`.

---

## Recommendation for controlled-pilot reassessment

Re-run the **2026-07-20 application audit** against this branch with focus on:

1. Finance threshold consistency on a $99,999 vs $100,000 MSA intake
2. Global search with `GEMINI_API_KEY` set and malformed provider payloads
3. Login brute-force behaviour on shared Redis with two workers
4. NDA workspace — confirm no deceptive primary actions
5. DPA workspace — decide whether to hide inert CTAs before pilot (gap remains)
6. Full Playwright critical flows + screenshot evidence

**Suggested reassessment verdict if above pass:** Conditional internal pilot (single org, light-only shell, MSA-first workflows).

---

## Workstream outcome detail

| # | Item | Outcome |
|---|---|---|
| 1 | Governance charter canonical | **Resolved** |
| 2 | Finance $100k unified | **Resolved** |
| 3 | Semantic search safe fallback | **Resolved** |
| 4 | Login rate limit | **Resolved** |
| 5 | NDA CTAs | **Deferred and hidden** |
| 6 | Honest audit | **Resolved** |
| 7 | Stage/Status PDR + repo fix + AI routing | **Mitigated for pilot** |
| 8 | Full green CI + Playwright | **Unverified** |

*This report provides evidence for reassessment. It does not certify pilot readiness.*
