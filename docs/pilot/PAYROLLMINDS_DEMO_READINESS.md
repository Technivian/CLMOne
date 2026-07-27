# PayrollMinds Demo Readiness

**Status:** Ready — final GO audit passed (synthetic, controlled design-partner demo only)
**Baseline assessed:** current repository `main` at `fc547ae0` (the request
named `618d4b3b`; the current branch had already advanced through the UI merge)
**Data policy:** fictional, synthetic data only; no PayrollMinds, customer,
employee, or payroll data

## Readiness assessment

| Journey step | Classification | Demo position | Blocking issue / focused action |
|---|---|---|---|
| 1. New contract request | Demo-ready | New Contract opens the governed intake with privacy, lifecycle, renewal, and notice inputs. | Frame it as the entry surface, not a live replay of the seeded record. |
| 2. Client, countries, value, vendors, privacy-risk intake | Demo-ready | The Global Payroll Transformation SOW visibly carries its synthetic value, countries, vendors, privacy flags, and review route. | Point to the record and source document; do not enter data during the session. |
| 3. NDA, MSA, SOW, DPA requirements | Demo-ready | The synthetic workspace contains all four agreement types and linked MSA/SOW/DPA context. | Keep the story on these four records; avoid unrelated templates. |
| 4. Legal, Finance, and Privacy review | Demo-ready | Legal is approved; Finance and Privacy are visibly pending; DPA review has three owned risks. | Do not claim automatic routing beyond the displayed synthetic route. |
| 5. Conditional approval | Demo-ready | Finance is visibly pending because the synthetic SOW is EUR 240,000. | Use the Finance role view as the proof point; do not submit a decision. |
| 6. Signature preparation | Demo-ready | The SOW has a pending synthetic signature request; the MSA shows completed synthetic execution evidence. | Do not send a real signature or claim provider integration. |
| 7. Contract record creation | Demo-ready | The record workspace renders provenance, linked MSA, source document, conditional approval, signature preparation, and contract-scoped activity. | The seed is a demonstration snapshot, not an auditable live request-to-record replay. |
| 8. Obligations, milestones, renewals, and notices | Demo-ready | Seeded deadlines visibly cover the MSA renewal-and-notice decision, subprocessor review, milestone, pricing indexation, and NDA expiry. | Describe them as tracked work only; do not imply automated notices. |
| AI assistance / redaction | Out of scope | AI is disabled for this demonstration. | No synthetic AI path is approved in this tranche. |
| Ethical walls, full analytics, production controls | Out of scope | Not shown or claimed. | Keep hidden or avoid during the walkthrough. |

## Remediation completion — 2026-07-27

The documented route is server-enforced read-only only for the synthetic
`payrollminds-demo` workspace. The final GO audit passed after a clean reset,
focused endpoint-permission tests, browser smoke, refreshed screenshots, and
backup walkthrough validation. Other workspaces retain their normal behavior.

## Prior rehearsal result — 2026-07-25

The local reset completed, and all eight presenter scenes were rendered at a
2048 × 1072 desktop viewport using the fictional role accounts. The
contract-scoped route is the approved activity/audit surface for the demo.

| Scene | Result | Rehearsal note |
|---|---|---|
| New contract request | Ready | Intake, privacy/risk, lifecycle, renewal, and notice sections render. |
| Global Payroll Transformation SOW overview | Ready | Value, governed stage, linked MSA, document, pending signature, and recent activity are legible. |
| SOW document record | Ready | The document renders as a normal synthetic record without extraction/AI-review copy. |
| Finance approval | Ready | The Finance account sees the EUR 100,000 conditional approval; decision controls are absent. |
| Privacy review | Ready | The Privacy account sees the DPA pack and the three human-owned risk positions; no decision can be submitted. |
| Signature preparation | Ready | The pending synthetic request, external reference, and unsent state are clear; all mutation controls are absent. |
| Contract-scoped activity and audit history | Ready | Use the SOW's **Recent activity → View all** route; it is scoped to the story. |
| Obligations and dates | Ready | Renewal, subprocessor review, milestone, pricing, and NDA deadlines render. |
| Global audit ledger | Out of scope — absent | The route is not linked from the presenter surface. Contract-scoped activity remains the audit evidence for the story. |

