# Batch 4 Post-Migration Audit

**Date:** 2026-05-18
**Auditor:** Copilot (automated + manual inspection)

---

## 1. Scope

| Template | Assigned Archetype | Step |
|---|---|---|
| `theme/templates/contracts/reports_dashboard.html` | DashboardPage | Step 2 Slice A |
| `theme/templates/contracts/identity_telemetry_dashboard.html` | DashboardPage | Step 2 Slice A |
| `theme/templates/contracts/contract_list.html` | QueuePage | Step 4 Slice B |
| `theme/templates/contracts/contract_detail.html` | WorkspacePage | Step 5 Slice B |
| `theme/templates/contracts/search_results.html` | QueuePage | Step 6 |

---

## 2. Validation Results

### Template Parse

| Template | Result |
|---|---|
| reports_dashboard.html | ✅ OK |
| identity_telemetry_dashboard.html | ✅ OK |
| contract_list.html | ✅ OK |
| contract_detail.html | ✅ OK |
| search_results.html | ✅ OK |

### manage.py check

```
System check identified no issues (0 silenced).
```

### Test Suite

```
Found 3 tests. Ran 3 tests in 0.236s — OK
```

### Inline Style Scan

| Template | Violations |
|---|---|
| reports_dashboard.html | 0 ✅ |
| identity_telemetry_dashboard.html | 0 ✅ |
| contract_list.html | 0 ✅ |
| contract_detail.html | 0 ✅ |
| search_results.html | 0 ✅ |

> Note: `reports_dashboard.html` contains `fill.style.height = ...` inside a `<script>` block for JS-driven bar chart sizing — this is a JavaScript property assignment, not an HTML `style=` attribute. Not a violation.

### Inline Event Handler Scan

All 5 templates: 0 violations ✅

### Retired Class Scan

`action-chip`, `dashboard-card`, `btn-sm`, `sidebar-nav`, `card-header`, `card-body`: **0 references across all 5 templates** ✅

---

## 3. Archetype Conformance

### Structure primitives

| Template | `page-wrap` | `page-header` | `page-title` | `page-subtitle` | `page-actions` |
|---|---|---|---|---|---|
| reports_dashboard.html | ✅ (×2 — outer + inner section) | ✅ | ✅ | ✅ | ✅ |
| identity_telemetry_dashboard.html | ✅ (×2) | ✅ | ✅ | ✅ | ✅ |
| contract_list.html | ✅ | ✅ | ✅ | ✅ | ✅ |
| contract_detail.html | ✅ | ✅ | ✅ | ✅ | ✅ |
| search_results.html | ✅ | ✅ | ✅ | ✅ | — (no page-level actions) |

### Content primitives

| Template | `panel` | `kpi-card`/`stat-card` | `tbl-*` | `list-row` | `badge-sm` | `btn-*` |
|---|---|---|---|---|---|---|
| reports_dashboard.html | ✅ | ✅ kpi-card | — | — | ✅ | ✅ |
| identity_telemetry_dashboard.html | ✅ | ✅ kpi-card | — | — | ✅ | ✅ |
| contract_list.html | ✅ | ✅ stat-card | ✅ tbl-head/th/row/td | — | ✅ | ✅ |
| contract_detail.html | ✅ (×5) | — | — | ✅ | ✅ | ✅ |
| search_results.html | ✅ (×9) | — | — | ✅ (×7 sections) | — | ✅ |

### Text utilities

| Template | `c-muted` | `c-link` | `c-danger` | `c-warning` | `c-info` |
|---|---|---|---|---|---|
| reports_dashboard.html | ✅ | ✅ | — | ✅ (Step 3) | ✅ (Step 3) |
| identity_telemetry_dashboard.html | ✅ | ✅ | — | — | — |
| contract_list.html | ✅ | ✅ | — | — | — |
| contract_detail.html | ✅ | — | — | — | — |
| search_results.html | ✅ | ✅ | ✅ | — | — |

---

## 4. Behavior Preservation Audit

### reports_dashboard.html

| Element | Preserved? |
|---|---|
| KPI cards (total_contracts, active_contracts, avg_risk_score, expiring_soon) | ✅ |
| risk_trend_data / contract_value_data chart JS | ✅ |
| risk-trend-chart / contract-value-chart canvas IDs | ✅ |
| period filter (GET param) | ✅ |
| recent_contracts table with links | ✅ |
| empty state conditionals | ✅ |
| All context variables | ✅ |

### identity_telemetry_dashboard.html

| Element | Preserved? |
|---|---|
| KPI cards (total_identities, active_sessions, failed_logins, threat_indicators) | ✅ |
| Login activity / threat distribution chart IDs | ✅ |
| recent_sessions / threat_indicators table loops | ✅ |
| All context variables | ✅ |

### contract_list.html

