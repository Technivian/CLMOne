# DocClad Design-System Migration Visual Checkpoint

Captured: 2026-07-09  
App: `http://127.0.0.1:8010/` using `e2e.sqlite3`  
Screenshot folder: `/Users/haroonwahed/Documents/Projects/DocClad/evidence/visual-checkpoint-2026-07-09`

## Screenshot Matrix

| # | Screen | Route / URL | Workspace mode | Template | New DocClad shell | DS adapter components | Visual read |
|---|---|---|---|---|---|---|---|
| 1 | Command Center | `/dashboard/` | `in_house_clm` | `theme/templates/dashboard.html` | Yes: global base shell, custom Command Center content shell | No direct adapter; custom `DocCladDashboard` components | Premium CLM direction. Strong queue + right rail, but table/right-rail horizontal collision at 1440px. |
| 2 | Dashboard | `/dashboard/` | `law_firm_ops` | `theme/templates/dashboard.html` | Yes: global base shell, fallback dashboard content | No direct adapter; custom fallback dashboard | Still admin-template-like: generic KPIs, sparse empty queue, no right rail. |
| 3 | New Contract Request | `/contracts/new/start/` | `in_house_clm` | `theme/templates/contracts/contract_template_picker.html` | Yes: global base shell; older `page-wrap`/`arch-header` content shell | No | Good CLM content, but visually card-gallery-like; missing readiness/support rail and richer launch flow. |
| 4 | Organization Session Audit | `/settings/organization-security/sessions/` | `in_house_clm` | `theme/templates/contracts/organization_session_audit.html` plus partials | Yes | Yes: `design_system/page_scaffold.html`, `surface_card`, `dc-ds-*` | Structurally migrated. Rows look incident/error-like because every active session is pink/red. |
| 5 | Operations Dashboard | `/operations/` | `in_house_clm` | `theme/templates/contracts/operations_dashboard.html` plus partials | Yes | Yes: `page_scaffold`, `surface_card`, `dense_admin_list`, `dense_admin_row`, metric grid | Best adapter migration example. Still operational/admin in subject, but visually cohesive and restrained. |
| 6 | Repository | `/contracts/repository/` | `law_firm_ops` | `theme/templates/contracts/repository.html` | Yes; migrated workspace/content shell | Partial: shared queue-derived row conventions, but JS-rendered table not adapter | Premium-ish repository. Good rail/table pattern; still narrow and leaves large blank full-page canvas. |
| 7 | Workflows | `/contracts/workflows/` | `law_firm_ops` | `theme/templates/contracts/workflow_dashboard.html` | Yes; older `workspace-main hero-shell` | No adapter | In-between. Hero shell and dense rows help, but pale card hero and generic summary cards feel admin-dashboard-like. |
| 8 | Approvals | `/contracts/approvals/` | `law_firm_ops` | `theme/templates/contracts/approval_request_list.html` | Yes; `page-wrap`/`arch-header` | Partial: `approval_queue_table` / `wq-table` | Close to migrated queue pattern. Empty state is only a table row, so the page feels underdesigned when empty. |
| 9 | Audit Trail | `/contracts/audit-log/` | `law_firm_ops` | `theme/templates/contracts/audit_log_list.html` | Yes; old `page-wrap`/`arch-header` | No | Functional ledger page. Needs evidence/timeline treatment, stronger filters, and richer audit empty/error states. |
| 10 | Documents | `/contracts/documents/` | `law_firm_ops` | `theme/templates/contracts/document_list.html` | Yes; older `page-header` content shell | No | Major old-layout page. Generic table, native-feeling controls, weak empty state, no document/repository rail. |

## Per-Screen Notes

### 1. Command Center / `in_house_clm`
- Screenshot: `01-command-center-in-house-clm.png`
- What still looks old: none at the page concept level; the table is dense but partly constrained by the right rail.
- Inconsistent: the right rail sits over the horizontal table area at 1440px; queue columns become visually clipped.
- Premium CLM/CMS read: yes, this is the strongest CLM command surface.
- Missing pattern: needs responsive table/rail behavior so the queue and rail do not compete for width.

### 2. Dashboard / `law_firm_ops`
- Screenshot: `02-dashboard-law-firm-ops.png`
- What still looks old: generic KPI cards, empty table row, footer floating high on a mostly empty page.
- Inconsistent: uses the same template as Command Center but feels like a separate product quality tier.
- Premium CLM/CMS read: no; still admin-template-like.
- Missing pattern: no right rail, no richer empty state, no guided work-start panel.

### 3. New Contract Request
- Screenshot: `03-new-contract-request.png`
- What still looks old: self-contained CSS and card grid rather than adapter shell.
- Inconsistent: strong domain copy, but equal-weight cards and repeated CTAs flatten hierarchy.
- Premium CLM/CMS read: mostly yes, but closer to a launcher gallery than a governed intake flow.
- Missing pattern: readiness/status rail, template/playbook recommendation panel, selected-state workflow preview.

### 4. Organization Session Audit
- Screenshot: `04-organization-session-audit.png`
- What still looks old: list rows are plain stacked blocks.
- Inconsistent: red/pink tone implies all sessions are dangerous; action buttons are visually detached from session metadata.
- Premium CLM/CMS read: premium admin/security page structurally, but warning tone is overused.
- Missing pattern: neutral active-session rows, current-session affordance, revoke confirmation emphasis, empty state.
- Risk: contains security/session revocation POST actions.

