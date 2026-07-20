# Phase 3C: app-wide table standardization

Status: complete for primary runtime data tables.

This phase closes the Phase 3A deferred work for remaining standard lists,
Workflow Designer tables, and the Command Center Recent Matters queue. The
Contracts Repository table remains the source of truth for the canonical
contract.

## Canonical contract (unchanged)

| API | Responsibility |
|---|---|
| `.dc-ds-table-wrap` | Horizontal containment |
| `.dc-ds-table` | Typography, row hover/focus, numeric alignment |
| `<caption class="sr-only">` + `aria-label` | Accessible table name |
| `scope="col"` | Header semantics |
| `data-col="actions"` + `wq-kebab` | Row actions without clipping |
| In-cell empty state | `design_system/empty_state.html` inside a spanning `<td>` |
| `[data-numeric]` | Right-aligned numeric/money cells |

**Not copied from Repository:** selection, bulk bar, Columns menu, sticky
columns, client sort, or JS-rendered tbody.

## Families migrated in this phase

| Family | Runtime units |
|---|---|
| Core entity lists | `matter_list`, `client_list`, `counterparty_list`, `contract_list`, `deadline_list`, `legal_intelligence_hub` |
| Finance / ops lists | `budget_list`, `budget_detail` (expenses), `invoice_list`, `time_entry_list`, `trust_account_list`, `signature_request_list`, `risk_log_list`, `audit_log_list` |
| Privacy / compliance | `conflict_check_list`, `ethical_wall_list`, `compliance_checklist_list`, `retention_policy_list`, `subprocessor_list`, `transfer_record_list`, `data_inventory_list`, `dsar_list`, `legal_hold_list`, `dpa_playbook_list`, `trademark_request_list`, `document_ocr_queue`, `privacy_dashboard` embeds |
| Workflow Designer | `workflow_template_detail` version history, preview results, activity |
| Command Center | `dashboard.html` Recent Matters (`cc-v3-table` → `dc-ds-table`) |

## Explicitly out of scope

- Design preview templates (`design_preview_*.html`)
- Pattern catalog demos
- Nested tool panels that are not primary record lists (for example document
  compare field diffs, identity telemetry recovery partials) — migrate when
  those surfaces are next redesigned
- Changing Repository itself

## Evidence

- Consumer assertions extended in `tests/test_design_system_phase2a.py`
  (`test_phase_three_a_list_families_use_the_canonical_table_api`) for sample
  migrated lists, Workflow Designer, and the Command Center dashboard.
- Command Center visual baseline mask updated in
  `client/tests/e2e/visual-baselines.spec.js` to target
  `.cc-v3-matters .dc-ds-table`.