| Element | Preserved? |
|---|---|
| Sort links (title, case_phase, value, end_date) with sort+q+phase params | ✅ |
| Search/filter GET form (q, phase, sort) | ✅ |
| Pagination (page param, page_range, has_previous/next) | ✅ |
| Contract rows (title link → contract_detail, counterparty, badge status, expiry date) | ✅ |
| Action links (edit, delete with confirm) | ✅ |
| New Contract button → contract_create | ✅ |
| stat-card-amber / expiring_soon conditional | ✅ |
| row-overdue class on overdue rows | ✅ |
| empty-state for empty queryset | ✅ |

### contract_detail.html

| Element | Preserved? |
|---|---|
| All 5 panel sections (Contract Info, Deadlines, Negotiation Notes, Documents, AI Assistant) | ✅ |
| Edit link → contract_edit | ✅ |
| AI Analyze button → contract_ai_assistant fetch POST | ✅ |
| IDs: ai-assistant-trigger, ai-assistant-prompt, ai-assistant-submit, ai-assistant-status, ai-assistant-output | ✅ |
| Deadline rows with badge-red/blue status | ✅ |
| Document list-rows with document_detail links | ✅ |
| Negotiation notes vertical stack | ✅ |
| Metadata key-value pairs | ✅ |
| All context variables (contract, deadlines, negotiation_notes, documents) | ✅ |

### search_results.html

| Element | Preserved? |
|---|---|
| GET search form (q, type, status, jurisdiction, search_mode) | ✅ |
| Save search preset POST form (save_search_preset + hidden current_search_params.*) | ✅ |
| Delete preset POST forms (delete_search_preset + preset.id) | ✅ |
| 7 result category panels (cases, clients, case_matters, task_signals, documents, clauses, counterparties) | ✅ |
| All detail route links (contract_detail, client_detail, matter_detail, legal_task_kanban, document_detail, clause_template_detail, counterparty_detail) | ✅ |
| saved_searches loop | ✅ |
| Empty state (no results + prompt-to-search) | ✅ |
| All context variables | ✅ |

---

## 5. Exceptions Decision Table

| Exception | Template | Class / Pattern | Decision | Rationale |
|---|---|---|---|---|
| Chart bar fill colors | reports_dashboard.html | `bg-blue-500`, `bg-red-500` in `<script>` JS `className` | **Remain documented — JS exception** | These are JavaScript DOM property strings, not HTML class attributes. No canonical JS chart API. Chart primitive deferred to Batch 5+ design system phase. |
| Chart text colors | reports_dashboard.html | `text-gray-500` in `<script>` JS `className` | **Remain documented — JS exception** | Same as above — JS-built chart labels. Cannot use `c-muted` in JS string without build tooling. |
| Amber dot indicator | contract_list.html | `bg-yellow-400` on `<span class="w-2 h-2 rounded-full">` | **Remain documented — decorative** | Small colored dot reinforces amber stat-card-amber state. No canonical "status-dot" primitive. Deferred to Batch 5. |
| AI output `<pre>` | contract_detail.html | `bg-gray-50 border border-gray-200 rounded-lg` on `<pre>` | **Remain documented — no primitive** | No canonical code-output or pre-output primitive exists. Adding one is Batch 5 design work. |
| Negotiation notes vertical stack | contract_detail.html | `divide-y divide-gray-200` stack (not list-row) | **Remain documented** | `list-row` is horizontal flex. Vertical date-keyed stacks are a different pattern. Deferred. |
| Responsive grid (contract_detail) | contract_detail.html | `lg:grid-cols-3`, `lg:grid-cols-2` | **Remain documented** | `dash-grid` has no breakpoint equivalents. Responsive layout primitives deferred to Batch 5. |
| Input shape classes | search_results.html, contract_list.html | `rounded-xl px-4 py-3 border` alongside `input-base` | **Remain documented — correct pattern** | `input-base` provides semantic color/bg tokens only; shape/spacing classes are layout, not design token violations. Pattern is intentional and canonical. |
| Asymmetric sidebar grid | search_results.html | `lg:grid-cols-[2fr_1fr]` | **Remain documented** | No canonical asymmetric grid. Custom proportions deferred to Batch 5. |
| Preset row inner border | search_results.html | `rounded-lg border border-gray-100 px-3 py-2` | **Remain documented — no sub-panel primitive** | No canonical "chip-within-panel" or "item-within-panel" primitive. Deferred. |

---

## 6. Accessibility Audit

### Findings During Audit

| Issue | Template | Fix Applied |
|---|---|---|
| 4 sort-arrow SVGs missing `aria-hidden="true"` | contract_list.html | ✅ **Fixed in audit** — `aria-hidden="true"` added to all 4 |
| No SVGs in reports_dashboard.html or identity_telemetry_dashboard.html | — | N/A (no SVGs present) |
| No SVGs in contract_detail.html | — | N/A |
| Filter inputs without labels (type, status, jurisdiction, search mode) | search_results.html | ✅ Previously fixed — `aria-label` added in Step 6 |
| Empty-state SVGs | search_results.html | ✅ Previously fixed — `aria-hidden="true"` in Step 6 |