### Defect fixed during rehearsal

The synthetic SOW document record exposed a text-extraction review and a
confidence score despite AI being disabled. The seed now removes that
presenter-visible OCR review for the SOW, and a regression assertion protects
the rule. No AI or extraction capability is enabled or shown in the golden
route.

## Remaining limitations

1. The story is a seeded operational snapshot, not an end-to-end playback of
   every state transition; state this plainly.
2. The global audit ledger and the known approval-SLA audit-fixture issue are
   outside the presenter route. Do not claim complete audit-chain robustness
   or SLA escalation.
3. No live e-sign, notice delivery, AI, data residency, Ethical-Wall,
   analytics, or redaction assurance is demonstrated.
4. No real PayrollMinds, client, employee, or payroll data is permitted.

## Synthetic workspace design

Run locally only:

```bash
PAYROLLMINDS_DEMO_PASSWORD='choose-a-local-password' \
  .venv/bin/python manage.py seed_payrollminds_demo --reset
```

The command refuses a deployed platform, uses the `payrollminds-demo` tenant,
and leaves unrelated workspaces untouched. It creates fictional `.example`
accounts for Legal Operations, Legal, Procurement, Finance, and Privacy.

The central record is **Global Payroll Transformation Engagement —
Implementation SOW**: EUR 240,000, Netherlands/Germany/Belgium/United Kingdom,
Atlas Workforce and CloudPay as fictional vendors, personal-data and
cross-border flags, and linked MSA/DPA context. The associated NDA, MSA, SOW,
and DPA are deliberately synthetic demonstration paper.

## Focused implementation slices

1. **Demo safety and reset — complete:** local-only reset, fictional addresses,
   separate privacy role, agreement set, conditions, documents, signatures,
   audit entries, and deadlines.
2. **Golden-route rehearsal — complete:** entry, review, record, activity,
   signature, and obligations routes were verified and screenshots captured;
   only the presenter-visible extraction copy needed correction.
3. **Presenter controls — complete:** decision, review, signature, and
   obligation mutations are absent in the demo UI and rejected server-side;
   technical audit surfaces are absent.
4. **Evidence pack — complete:** focused tests, reset regression, browser
   smoke, final screenshots, and a validated local backup walkthrough are
   recorded below. No broad platform refactor was undertaken.

## Required evidence

Run the focused suite before recording or a design-partner session:

```bash
.venv/bin/python manage.py test \
  tests.test_seed_payrollminds_demo \
  tests.test_login_presentation \
  tests.test_msa_workflow \
  tests.test_document_versioning \
  tests.test_document_storage_download \
  tests.test_approval_workflow \
  tests.test_dpa_review \
  tests.test_cross_tenant_isolation \
  tests.test_workflow_audit_trail \
  tests.test_obligations_workspace \
  tests.test_ui_click_integrity \
  --settings=config.settings_test
```

This covers the requested login/roles, request-to-record primitives, document
rendering and storage, approvals/review, tenant isolation, activity/audit,
obligations, route integrity, and reset. The seed command regression test is
the demo-reset proof. A green focused suite supports a demonstration only; it
does not establish production readiness.

Related presenter artifacts:

- [Demo script](PAYROLLMINDS_DEMO_SCRIPT.md)
- [Eight-slide pitch outline](PAYROLLMINDS_PITCH_OUTLINE.md)
- [Pilot proposal](PAYROLLMINDS_PILOT_PROPOSAL.md)
- [Security and maturity statement](PAYROLLMINDS_SECURITY_AND_MATURITY.md)
- [Backup recording plan](PAYROLLMINDS_BACKUP_RECORDING_PLAN.md)
- [Presenter click-path checklist](PAYROLLMINDS_REHEARSAL_CHECKLIST.md)
- [Final screenshots](screenshots/payrollminds-rehearsal-20260727/README.md)
- [Validated backup walkthrough](recordings/payrollminds-rehearsal-20260727/README.md)
