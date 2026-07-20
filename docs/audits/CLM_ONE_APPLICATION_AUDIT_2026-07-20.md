# CLM One Application Audit — 2026-07-20

**Type:** Evidence-based baseline audit (read-only; no product changes)  
**Auditor:** Cursor agent (Composer)  
**Governance sources:** `DESIGN_CONSTITUTION.md` (Charter v1.5), `docs/design-system/*`, `theme/static/css/clmone-tokens.css`, approved ADRs (`docs/adr/0008-…`), operational docs  
**Prior baseline:** `PRE_DEMO_READINESS_REPORT.md` (2026-07-15) — treated as historical; re-verified against current code/tests  

---

## Table of contents

1. [Executive audit report](#1-executive-audit-report)
2. [Product scorecard](#2-product-scorecard)
3. [Page and feature inventory](#3-page-and-feature-inventory)
4. [Detailed findings register](#4-detailed-findings-register)
5. [Critical-journey report](#5-critical-journey-report)
6. [Design Drift Report](#6-design-drift-report)
7. [Test and quality report](#7-test-and-quality-report)
8. [Prioritized roadmap](#8-prioritized-roadmap)
9. [Plain closing statement](#9-plain-closing-statement)

---

## Method and confidence

### Evidence used

| Method | Evidence |
|---|---|
| Governance read | Charter, Casefile README/ARCHITECTURE/CONTENT_STANDARDS/DOMAIN patterns, ADR 0008 |
| Code inventory | `config/urls.py`, `contracts/urls.py` (~377 paths), `contracts/models.py`, `nav_config.py`, services for lifecycle/approvals/AI |
| Automated tests (this audit) | Critical subset + workflow subset (see §7) — **not** full 2,045-test suite |
| Runtime | Dev server on `http://127.0.0.1:8060`; login POST with `mvp_admin` → **302** to `/dashboard/`; HTTPS on 8060 not listening |
| Prior reports | PRE_DEMO (15 Jul), READINESS_SCOREBOARD, NORTH_STAR_MATURITY_MATRIX |

### Confidence

| Claim class | Confidence |
|---|---|
| Route/module inventory from URLconf | **High** |
| Lifecycle/permission behaviour from services + focused tests | **High** |
| MSA actions wired (vs PRE_DEMO inert claim) | **High** (code + `test_msa_workflow.py`) |
| Full suite green / production cutover proven | **Low** — not re-run end-to-end; live deploy evidence not re-executed |
| Authenticated UI walkthrough of every screen | **Medium-Low** — login verified; full cookie-session page crawl partially failed tooling; mark many screens **Partial / Unverified** for visual QA |
| Accessibility at 390–1440px | **Low** — not systematically measured this pass |

**Rule applied:** existing screens/code are not proof of correctness against Charter. Ambiguities are recorded, not invented.

---

# 1. Executive audit report

## Overall conclusion

CLM One is a **substantial governed-contract platform**, not a prototype. Core tenancy, contract records, intake routing, MSA workflow (including approvals/export in code), DPA packs, obligations-as-deadlines, upload/review scaffolding, Command Center, and a large automated suite are real.

It is **not production- or enterprise-ready** as a whole. Governance documents still brand as CMS Aegis; status vs lifecycle_stage are dual sources of truth; finance thresholds disagree ($100k vs $250k); NDA workspace actions remain inert `type="button"`; DPA/NDA audit panels are partly synthetic; semantic search and login rate-limit tests failed in this run; design drift (inline CSS, header patterns) remains material; commercial/onboarding surfaces are thin; live integration and cutover proof remain operational gaps.

**Honest maturity (separate measurements):**

| Measurement | Estimate | Confidence |
|---|---|---|
| **Implementation completeness** (surface area that exists and is connected to real data on a happy path) | **~55–65%** of claimed CLM scope | Medium |
| **Pilot readiness** (controlled internal pilot with known limits) | **~40–50%** | Medium |
| **Production / enterprise readiness** | **~25–35%** | Medium-High that it is *below* 40% |

Do **not** treat prior north-star scores (e.g. 4.0–4.5 domain grades in May 2026 docs) as current truth without fresh live proof — those docs still say “CMS Aegis” and predate PRE_DEMO NO-GO findings.

## Strongest parts

1. **Tenant isolation test depth** — large cross-org suite + CI checkbox culture (`test_cross_tenant_isolation.py`).
2. **Contract status transition service** — explicit graph, preconditions for ACTIVE, segregation of duties for approvals.
3. **MSA path (current code)** — generate draft, risk signals, submit Legal/Finance, persist DOCX exports, real AuditLog on MSA workspace (contradicts July 15 “inert buttons” for MSA specifically).
4. **Casefile design-system foundations** — tokens, `.dc-ds-*` primitives, Phase 6 progress on flagship shells (Command Center, repository, settings hub).
5. **Operational documentation volume** — runbooks, cutover checklists, observability policy (documentation ≠ proven live).

## Weakest parts

1. **Governance authority drift** — Charter titled CMS Aegis; button APIs in Charter disagree with Casefile `.dc-ds-button`; dark-theme required in §4 while app is light-only.
2. **Dual lifecycle model** — `Contract.status` and `lifecycle_stage` both user-facing; repository labels Stage/Status inconsistently.
3. **Uneven workflow depth** — MSA largely wired; **NDA buttons inert**; DPA/NDA audit previews synthetic.
4. **AI path** — real Gemini gated; default org policy AI-on; no documented redaction; pilot often AI-off; some review UI copy/tests already drifted.
5. **Surface sprawl** — law-firm modules, duplicate URLs, orphan templates, ~60 inline `<style>` blocks, gravity-well files (`models.py` ~4.2k, `contracts.py` views ~2.9k).

## Top 10 risks

| # | Risk | Priority |
|---|---|---|
| 1 | Finance approval threshold inconsistency ($100k intake/launch vs $250k MSA/routing) causes wrong routing | P0 |
| 2 | Semantic search failure mode (`list` vs dict) — AttributeError in `semantic_search.py:110`; tenant search tests red | P0 |
| 3 | Login rate-limit test failed (expected 429, got 200) — auth abuse control may be ineffective under current cache/config | P0 |
| 4 | NDA workspace primary actions are non-functional buttons | P1 |
| 5 | Synthetic audit previews on DPA/NDA workspaces overstate auditability | P1 |
| 6 | Status vs stage duality + AI API can write lifecycle_stage outside status service | P1 |
| 7 | Secrets inventory incomplete (Gemini, Redis, S3, Stripe, etc.); OIDC rotation marked overdue in inventory | P1 |
| 8 | CSRF/session fragility when mixing HTTP/HTTPS or hosts (observed in product use) | P1 |
| 9 | Design/governance drift undermines “single product language” Charter mandate | P2 |
| 10 | Production cutover / live IdP / backup-restore not re-proven in this audit | P1 (ops) |

## Top 10 opportunities

1. Reconcile Charter → CLM One / Casefile as single authority; retire stale CMS Aegis docs or mark historical.
2. Unify finance threshold and document it in an ADR/PDR.
3. Wire NDA (and any remaining inert CTAs) to the same approval/export pattern as MSA.
4. Replace synthetic DPA/NDA audit panels with `AuditLog` queries (MSA already does this).
5. Collapse status/stage UX to one primary vocabulary per `DOMAIN_PATTERNS.md`.
6. Fix semantic search response parsing + harden rate limiting with Redis in shared environments.
7. Extend CI drift gates beyond three templates; extract repository/DPA inline CSS.
8. Make MSA E2E click Legal/Finance/export (visibility-only today).
9. Ship a **pilot profile**: single-user or role-separated seed, AI off by default, hermetic DB/Redis, smoke suite green.
10. Defer law-firm sprawl / billing self-serve until core CLM pilot path is airtight.

## Go / no-go

| Decision | Recommendation | Rationale |
|---|---|---|
| **Internal demonstration** | **CONDITIONAL GO** | Guided demo of Command Center → New Contract → MSA generate → (if seeded) Legal/Finance submit → repository. Explicitly exclude NDA actions, full e-sign live, and “enterprise complete” claims. |
| **Controlled internal pilot** | **NO-GO until P0s closed** | Threshold bug, search crash, rate-limit doubt, and dual lifecycle confusion are pilot-stopping for trust. |
| **External customer pilot** | **NO-GO** | Needs pilot GO + permission/role clarity + audit honesty + isolated ops + support path. |
| **Production deployment** | **NO-GO** | Cutover/live evidence, secrets hygiene, monitoring ownership, and suite health not certified this pass. |
| **Enterprise deployment** | **NO-GO** | IdP/SCIM/MFA live proof, commercial surfaces, and governance compliance incomplete. |

---

# 2. Product scorecard

Scale: **0** Missing → **5** Production/enterprise-ready. Scores are **not** flattering averages of UI polish.

| Area | Score | Evidence | Main gaps | Pilot blockers | Production blockers |
|---|---:|---|---|---|---|
| Command Center | 3 | Dashboard routes; work items; tests exist | Density/consistency; unverified empty/error states live | Role-separated queues | Observability of queue health |
| New Contract / intake | 3 | Launcher, routing, risk scenarios tested | Copy/threshold mismatches; some test expectation drift | Finance threshold ADR | Jurisdiction policy completeness |
| Upload & Review | 3 | Upload route, OCR/AI pipeline services, review workspace | AI off in many envs; UI copy tests failing | Provider config + human confirm path | Redaction, malware scanning |
| Contracts repository | 3 | Canonical list; filters; record shell | Stage/Status label bug; heavy inline CSS | Label clarity | Performance at scale Unverified |
| Contract detail / tabs | 3 | Record chrome; tabs; blockers | Mixed `arch-title` / badges | Consistent next action | Full tab depth Unverified |
| Documents / versioning | 3 | Document models + APIs | Compare/polish Unverified | Download/open reliability | Virus scanning, retention enforcement |
| Review / clause findings | 3 | Models + finding actions API + tests | Stale UI assertion “AI-assisted clause review” | Human confirmation before approval | Model governance |
| Approvals | 4 | Service + SoD tests + MSA submit tests | Standalone inbox vs in-contract; rule setup required | Seeded rules + non-owner approvers | SLA ops evidence |
| Negotiation | 2 | Notes/collab scaffolding | Depth Unverified | Clear negotiation state machine | External party UX maturity |
| Signature | 2 | Models, blockers, Documenso hooks | Live provider Unverified; NDA send inert | Provider config | Webhook/recon proof |
| DPA Reviews | 3 | Packs, risks, playbooks, rule-based analysis | Synthetic audit preview; detail shell drift | Honest audit UI | Enterprise privacy packaging |
| Risks / decisions | 3 | RiskLog, RiskSignal, intake | Multiple risk concepts | Unified risk vocabulary | Analytics |
| Obligations | 3 | Workspace over Deadline; overdue UI tests | No Obligation model; auto-renewal uneven historically | Reminder reliability | Scheduler live proof |
| Renewals / expiry | 3 | Jobs + tests | Guidance vs UI completeness | Job schedule in pilot env | DR/ops |
| Activity / audit | 3–4 | Hash-chained AuditLog; MSA real | DPA/NDA synthetic panels | Honest audit everywhere | Export/compliance packs |
| Counterparty collaboration | 2 | Token portal routes | Depth/security review Unverified | Scope limits | Enterprise legal review |
| Search / filtering | 2 | Global search + repository | **Semantic search crash**; isolation tests failed | Fix search | Ranking/telemetry |
| Notifications | 2 | List route | Matrix docs vs completeness Unverified | Critical event coverage | Delivery SLAs |
| Admin / settings | 3 | Settings hub cards | Ops outside settings | Admin seeding | SCIM live |
| Users / roles / permissions | 3 | Org Owner/Admin/Member + profile roles | Least-privilege Legal/Finance not first-class org roles | Clear pilot personas | Fine-grained ABAC |
| Templates / playbooks | 3 | Clause templates, DPA playbooks, workflow templates | Three “playbook” concepts | Naming | Analytics |
| AI-assisted features | 2 | Gemini services gated; human findings | Default AI-on policy; no redaction layer documented | Killswitch + disclosure | Governance pack + red-team |
| Reporting / dashboards | 2 | Reports route + executive APIs | Thin vs charter promise | Pilot KPIs | Multi-org evidence |
| Design system consistency | 2 | Strong foundations; weak enforcement | 63 templates with inline styles; header drift | Flagship header fixes | Full migration |
| Security / privacy ops | 3 | MFA, CSRF, rate limit code, privacy suite routes | Rate-limit test fail; secrets inventory gaps | Hermetic pilot env | Live IdP + rotation |
| Accessibility / responsive | 2 | Some a11y rules in Charter | Not systematically verified this pass | Keyboard on critical path | WCAG evidence |
| Performance / reliability | 2 | Health endpoint, observability docs | N+1/asset Unverified | Health green | Load proof |
| Engineering quality | 2 | Domain split exists | Gravity wells; dual URLs | Containment | Modularization |
| Testing / release | 2 | 2045 collected tests; critical subset mostly green | Full suite Unverified; E2E gaps; stale assertions | Critical smoke green | Release gate live |
| Ops / enterprise readiness | 2 | Runbooks/CI workflows exist | Live backup/cutover Unverified | Isolated DB/Redis | Proven DR |

---

# 3. Page and feature inventory

## Primary navigation (`contracts/nav_config.py`)

| Item | Route | Status |
|---|---|---|
| Command Center | `/dashboard/` | **Partial** (happy path exists; depth Unverified live) |
| New Contract | `/contracts/new/start/` | **Partial** |
| Upload & Review | `/contracts/new/upload/` | **Partial** |
| Contracts | `/contracts/repository/` | **Partial** |
| DPA Reviews | `/contracts/dpa-reviews/` | **Partial** |
| Obligations | `/contracts/obligations/` | **Partial** |

## Major modules (selected)

| Module | Key routes | Status | Notes |
|---|---|---|---|
| Auth / MFA | `/login/`, `/mfa/*` | **Partial** | Login works; CSRF sensitive to host/scheme mix |
| Contract CRUD | `/contracts/<pk>/`, edit, tabs | **Partial** | Record shell present |
| Review workspace | `/contracts/<pk>/review/` | **Partial** | UI evolved; some tests stale |
| MSA workflow | `/contracts/new/msa/`, workspace | **Partial→Functional** | Actions wired in code/tests |
| NDA workflow | NDA workspace | **Broken** (CTAs) | `type="button"` inert |
| DPA workflow | `/contracts/new/dpa/`, packs | **Partial** | Rule-based analysis strong; audit UI weak |
| Approvals | `/contracts/approvals/`, rules | **Partial** | Needs configured rules |
| Deadlines (legacy) | `/contracts/deadlines/` | **Partial** / duplicate of obligations |
| Search | `/contracts/search/` | **Broken** (semantic path) | AttributeError risk |
| Settings hub | `/settings/` | **Partial** | Good hub pattern |
| Profile / Account | `/profile/` | **Partial** | Recent redesign; Unverified exhaustively |
| Operations | `/operations/` | **Partial** | Admin-only |
| Design system catalogue | `/contracts/design-system/` | **Complete** as validation surface | Not product nav |
| Design previews | `/contracts/design-preview/*` | **Placeholder** | Sample data |
| Billing | `/contracts/billing/` | **Partial** / often disabled | Feature flag |
| Privacy ops | `/contracts/privacy/*` | **Partial** | Large suite; not in primary nav |
| Law-firm spine | clients, matters, time, invoices, trust | **Partial** / secondary | Mode-neutral routes still present |
| Integrations APIs | Salesforce, NetSuite, e-sign, webhooks | **Partial** | Live proof Unverified |
| SCIM / SAML | Root + `/contracts/` duplicates | **Partial** | Live IdP Unverified |
| Counterparty portal | `/contracts/collaborate/<token>/` | **Partial** | Unverified this pass |
| Clause library template | `clause_library.html` | **Missing** route | Dead template |
| Legacy contract list | `/contracts/` | **Partial** | Duplicate of repository |

## Roles

| Layer | Values | Status |
|---|---|---|
| Org membership | OWNER, ADMIN, MEMBER | **Functional** |
| UserProfile | Partner → Client (law-firm flavoured) | **Partial** for in-house CLM clarity |
| Approval assignees | Rule-specific | **Functional** when configured |

---

# 4. Detailed findings register

## P0

### FIND-001 — Finance approval threshold split
- **Area:** Business rules / routing  
- **Route/workflow:** Intake launch metadata vs MSA risk vs workflow routing  
- **Description:** `$100,000` in `contract_launch_setup.MSA_FINANCE_APPROVAL_THRESHOLD` vs `$250,000` in `msa_workflow.FINANCE_APPROVAL_THRESHOLD` and `workflow_routing.HIGH_VALUE_THRESHOLD`.  
- **Expected:** One governed threshold (Charter: predictable state communication).  
- **Actual:** Path-dependent Finance triggering.  
- **Evidence:** Code cites above; tests encode both behaviours separately.  
- **Severity:** P0 | **Class:** Inconsistent | **Governance:** Needs ADR/PDR  
- **Impact:** Wrong approval chain; demo/pilot distrust.  
- **Root cause:** Parallel constants without single policy object.  
- **Resolution:** Single org/policy threshold; update launch copy + MSA + routing; regression matrix.  
- **Tests:** Extend launch + MSA + routing tests to same constant.  
- **Confidence:** High  

### FIND-002 — Semantic search response parsing crash
- **Area:** Search / tenant isolation  
- **Route:** Global search semantic clause mode  
- **Description:** `contracts/services/semantic_search.py:110` calls `.get` on object that can be a `list` → `AttributeError`.  
- **Expected:** Tenant-safe results or graceful fallback.  
- **Actual:** Two isolation tests failed this audit.  
- **Evidence:** `pytest` failures `PrivacyAndSearchIsolationTest::*semantic*`; line 110.  
- **Severity:** P0 | **Class:** Broken | **Security risk** (availability + possible incorrect degradation)  
- **Resolution:** Normalize provider JSON; fail closed to keyword mode; add fixture for list/dict shapes.  
- **Confidence:** High  

### FIND-003 — Login rate limit did not return 429 in test
- **Area:** Security  
- **Route:** `/login/`  
- **Description:** `test_login_rate_limit_blocks_after_threshold` expected 429, got 200.  
- **Expected:** Threshold blocks credential stuffing.  
- **Actual:** Test red in this environment.  
- **Evidence:** `tests/test_security_guardrails.py` failure this run.  
- **Severity:** P0 | **Class:** Security risk / Unverified prod behaviour  
- **Resolution:** Verify `AuthRateLimitMiddleware` + cache backend; fix flake or defect; require Redis for multi-worker.  
- **Confidence:** Medium (could be test env LocMem quirk — still release-stopping until explained)

## P1

### FIND-004 — NDA workspace CTAs inert
- **Area:** NDA workflow  
- **Route:** NDA contract workspace  
- **Evidence:** `theme/templates/contracts/nda_contract_workspace.html` lines 9–12: `type="button"` for Send for signature, Send to Legal, Generate summary, Export Word — no forms/actions.  
- **Expected:** Same class of server actions as MSA.  
- **Actual:** UI implies actions; none fire.  
- **Severity:** P1 | **Class:** Broken  
- **Confidence:** High  

### FIND-005 — DPA/NDA audit panels synthetic
- **Area:** Auditability  
- **Evidence:** Lifecycle audit agent: MSA queries `AuditLog`; DPA/NDA `_dpa_audit_preview` / `_nda_audit_preview` hardcoded narratives.  
- **Expected:** Persisted audit only (or clearly labelled projection).  
- **Actual:** Can overstate history (PRE_DEMO P1-04 pattern still applies outside MSA).  
- **Severity:** P1 | **Class:** Inconsistent / Governance gap  
- **Confidence:** High  

### FIND-006 — Dual status / lifecycle_stage without UX hierarchy
- **Area:** Lifecycle IA  
- **Evidence:** Models expose both; repository column “Stage” sorts `status`; detail shows two badges; DOMAIN_PATTERNS wants one vocabulary.  
- **Severity:** P1 | **Class:** Inconsistent / product drift  
- **Confidence:** High  

### FIND-007 — Charter / product naming and API drift
- **Area:** Governance  
- **Evidence:** `DESIGN_CONSTITUTION.md` title “CMS Aegis”; §5 `btn-*` vs live `.dc-ds-button`; §4 dark theme vs light-only `base.html`.  
- **Severity:** P1 | **Class:** Governance gap / Documentation gap  
- **Confidence:** High  

### FIND-008 — Incomplete secrets inventory + overdue OIDC rotation flag
- **Area:** Security ops  
- **Evidence:** `docs/SECRET_INVENTORY.md` vs `.env.example` (Gemini, Redis, Stripe, S3…).  
- **Severity:** P1 | **Class:** Security risk / Documentation gap  
- **Confidence:** High  

### FIND-009 — CSRF/session host-scheme sensitivity
- **Area:** Auth UX  
- **Evidence:** User-facing 403 CSRF with incorrect POST token when mixing environments; `CSRF_TRUSTED_ORIGINS` lists 8060 HTTP/HTTPS; runtime HTTPS not listening while HTTP works.  
- **Severity:** P1 | **Class:** Partial / ops  
- **Confidence:** Medium-High  

### FIND-010 — MSA E2E does not click critical actions
- **Area:** Testing  
- **Evidence:** `client/tests/e2e/msa-workflow.spec.js` visibility-focused; unit tests cover actions but browser path incomplete.  
- **Severity:** P1 | **Class:** Documentation gap / Technical debt  
- **Confidence:** High  

### FIND-011 — Stale UI test expectations on review / launch copy
- **Area:** Testing / UX copy  
- **Evidence:** Failed assertions for `AI-assisted clause review` and `Preliminary Low risk` this run.  
- **Severity:** P1 | **Class:** Inconsistent (product moved; tests/docs lag)  
- **Confidence:** High  

### FIND-012 — AI default-on + no documented redaction before provider
- **Area:** AI / privacy  
- **Evidence:** `OrgPolicy.ai_features_enabled` default True; Gemini sends contract excerpts; SECRET/settings comments note redaction as future.  
- **Severity:** P1 | **Class:** Security risk / Governance gap  
- **Confidence:** Medium-High  

## P2

### FIND-013 — Large page-local CSS / undeclared Charter exceptions
- **Evidence:** ~63 templates with `style nonce`; repository & DPA detail heavy; CI bans only narrow set.  
- **Severity:** P2 | **Class:** Technical debt / design drift  

### FIND-014 — Header pattern inconsistency
- **Evidence:** Duplicate MSA titles; empty DPA detail topbar; profile duplicate H1; contract detail `arch-title` inside workspace row.  
- **Severity:** P2  

### FIND-015 — Duplicate routes and orphan surfaces
- **Evidence:** `contract_list` vs `repository`; deadlines vs obligations; SCIM/SAML dual mount; `clause_library.html` unrouted; law-firm modules not in nav.  
- **Severity:** P2  

### FIND-016 — Org roles lack Legal/Finance least privilege
- **Evidence:** Membership Owner/Admin/Member; profile roles law-firm flavoured; approvals via rules/assignees.  
- **Severity:** P2 | **Class:** Partial  

### FIND-017 — Upload validation extension-centric
- **Evidence:** Allowed extensions/size in `documents_ai.py`; magic-byte validation not found.  
- **Severity:** P2 | **Class:** Security risk  

### FIND-018 — Engineering gravity wells
- **Evidence:** `models.py` 4200 LOC; `views_domains/contracts.py` 2875; `urls.py` 448.  
- **Severity:** P2 | **Class:** Technical debt  

### FIND-019 — Commercial / onboarding readiness thin
- **Evidence:** Billing feature-flagged; north-star commercial score historically low.  
- **Severity:** P2  

### FIND-020 — Accessibility/responsive not re-certified
- **Severity:** P2 | **Class:** Unverified / Accessibility gap  

## P3

### FIND-021 — Error pages hardcoded hex  
### FIND-022 — Stale CMS Aegis paths in ops docs  
### FIND-023 — Design catalogue Stage label under status vocabulary demo  

---

# 5. Critical-journey report

Legend: ✅ verified by tests/code this pass · ⚠️ partial · ❌ fail · ❓ Unverified live UI

| # | Scenario | Expected (docs/rules) | Actual (code/tests) | Diff / severity |
|---|---|---|---|---|
| 1 | Standard low-risk SOW | Low/preliminary risk; Legal+Finance playbook metadata | Intake risk LOW for preferred law/our paper; launch tests | ⚠️ Copy assertion failed (`Preliminary Low risk`) — P1 test drift |
| 2 | Personal data + approved DPA | Informational; no extra Privacy score | Code path exists | ❓ No dedicated test with both flags |
| 3 | Personal data without DPA | Privacy escalation + score | ✅ launch/routing tests | — |
| 4 | Cross-border + SCC | Privacy not forced | ✅ routing test | — |
| 5 | Cross-border unresolved | Privacy reviewer | ✅ | — |
| 6 | Non-standard governing law | Legal escalation | ✅ intake; MSA signal weakly asserted | ⚠️ |
| 7 | Third-party paper | Higher risk + deviation | ✅ intake; MSA client_paper ❓ | — |
| 8 | No matching playbook | Medium + Legal full review | ✅ | — |
| 9 | High-value Finance | Finance Director / Finance step | ❌ **Threshold split $100k vs $250k** | **P0** |
| 10 | Missing mandatory info | NOT_ASSESSED / blockers | ✅ | — |
| 11 | Returned for changes | DRAFT + CHANGES_REQUESTED | ✅ `test_mvp_vertical_slice` | — |
| 12 | Expired / overdue | Jobs + UI | ✅ jobs/tests; detail “Expired” guidance ❓ | — |

### End-to-end product paths

| Path | Result |
|---|---|
| Login (`mvp_admin`) | ✅ 302 → dashboard (HTTP :8060) |
| MSA generate → approvals → export | ✅ Covered by `test_msa_workflow.py` (not re-clicked in browser this pass) |
| NDA generate → Legal/export | ❌ Inert buttons |
| Upload → AI review → human findings | ⚠️ Services+tests exist; AI often off; UI copy drift |
| Full signature with live provider | ❓ Unverified |
| Cross-tenant read/mutation | ✅ Broad tests; search semantic ❌ |

---

# 6. Design Drift Report

## Authority conflict

1. Charter still **CMS Aegis**, maps retired `btn-*` / requires dark theme.  
2. Casefile docs + tokens + `.dc-ds-*` are the live standard.  
3. App is **light-only**.

## Inconsistent page families

| Family | Examples | Issue |
|---|---|---|
| Canonical shell | Command Center, repository, settings, upload | Mostly `.dc-ds-page` / topbar titles |
| Workspace record | Contract detail, review workspace | Mixed `arch-title` + `dc-ds-workspace__*` |
| Legacy arch | DPA detail, many `page-wrap` pages | Empty/missing topbar title |
| Marketing | Landing | Large inline CSS (allowed exception, not token-fed) |

## Typography / spacing / components

- Token scale exists; **arbitrary px** in repository sticky table and DPA section CSS.  
- Buttons: mostly `.dc-ds-button`; DPA detail has **modifier-only** classes missing base.  
- Badges: filters on contract header; hand-rolled chains elsewhere; profile custom status pills.  
- Tables: repository hybrid `.dc-ds-table` + `.tbl-*` + `.repo-*`.  
- Cards: `dc-ds-surface` vs `.dpa-section`.

## Status semantics

- Stage vs Status labels disagree on repository.  
- Dual badges on contract header.

## Proposed canonical patterns (identify only — do not redesign here)

1. **One header contract:** topbar = section context; canvas H1 = record identity XOR topbar = record identity — never both identical.  
2. **One button API:** `design_system/button.html` → `.dc-ds-button--*`.  
3. **One lifecycle vocabulary** for users; map both DB fields behind it.  
4. **No new inline `<style>`**; extract repository/DPA; log Charter §15 exceptions with expiry.  
5. **Update Charter** to CLM One / Casefile / light-only (or implement dark — do not leave contradiction).

---

# 7. Test and quality report

## Collection

- **2,045** tests collected under `tests/` (this environment).  
- **165** `test_*.py` modules; **25** Playwright specs under `client/tests/e2e/`.

## Suites executed this audit

| Suite | Result |
|---|---|
| Cross-tenant + MSA + prod gate + MFA + security + lifecycle transitions + MVP slice + self-approval | **164 passed, 3 failed** |
| AI clause review + launch setup + NDA + DPA + obligations + contract detail shell | **198 passed, 2 failed** |

### Failures (this run)

1. `test_global_search_excludes_other_org_results` — semantic_search AttributeError  
2. `test_global_search_semantic_clause_mode_excludes_other_org_results` — same  
3. `test_login_rate_limit_blocks_after_threshold` — 200 ≠ 429  
4. `test_contract_workspace_exposes_governed_review_state` — missing copy `AI-assisted clause review`  
5. `test_create_audit_records_derived_risk_and_routing` — missing `Preliminary Low risk`  

## Important untested / under-tested

- Browser click-through MSA Legal/Finance/export  
- Personal data **with** DPA attached  
- NDA action wiring (will fail until implemented)  
- Live Salesforce/NetSuite/e-sign  
- Full a11y suite  
- Magic-byte malware upload tests  
- Full 2,045 run + Playwright matrix this pass (**Unverified**)

## Misleading / stale tests

- Assertions tied to retired marketing copy on review/launch pages  
- PRE_DEMO claims MSA inert — **obsolete relative to current MSA code** (do not use as current evidence)  
- E2E that only check visibility

## Recommended pyramid

1. **Smoke (every PR):** login, dashboard 200, repository 200, cross-tenant sample, production config gate, MFA fail-closed sample  
2. **Critical unit/integration:** lifecycle transitions, approval SoD, MSA workflow, upload review readiness, DPA pack create  
3. **E2E critical:** smoke.spec.js; msa-workflow **with clicks**; upload happy path; approval decide  
4. **Nightly:** full Django suite; visual baselines; security guardrails  

---

# 8. Prioritized roadmap

## Phase 1 — Stabilize critical workflows and data integrity

| Item | Outcome | Why | Deps | Pri | Effort | Acceptance | Tests |
|---|---|---|---|---|---|---|---|
| Unify finance threshold | One policy constant/org setting | Wrong routing | — | P0 | S | All paths use same value; docs match | Launch+MSA+routing |
| Fix semantic search parse | No crash; tenant filter holds | Isolation red | — | P0 | S | Isolation tests green; fallback works | Isolation + unit |
| Explain/fix login rate limit | 429 after threshold | Auth abuse | Cache/Redis | P0 | S–M | Guardrail test green in CI | Security guardrails |
| Wire NDA CTAs or remove them | No fake buttons | Trust | MSA pattern | P1 | M | POST creates approvals/docs or controls hidden | NDA workflow + E2E |
| Honest DPA/NDA audit UI | AuditLog-backed or labelled | Auditability | — | P1 | M | No synthetic “history” unmarked | DPA/NDA tests |

## Phase 2 — Governance, permissions, security

| Item | Outcome | Why | Deps | Pri | Effort |
|---|---|---|---|---|---|
| Retitle/reconcile Charter | Single authority | Drift | Product decision | P1 | S |
| Secrets inventory refresh + rotations | Complete inventory | Secops | — | P1 | M |
| Status/stage UX decision + ADR | One user vocabulary | Confusion | Product | P1 | M |
| AI default-off for pilot + disclosure | Safe AI | Privacy | Policy | P1 | S |
| Upload content sniffing | Stronger uploads | Sec | — | P2 | M |
| Role model for Legal/Finance | Least privilege | Pilot | ADR | P2 | L |

## Phase 3 — Canonical design / interaction

| Item | Outcome | Why | Effort |
|---|---|---|---|
| Fix DPA/MSA/profile headers | Canonical header | Drift | S–M |
| Extract repository + DPA CSS | Token-aligned | Charter §9 | M |
| Extend design drift CI | Prevent regression | Enforcement | M |
| Badge/button completeness pass | No modifier-only buttons | Consistency | S |

## Phase 4 — Pilot-critical functionality

| Item | Outcome | Effort |
|---|---|---|
| Pilot seed: roles, approval rules, hermetic DB/Redis | Repeatable pilot | M |
| Signature path with sandbox provider | Demoable signature | L |
| Obligation reminders reliable in pilot | Operational CLM | M |
| Notification matrix for pilot events | Awareness | M |

## Phase 5 — Usability, a11y, responsive

| Item | Outcome | Effort |
|---|---|---|
| Keyboard + focus audit on top 10 routes | A11y baseline | M |
| 1440/1024/768/390 pass on nav + detail | Responsive | M |
| Empty/error/permission states pass | Clarity | M |

## Phase 6 — Tests, observability, operations

| Item | Outcome | Effort |
|---|---|---|
| MSA E2E clicks | Prevent PRE_DEMO regression | S |
| Full suite triage to green on main | Release confidence | L |
| Health/alerts ownership | Ops | M |
| Backup/restore drill with artifacts | DR | M |

## Phase 7 — Production / enterprise

| Item | Outcome | Effort |
|---|---|---|
| Live IdP/SCIM/MFA proof | Enterprise identity | L |
| Live CRM/e-sign evidence | Integrations | L |
| Cutover window execution | Launch | XL |
| Commercial/support surfaces | Enterprise package | XL |

### Explicitly do **not** work on yet

- Broad law-firm module polish (clients/matters/time/trust) while CLM pilot path is red  
- Dark theme implementation (resolve Charter first)  
- Marketing landing redesign  
- Billing self-serve expansion  
- New AI features beyond making upload/review safe and honest  
- Large models.py rewrite without lifecycle/threshold/ADR clarity  

---

# 9. Plain closing statement

## Where CLM One stands today

A **real, multi-tenant CLM codebase** with meaningful lifecycle, approval, MSA, DPA, obligations, and design-system work — alongside **serious governance drift, uneven workflow depth, dual lifecycle semantics, and uncertified production ops**.

## Demo-ready?

**Yes, conditionally** — only as a guided internal demo of known-good paths (especially MSA if seeded), with explicit exclusions.

## Pilot-ready?

**Not yet.** Close P0s (threshold, search, rate limit), remove or wire NDA fake actions, make audit UI honest, and run a hermetic smoke+E2E gate.

## Production-ready?

**No.**

## Five highest-leverage next actions

1. **Unify the Finance approval threshold** and record the decision.  
2. **Fix semantic search + confirm login rate limiting.**  
3. **Wire or remove inert NDA actions; replace synthetic DPA/NDA audit with AuditLog.**  
4. **Reconcile Charter ↔ Casefile ↔ light-only** and normalize status/stage UX.  
5. **Stand up a pilot package:** hermetic env, role seed, AI policy, MSA E2E clicks, green critical suite.

## What not to do next

Do not expand surface area (new modules, dark theme, commercial portal, more AI demos) until the core governed path is trustworthy end-to-end.

---

## Appendix A — Runtime notes (2026-07-20)

- Server listening: **HTTP** `0.0.0.0:8060` (PID observed); **HTTPS** probe to 8060 failed (`000`).  
- Login: CSRF token present; POST `mvp_admin` / demo password → **302** `/dashboard/`.  
- Follow-up authenticated crawl via cookie jar returned login titles for most routes (tooling/session persistence issue) — treat deep live UI verification as **Unverified** except login success.  
- Prefer `scripts/dev_up.sh` or `scripts/dev_https.sh` consistently; do not mix hosts/schemes.

## Appendix B — Key file index

| Concern | Path |
|---|---|
| Charter | `DESIGN_CONSTITUTION.md` |
| Casefile | `docs/design-system/README.md` |
| URLs | `config/urls.py`, `contracts/urls.py` |
| Lifecycle | `contracts/services/contract_lifecycle.py` |
| Approvals | `contracts/services/approval_workflow.py` |
| Intake | `contracts/services/intake_risk.py`, `intake_routing.py` |
| MSA | `contracts/services/msa_workflow.py`, `views_domains/msa_workflow.py` |
| AI | `contracts/services/ai_*.py`, `api/documents_ai.py` |
| Nav | `contracts/nav_config.py` |
| Prior demo audit | `PRE_DEMO_READINESS_REPORT.md` |

---

*End of audit. No product code was modified for this deliverable beyond creating this document under `docs/audits/`.*