### Post-Audit Accessibility State

| Template | SVG coverage | Input labels | Keyboard accessible |
|---|---|---|---|
| reports_dashboard.html | N/A (no SVGs) | ✅ | ✅ |
| identity_telemetry_dashboard.html | N/A (no SVGs) | ✅ | ✅ |
| contract_list.html | ✅ 11/11 (7 from Step 4 + 4 fixed in audit) | ✅ search/filter | ✅ |
| contract_detail.html | N/A (no SVGs) | ✅ AI prompt | ✅ |
| search_results.html | ✅ 2/2 | ✅ all filters | ✅ |

### Remaining Accessibility Gaps

| Gap | Template | Severity | Action |
|---|---|---|---|
| Chart bar elements have no text alternative | reports_dashboard.html | Medium | Deferred — requires chart component redesign. Add `role="img" aria-label="..."` wrappers in Batch 5 |
| KPI chart containers have no aria-label | reports_dashboard.html, identity_telemetry_dashboard.html | Low | Deferred — canvas/dynamic elements. Batch 5 |

---

## 7. Token / Primitive Gaps Discovered

| Gap | Severity | Recommendation |
|---|---|---|
| No JS-compatible design tokens for chart colors | Medium | Batch 5: expose CSS variables to JS or provide a chart configuration layer |
| No `status-dot` primitive (colored circular indicator) | Low | Batch 5: add `status-dot-amber`, `status-dot-green`, etc. |
| No code-output / `pre` primitive | Low | Batch 5: add `pre-output` or `code-output` class to base.html |
| No responsive layout primitives (breakpoint-aware grid) | Medium | Batch 5: consider `dash-grid--responsive` or document accepted Tailwind grid patterns |
| No sub-panel item primitive (chip-within-panel) | Low | Batch 5: add `panel-item` for list items inside panel-inner |
| No asymmetric grid primitive | Low | Batch 5: evaluate need; may remain documented Tailwind exception |

---

## 8. Consistency Verdict

**✅ Batch 4 is internally consistent.**

All 5 templates:
- Use `page-wrap` + `page-header` + `page-title` structure ✅
- Use `panel` / `panel-inner` for content blocks ✅
- Use canonical button primitives (`btn-primary-grad`, `btn-ghost`, `btn-secondary`) ✅
- Use semantic text utilities (`c-muted`, `c-link`, `c-danger`, `c-warning`, `c-info`) ✅
- Have 0 inline `style=` attributes ✅
- Have 0 inline event handlers ✅
- Have 0 retired class references ✅
- Have all decorative SVGs marked `aria-hidden="true"` ✅ (post-audit fix applied)

---

## 9. Regression Verdict

**✅ No regressions detected.**

- All forms, links, routes, IDs, data attributes, AJAX endpoints, context variables, and conditionals are verified intact across all 5 templates.
- Tests: 3/3 passing.
- manage.py check: 0 issues.
- Template parse: all 5 OK.

---

## 10. Recommended Batch 5 Scope

Based on gaps discovered, the following work is recommended for Batch 5:

### A. Primitive additions (design system work)
1. `status-dot` — canonical colored dot primitives (`status-dot-amber`, `status-dot-green`, `status-dot-red`)
2. `pre-output` / `code-output` — canonical `<pre>` styling for code/AI output
3. `panel-item` — canonical sub-item within `panel-inner` (replacing ad-hoc border chips)
4. Responsive grid guidance — document accepted Tailwind grid patterns or add `dash-grid--responsive`

### B. Page migration wave (tier-2/tier-3 backlog from DESIGN_ARCHETYPE_MAP.md)
- `theme/templates/contracts/invoice_detail.html`
- `theme/templates/contracts/invoice_list.html`
- `theme/templates/contracts/invoice_form.html`
- `theme/templates/contracts/retention_policy_list.html`
- `theme/templates/contracts/retention_policy_detail.html`
- Organization and settings templates

### C. Accessibility improvements
- Add `role="img" aria-label="..."` to chart container regions in dashboard templates
- Evaluate screen-reader experience for dynamic AI assistant output (`aria-live`)

---

## 11. Audit Sign-off

| Check | Result |
|---|---|
| Template parse (all 5) | ✅ |
| manage.py check | ✅ 0 issues |
| Tests | ✅ 3/3 |
| Inline styles | ✅ 0 |
| Inline event handlers | ✅ 0 |
| Retired classes | ✅ 0 |
| Archetype conformance | ✅ |
| Behavior preservation | ✅ |
| ARIA coverage | ✅ (post-audit fix: 4 SVGs in contract_list.html) |
| Exceptions reviewed | ✅ All documented, decisions recorded |
| Docs updated | ✅ |

**Batch 4 is complete and audit-clean. Batch 5 can begin.**
