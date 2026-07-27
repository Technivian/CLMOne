# PayrollMinds Presenter Click-Path Checklist

**Use:** local, reset synthetic workspace only.
**Readiness:** Ready — final GO audit passed on 2026-07-27.
**Presenter mode:** the `payrollminds-demo` workspace is server-enforced read-only
for this route. AI, extraction, Ethical Walls, analytics, SLA escalation, live
signatures, and the full audit ledger are not part of the demonstration.

## Before opening the meeting

1. Run the documented reset command:

   ```bash
   PAYROLLMINDS_DEMO_PASSWORD='<local-demo-password>' \
     .venv/bin/python manage.py seed_payrollminds_demo --reset
   ```

2. Open `https://127.0.0.1:8060/login/` and use only the fictional
   `payrollminds-demo` accounts.
3. Do not create, edit, approve, reject, return, submit, complete, or sign
   anything. Those presenter-facing controls are absent and their backed
   endpoints reject requests in this workspace.

## Presenter path

1. **Boundary — 1 minute.** `/dashboard/` — sign in as Legal Ops. State that
   this is a local synthetic operational snapshot, not a production workflow
   or real PayrollMinds/client/payroll data. Confirm the technical audit card
   and global audit route are absent.
2. **Agreement set — 2 minutes.** `/contracts/repository/` — open
   **Global Payroll Transformation Engagement — Implementation SOW** and point
   out the fictional NDA, MSA, SOW, DPA, value, countries, vendors, and
   privacy context.
3. **Contract record — 2 minutes.** `/contracts/186/` — point to its EUR
   240,000 value, Atlas Workforce B.V., approval stage, source document,
   prepared signature, and expiry milestone. There is no review-decision CTA.
4. **Agreement paper — 1 minute.** `/contracts/186/?tab=documents`, then
   `/contracts/documents/80/` — show the synthetic version-one source
   document. Do not describe it as extracted or AI-reviewed.
5. **Conditional Finance review — 2 minutes.** `/contracts/approvals/` — use
   the Finance row to explain the EUR 100,000 condition. The displayed
   Approved/Rejected controls are list filters, not decision controls; there
   is no Approve, Reject, or Return action.
6. **Privacy review — 2 minutes.** `/contracts/dpa-reviews/23/` — show the
   three human-owned risk positions: breach timing, audit right, and liability
   alignment. There is no Submit decision control and no AI/extraction path.
7. **Signature and activity — 3 minutes.** `/contracts/signatures/32/`, then
   `/contracts/186/?tab=activity` — show the prepared synthetic reference and
   contract-scoped activity/audit history. Do not use a signature action or
   leave the contract scope.
8. **Operate the commitment — 2 minutes.** `/contracts/obligations/` — show
   the MSA renewal and notice decision, subprocessor notification review,
   implementation milestone, pricing indexation, and NDA expiry. Complete and
   other obligation-mutation controls are absent. Describe these as tracked
   dates, not delivered notices.

The numeric record IDs are intentionally checked after each reset. If a reset
creates a different local ID, find the named synthetic record in the
repository; do not substitute another workspace or record.

## Final scene inventory

| Scene | Status | Screenshot |
|---|---|---|
| Dashboard boundary | Ready — final browser smoke | `01-dashboard.png` |
| Contract repository | Ready — final browser smoke | `02-contracts.png` |
| SOW overview | Ready — final browser smoke | `03-global-payroll-sow-overview.png` |
| SOW documents | Ready — final browser smoke | `04-sow-documents.png` |
| SOW document record | Ready — final browser smoke | `05-sow-document-record.png` |
| Finance approval | Ready — final browser smoke | `06-finance-approval.png` |
| Privacy review | Ready — final browser smoke | `07-privacy-review.png` |
| Signature preparation | Ready — final browser smoke | `08-signature-preparation.png` |
| Contract activity history | Ready — final browser smoke | `09-contract-activity-history.png` |
| Obligations, renewal, and notice | Ready — final browser smoke | `10-obligations-and-dates.png` |

See the detailed inventory in
[`screenshots/payrollminds-rehearsal-20260727/README.md`](screenshots/payrollminds-rehearsal-20260727/README.md).

## Fallback

If any screen cannot be reached, stop rather than improvise. Reset once,
restart the local server, and use the backup walkthrough. Do not substitute
real data, enable AI, or use another unfinished workspace.
