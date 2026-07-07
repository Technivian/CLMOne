# Workspace-Mode Containment (Phase 5 of the Product Coherence Redesign)

`Organization.workspace_mode` (`law_firm_ops` / `in_house_clm`) changes what
a tenant sees — sidebar emphasis, dashboard framing, Matter detail sections,
Risk Review framing. This note is the single place documenting how that
branching is allowed to happen, which routes are genuinely shared, and which
are temporary placeholders — so future mode-aware changes have a policy to
follow instead of re-deriving one per PR.

Enforced by [`tests/test_workspace_mode_containment.py`](../tests/test_workspace_mode_containment.py).
That file is the living contract — if a route's classification changes, the
test for it must change in the same commit.

## Policy: shared shell vs mode-specific content

Two, and only two, legitimate shapes for a mode-aware page:

1. **Shared / mode-neutral** — one route, one template, no branching at all.
   The content is equally correct for both tenant types (a document
   repository, a counterparty list). Default to this shape; only leave it
   if the content is genuinely tenant-type-specific.
2. **Shared shell, mode-specific content** — one route, one template,
   internally branching on `workspace_mode` (never on anything else — no
   plan tier, no feature flag, no org name heuristic). The gate must be a
   single `is_in_house_clm` boolean computed once (a `cached_property` on
   class-based views, a local at the top of function-based views) and
   passed to the template — never re-derived per section. `law_firm_ops`
   behavior in the `else` branch must be provably unchanged from before the
   branch was introduced (a preservation test is mandatory, see below).

What is **not** a legitimate shape: removing a mode gate so both tenant
types see identical content "for now." If a page's content should converge,
that's a product decision made explicitly, not a side effect of a
refactor — see the Bucket B correction below.

## Route classification

| Route | URL name | Classification | Notes |
|---|---|---|---|
| Nav sidebar | `nav_config.get_nav_for` | Shared dispatcher | Produces the two nav specs; not itself a page. Zero new routes, zero permission changes — see its own module docstring. |
| Dashboard | `dashboard` | Shared shell, mode-specific content | `contracts.py::dashboard` computes `is_in_house_clm` once; `dashboard.html` branches `{% if is_in_house_clm %}Command Center{% else %}Dashboard{% endif %}` and the sections beneath it. |
| Matter detail | `contracts:matter_detail` | Shared shell, mode-specific content | `MatterDetailView.get_context_data` branches once; `matter_detail.html` renders the Matter Workspace Spine for `in_house_clm`, the original billing/time-entry layout otherwise. |
| Risk Review | `contracts:risk_log_list` / `risk_log_list_legacy` | Shared shell, mode-specific content | `RiskLogListView` picks `legal_intelligence_hub.html` vs `risk_log_list.html` via `get_template_names()`, short-circuiting the unused query path entirely rather than computing-then-discarding it. |
| Org security settings | `organization_security_settings` | Shared / mode-neutral, with a mode **selector** | Not content-per-mode — it's the admin control that sets `workspace_mode` itself (`actions.py::organization_security_settings`, the `save_workspace_mode` action). No change needed. |
| Repository | `contracts:repository` | Shared / mode-neutral | Tenant-scoped, domain-neutral. No workspace_mode reference anywhere in the view or template. |
| Counterparties | `contracts:counterparty_list` | Shared / mode-neutral | Same reasoning. |
| DPA Reviews | `contracts:dpa_review_pack_list` | Shared / mode-neutral | DPA review is a general compliance primitive, not law-firm-exclusive. |
| Approvals | `contracts:approval_request_list` | Shared / mode-neutral | Approval requests are a general legal-ops primitive. |
| Reports | `contracts:reports_dashboard` | Shared / mode-neutral | Generic aggregate reporting. |
| Obligations | `contracts:deadline_list` | **Temporary stopgap** | `nav_config.py`'s in_house_clm nav labels this "Obligations" but points at the pre-existing, unbranched Deadlines page. Deliberate and self-documented in `nav_config.py`'s module docstring — not a dedicated Obligations view. `contracts/services/obligations.py` already exists (a persisted-data `ObligationService` over `Deadline`) but is currently wired only into JSON API endpoints, not this page. Building the dedicated page is explicitly Phase 6+ scope, not this phase. |
| Playbooks | `contracts:dpa_playbook_list` | **Temporary stopgap** | Same treatment, pointing at the DPA playbook positions list "until Clause Library playbooks are merged in" (verbatim from `nav_config.py`). `law_firm_ops` has no "Playbooks" nav item at all, so this stopgap cannot leak the wrong framing into the other mode — it just isn't fully built yet. |

No route in this audit needs to be hidden or redirected for either mode.
The two stopgaps are intentionally visible (removing them would leave no
nav path to Deadlines/Playbook positions at all, which is worse), and their
underlying pages are generic enough — data-driven off `DeadlineType` /
`DPAPlaybookPosition.Topic`, not hardcoded law-firm or CLM copy — that they
don't misrepresent the other mode's domain. The correction this phase makes
is turning that intentionality into a pinned test, not a UI change.

## Bucket B correction (dashboard unification)

A concurrent, uncommitted change (not part of Phases 1-4) had replaced the
dashboard's `is_in_house_clm` gate with `show_command_center = True`
unconditionally — i.e. converged both modes onto one Command Center layout
without an explicit product decision to do so, and rewrote
`tests/test_command_center_in_house_clm.py`'s
`LawFirmOpsDashboardPreservedTests` to assert the *opposite* of what Phase 2
required. That is exactly the "not a legitimate shape" case described above.

It was **stashed, not discarded** (`git stash` on the three affected files
only, since it may represent real in-progress work from another session),
and the working tree restored to the tested Phase 1-4 contract: shared
`dashboard.html` shell, `is_in_house_clm`-gated content, `law_firm_ops`
sees "Dashboard" with the original priority strip/right rail, `in_house_clm`
sees "Command Center" with DPA/MSA conflicts, approvals, and matter
activity. If dashboard convergence is wanted later, it should be scoped as
its own reviewed change — likely still "shared shell, mode-specific
content," just with more content shared between the branches than today,
not zero branching.

## Testing expectations for future mode-aware changes

Any PR that adds or changes `workspace_mode` branching must:

1. Add this route (or confirm an existing entry) to the classification
   table above, in the same commit.
2. If it's **shared shell, mode-specific content**: add both a
   `law_firm_ops`-preservation test (existing behavior/copy unchanged) and
   an `in_house_clm`-content test, following the pattern in
   `tests/test_workspace_mode_containment.py`'s `DashboardContainmentTests` /
   `MatterDetailContainmentTests` / `RiskReviewContainmentTests` — assert the
   *other* mode's markers are **absent**, not just that the page returns 200.
2. If it's **shared / mode-neutral**: add an accessibility test (200 for
   both modes) and, if the route touches organization-scoped data, a
   tenant-scoping test proving cross-org data doesn't leak — `workspace_mode`
   must never become a backdoor around organization scoping.
3. If it's a **stopgap**: pin the nav mapping via `get_nav_for()` (not by
   scraping rendered HTML) and assert the underlying page still renders
   generically, per `StopgapRouteContractTests`.
4. Gate on a single `is_in_house_clm`/`workspace_mode` computation per
   request — never scatter `getattr(org, 'workspace_mode', ...)` calls
   throughout a view or template.