### 5. Operations Dashboard
- Screenshot: `05-operations-dashboard.png`
- What still looks old: the drill command block is useful but a bit plain.
- Inconsistent: zero-state cards are clean, but lack next-action guidance.
- Premium CLM/CMS read: premium operational admin.
- Missing pattern: richer empty state for jobs and scheduled runs; incident/right-rail summary could help.
- Risk: operational drills/background-job actions may affect queues if wired to POST/API controls later.

### 6. Repository
- Screenshot: `06-repository.png`
- What still looks old: JS table and custom controls still diverge from adapter components.
- Inconsistent: saved-view rail is good, but the main content is narrow within a very tall blank page capture.
- Premium CLM/CMS read: yes, partially.
- Missing pattern: proper empty/saved-view states, right-side record preview drawer pattern, table density consistency.
- Risk: upload document, saved views, bulk selection, API-backed table actions.

### 7. Workflows
- Screenshot: `07-workflows.png`
- What still looks old: hero metric slab, generic cards, and table-first body.
- Inconsistent: pale teal hero border does not match Command Center/adapter surfaces; progress column is visually weak.
- Premium CLM/CMS read: mixed; workflow content is domain-specific, layout still admin-like.
- Missing pattern: workflow pipeline board/rail, empty-state CTA, right-side workflow health summary.
- Risk: start workflow and workflow/template POST forms.

### 8. Approvals
- Screenshot: `08-approvals.png`
- What still looks old: sparse header and empty table row.
- Inconsistent: primary button is visually strong, but the page body collapses to one empty row.
- Premium CLM/CMS read: mixed; queue shell is useful, empty state is not premium.
- Missing pattern: approval empty state, approver SLA summary, right rail for delegated/escalated items.
- Risk: approval creation and approve/reject/delegate actions on populated states.

### 9. Audit Trail
- Screenshot: `09-audit-trail.png`
- What still looks old: native-feeling selects, flat KPI cards, ledger table.
- Inconsistent: audit evidence should feel higher-trust than the generic table styling suggests.
- Premium CLM/CMS read: not yet; admin ledger.
- Missing pattern: timeline/evidence bundle view, filter bar pattern, chain verification detail rail, empty/error state.
- Risk: audit/security content; filters are GET, but export/verification adjacent actions are sensitive.

### 10. Documents
- Screenshot: `10-documents.png`
- What still looks old: classic page header, basic filters, plain table, one-line empty state.
- Inconsistent: Documents overlaps Repository conceptually but is much less migrated.
- Premium CLM/CMS read: no; old admin document table.
- Missing pattern: repository-style views rail, upload/dropzone empty state, OCR queue status rail, table adapter.
- Risk: upload, edit, delete, OCR review, file-download actions.

## Before / After-Style Summary

Before migration, pages read as standard Django admin/SaaS tables: header, filters, table, one-line empty row. The law-firm dashboard, Audit Trail, and Documents still show that pattern.

After migration, the best screens use a legal-operations command surface: sidebar shell, domain-specific header, dense table/list pattern, meaningful status chips, and right-rail or surface-card context. Command Center, Operations Dashboard, Repository, and parts of Approvals show the target direction.

The migration is not complete because the content shells are fragmented: `DocCladDashboard`, `page_scaffold`, `workspace-main hero-shell`, `arch-header`, `page-header`, and page-local panels all coexist.

## Top 10 Visual Inconsistencies Remaining

1. Multiple content shells compete: `DocCladDashboard`, adapter `page_scaffold`, `workspace-main`, `arch-header`, and `page-header`.
2. Empty states vary from polished adapter cards to plain table rows.
3. Table systems differ: adapter dense lists, `wq-table`, JS-rendered Repository table, and old `w-full text-sm` tables.
4. Right-rail behavior is inconsistent and can collide with dense tables on Command Center.
5. Filter controls vary between chips, native selects, custom rail buttons, and old form controls.
6. KPI cards vary in size, border, tone, and semantic emphasis across dashboards.
7. CTA hierarchy differs: copper primary buttons, ghost buttons, small table buttons, and repeated full-width card CTAs.
8. Security/admin rows use warning tones too broadly, especially Session Audit.
9. Workspace-mode pages share navigation shell but not product quality level.
10. Old pages leave large empty canvas and footers floating high when datasets are empty.

## Recommended Next 5 Pages To Migrate

1. Documents: highest old-layout signal; align it with Repository and add upload/OCR empty states.
2. Audit Trail: important trust surface; migrate to evidence/timeline plus verification rail.
3. Approvals: already has shared queue table; add premium empty states, SLA rail, and populated-row polish.
4. Workflows: migrate from generic dashboard cards to workflow pipeline operations pattern.
5. Law-firm Dashboard: align fallback dashboard with Command Center quality so mode switching does not feel like a downgrade.

## Risky Pages / Areas

- Organization Session Audit: session revocation POST actions and security-sensitive content.
- Operations Dashboard: operational/background job controls and diagnostics content.
- Repository: upload, saved views, bulk actions, JS/API-rendered rows.
- Workflows: workflow creation, template publishing, cloning/restoring, step updates.
- Approvals: approve/reject/delegate/create actions, authorization-sensitive states.
- Documents: upload, edit/delete, download, OCR review.
- New Contract Request: workspace-mode-specific CLM launch content and downstream governed drafting flows.

