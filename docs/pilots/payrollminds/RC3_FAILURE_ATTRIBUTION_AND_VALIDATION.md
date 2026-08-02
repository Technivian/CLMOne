# RC3 failure attribution and validation

Status: **NO-GO**. This is an evidence record, not approval evidence. No
production action, merge, customer-data use, inbound-email activation, or
external-AI activation occurred.

## 1. Recorded baseline and environment

| Item | Evidence |
| --- | --- |
| Latest fetched `origin/main` | `4d194dcc0663b94accf4eb892c508fe70cf2d3a7` |
| RC2 pre-evidence SHA | `798d49a1b8bb00f467f099be3ead9aad3372a981` |
| Official Python | 3.12 (`.python-version`: `3.12.13`; CI: `actions/setup-python@v5`, `3.12`) |
| Python application dependency | Django `5.2.16` (`requirements/runtime.txt`) |
| Official browser environment | Node 20, locked `client/package-lock.json`, Chromium installed with `npm --prefix client exec playwright install chromium` |
| Local browser execution | locked client dependencies, Chromium; local host Node was `v25.2.1`, therefore browser result is diagnostic rather than CI-equivalent success evidence |
| Database / services | SQLite is the supported complete-suite test database (`config.settings_test`, in-memory); no PostgreSQL, Redis, or worker is required by the release workflows |
| Complete suite command | `PYTHON=/Users/haroonwahed/Documents/Projects/CLMOne/.venv/bin/python make test` |
| Browser command | `PATH=/Users/haroonwahed/Documents/Projects/CLMOne/.venv/bin:$PATH VERIFY_UI_MODE=browser VERIFY_UI_DEPS_READY=1 bash scripts/verify_ui.sh` |

The CI inspection covered `platform-guardrails.yml` and
`ui-verification.yml`. Quality and tenancy runs migrations, migration-check,
tenant audit and focused tests. Browser CI installs Node 20 dependencies and
Chromium. Before this repair its browser shard step used `continue-on-error`,
which made browser failures advisory.

## 2. Clean-main baseline

Two clean detached-worktree runs at `4d194dcc` were identical:

| Run | Total | Failures | Errors | Skipped | Duration | Exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2,627 | 35 | 19 | 32 | 50.103s | 1 |
| 2 | 2,627 | 35 | 19 | 32 | 50.966s | 1 |

All 54 normalized `FAIL`/`ERROR` test identifiers were identical. These are
stable **pre-existing main debt**, except where a later RC2 comparison below
adds a pilot-only signature. The runner did not fail or vary in either
complete-suite run.

### Normalized main registry

The following are the exact normalized identifiers. Each is test-phase unless
marked otherwise; paths and timestamps are volatile and deliberately omitted.

```
ERROR tests.test_5f_role_walkthrough.AdminJourneys.test_admin_cannot_self_approve_created_contract
ERROR tests.test_5h_expiration_rehearsal.ExpirationEligibility.test_terminal_and_non_active_excluded
ERROR tests.test_contract_launch_setup.NewContractRequestPageTests.test_create_audit_records_derived_risk_and_routing
ERROR tests.test_esign_outbound.DocuSignProviderTests.{test_builds_envelope_and_parses_envelope_id,test_factory_builds_docusign,test_missing_document_raises,test_unconfigured_raises}
ERROR tests.test_esign_outbound.DocumensoProviderTests.{test_detail_exposes_webhook_free_refresh_action,test_factory_builds_documenso,test_refresh_maps_opened_recipient_to_viewed,test_v2_completed_webhook_marks_request_signed,test_v2_provider_creates_and_distributes_envelope}
ERROR tests.test_tasks_inbox.TasksRowComponentTests.test_row_renders_stage_dots_assignee_chip_and_activity_line
ERROR tests.test_workflow_operations.WorkflowOperationsPageTests.{test_designer_hub_owns_templates_and_routing,test_filters_status_and_type,test_operations_page_surface_and_tabs,test_related_surfaces_share_hub_tabs,test_row_maps_stage_type_business_unit_and_progress,test_split_exception_from_title}
FAIL tests.test_5f_role_walkthrough.{AdminJourneys.test_admin_can_create_contract_via_http,CrossTenantNegative.test_bulk_transition_with_foreign_id,CrossTenantNegative.test_client_detail,CrossTenantNegative.test_contract_transition,CrossTenantNegative.test_guessed_and_altered_org_switch,MemberJourneys.test_member_can_read_own_org,StaleSessionAuthz.test_membership_removal_revokes_access_next_request}
FAIL tests.test_ai_clause_review_workflow.AIClauseReviewWorkflowTests.test_incomplete_review_is_truthful_and_surfaces_resolvable_blockers
FAIL tests.test_bolton_redesign.BoltonRedesignTestCase.{test_contracts_list_filters_and_actions,test_contracts_table_structure}
FAIL tests.test_clmone_features.CLMOneFeaturesTests.test_contract_list_has_search_filter_and_table
FAIL tests.test_command_center_in_house_clm.CommandCenterDashboardTests.test_reference_command_center_shell_renders
FAIL tests.test_contract_expiration.ContractExpirationTests.test_non_active_statuses_excluded
FAIL tests.test_contract_launch_setup.NewContractRequestPageTests.{test_new_request_create_ctas_use_standard_teal_button_treatment,test_new_request_workflow_header_is_intake_first_and_compact}
FAIL tests.test_dashboard_work_queue.DashboardQueueRowContentTests.test_queue_rows_render_without_raw_enums_iso_timestamps_or_model_names
FAIL tests.test_demo_command_center.DemoCommandCenterSeedTests.test_dashboard_renders_demo_personalities_and_workspace_links
FAIL tests.test_dpa_workflow.{CommandCenterKanbanProjectionTests.test_generated_dpa_workflow_row_renders_workspace_operational_fields,DPAWorkflowBuilderViewIntegrationTests.test_intake_does_not_expose_pre_generation_governance_or_ai_controls}
FAIL tests.test_lifecycle_three_dimensions.LabelAndCompactHeaderGuardTests.test_compact_header_uses_status_display_dot_stage_display
FAIL tests.test_nda_workflow.NDAWorkflowBuilderIntegrationTests.test_command_center_row_links_back_to_generated_workspace
FAIL tests.test_phase11_backlog_amplifiers.Phase11BacklogAmplifiersTests.test_reassign_options_include_workload_and_sort
FAIL tests.test_phase7_priority_reason.Phase7PriorityReasonTests.{test_approvals_queue_shows_why_this_priority,test_my_work_renders_governance_priority_with_reason,test_obligations_queue_uses_shared_priority_component,test_tasks_queue_includes_priority_reason}
FAIL tests.test_seed_demo_command.SeedDemoCommandTests.test_contracts_span_meaningful_lifecycle_states
FAIL tests.test_settings_hub.SettingsHubViewTests.{test_hub_cards_point_to_real_destinations,test_hub_renders_compact_groups_and_subtitle}
FAIL tests.test_tasks_inbox.TasksCopyQualityTests.test_empty_states_render_exact_specified_copy
FAIL tests.test_workflow_cockpit_regression.WorkflowCockpitRegressionTests.{test_dashboard_renders_mixed_workflow_rows_with_workspace_links,test_reference_workflows_generate_records_and_render_workspaces}
FAIL tests.test_workflow_routing.WorkflowRoutingTests.test_workflow_dashboard_and_detail_surface_routing_endpoints
FAIL tests.test_expressive_design_system.ExpressiveDesignSystemContractTests.{test_command_center_consumes_shared_variants,test_reference_layer_uses_tokens_instead_of_page_hex_values}
```

The 19 errors group into current status/lifecycle form drift, excluded e-sign
provider configuration/isolation, task component drift, and workflow-operation
surface drift. The 35 failures group into authorization expectation drift,
retired or changed Command Center/UI assertions, date/status drift, workflow
surface drift and design assertions. They require ownership-specific repairs;
none is hidden, skipped, or attributed to missing SQLite services.

## 3. RC2 comparison and cumulative attribution

RC2 had the same 54 main signatures plus four failures, for 39 failures and
19 errors (2,639 tests; 32 skips). Targeted cumulative evidence found the four
first present at PR #148 (`416818ab`, included by `0358405e`) and still present
at #149:

```
tests.test_par_sec_002_search_enforcement.ParSec002SearchEnforcementTests.test_client_wall_filters_direct_and_inherited_matter_client_before_counts  AssertionError 0 != 1 (line 138)
tests.test_par_sec_002_search_enforcement.ParSec002SearchEnforcementTests.test_http_search_and_facets_receive_requester_policy  AssertionError 0 != 1 (line 298)
tests.test_par_sec_002_search_enforcement.ParSec002SearchEnforcementTests.test_matter_wall_expiry_and_multiple_walls_are_additive  AssertionError 0 != 3 (line 164)
tests.test_par_sec_002_search_enforcement.ParSec002SearchEnforcementTests.test_policy_query_cost_is_bounded_by_wall_count  AssertionError query count 6 > 5 (line 156)
```

Classification: **intentional server-side private-by-default behaviour with
outdated security fixtures**, not an access-control regression. The repair is
`38748588594bb5baaab52f83d835b389f55f1883` on the earliest owning branch,
PR #148: the visible fixture is member-owned, wall denials stay in place, and
the bounded query assertion accounts for the active-membership lookup. Targeted
result: 10 tests passed in 0.084s. PRs #147, #150, #151 and #152 introduce no
additional complete-suite signatures; #152 is documentation-only.

## 4. Browser runner and CI coverage

Root cause: commit `ec6faf352a497901bb446af26018b400f76358f7` on main added
`"${PLAYWRIGHT_ARGS[@]}"` under `set -u`. Bash 3.2 reports an empty array
expansion as an unbound variable. This existed on main and RC2.

Foundational draft PR #153 contains repair commit
`d21ae2a8cf763c248a9bf226e939f745e82cbe66`. It uses a Bash-3.2-compatible
helper that calls the complete configured suite with no dangling separator for
zero arguments and preserves argument boundaries for one or more arguments.
`scripts/test_verify_ui_playwright_args.sh` passed for unset, empty, one,
multiple, and invalid arguments; an invalid shard exits 2. The repair also
removes browser CI `continue-on-error`, so a failing browser shard fails the
gate and still uploads diagnostic artifacts.

The repaired local entry point reached Playwright and started the configured
90-test suite. It demonstrated genuine legacy browser failures (for example canonical
layout, Command Center, field review, retired invoice surfaces, and mobile
list assertions). Its complete final result is not a green validation and is a
release blocker. No assertion was weakened or snapshot accepted.

## 5. Synthetic UAT, release gate, and RC3

Outcome B is confirmed: PR #152 (`31ffea75`) adds 11 evidence documents only;
it contains no runnable synthetic UAT suite or fixture code. Any earlier claim
that a synthetic UAT selection passed is retracted: documentation generation
is not UAT execution. A narrowly scoped executable suite covering the stated
pilot scenarios remains required before a release-gate PR or RC3 can be valid.

The dedicated complete-release-gate branch has **not** been created because
the prerequisite executable UAT suite and the unresolved stable baseline
failures would make it incomplete. It must run all full-suite, browser,
release-evidence, migration, tenant, dependency, static-security, secret-scan
and executable-UAT jobs without `continue-on-error`, and be made required only
with repository-owner authorization.

No RC3 integration branch or SHA exists: `none`. Consequently, RC3 run one,
run two, complete CI, stack rebase, and merge order are not eligible for green
evidence.

## 6. Required next merge order and recommendation

1. Independently review and merge foundational PR #153 after its CI is green.
2. Rebase the pilot stack onto that immutable merge SHA, then retain PR #148
   repair commit `38748588` in its earliest source branch.
3. Repair every remaining 54 stable main signature with owning teams; do not
   weaken authorization or excluded-feature controls.
4. Add and pass executable synthetic UAT, then open the complete release-gate
   PR and obtain two complete successful RC3 runs on one SHA.

**Final recommendation: NO-GO.** Critical/high blockers are: 54 stable
complete-suite signatures on main, an incomplete browser suite with real
failures, no executable synthetic UAT, no complete release-gate workflow, and
no validated RC3 SHA. Nothing was merged or deployed.
