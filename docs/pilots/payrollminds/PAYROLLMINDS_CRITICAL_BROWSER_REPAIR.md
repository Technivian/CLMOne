# PayrollMinds critical browser repair

Status: **Proposed / NO-GO**. This evidence records a source-owned browser
repair only. It is not a release approval, exception, merge instruction, or
deployment authorization.

## Scope and source

- Source branch: `codex/payrollminds-browser-critical-repair`
- Base: `4f5896840ccab147b5194aac706022d4a53c197a`
- Classification source: `release-baseline/browser-failures.json`, cluster
  `B-PILOT-JOURNEY`.
- Scope: the 11 records assigned to that cluster. No A snapshot records or D
  shared-platform records were changed.

## Root causes and repairs

| Surface | Observed cause | Repair |
| --- | --- | --- |
| DPA, MSA and NDA workspaces | Stale broad text and closed-menu locators | Exact governed labels and explicit canonical actions-menu handling. |
| DPA exception resolution | DPA script looked up MSA drawer IDs and MSA aria labels | Use the existing DPA drawer IDs and labels; no workflow state or permission change. |
| New Contract | History-aware card shelf and canonical launch grid replaced stale fixed-card selectors | Assert the governed MSA card and canonical grid. |
| Buyer demonstration | Synthetic seed titles, password, row navigation, and contract-detail labels changed | Align only with the local-only seed and canonical record UI. |
| Mobile obligations | Dense table is deliberately internally horizontally scrollable | Assert contained table scrolling and hidden page overflow. |
| Pilot gate | View-record is a controlled menuitem; Stage and Status are distinct | Open the menu and preserve both governed dimensions. |

## Completed evidence

Local isolated E2E server: synthetic SQLite database in `/tmp`, AI disabled,
no external provider, real customer data, deployment, or production access.

```text
PLAYWRIGHT_TEST_TIMEOUT_MS=60000 npm --prefix client run test:e2e -- \
  tests/e2e/dpa-workflow.spec.js tests/e2e/msa-workflow.spec.js \
  tests/e2e/nda-workflow.spec.js tests/e2e/new-contract-launcher.spec.js \
  tests/e2e/payrollminds-buyer-demo.spec.js tests/e2e/pilot-gate.spec.js

16 passed (40.2s)
```

This run contains all 11 assigned records. No migration was added. The repair
does not broaden roles, grants, tenant visibility, downloads, exports, or AI
use. Rollback is `git revert` of the source-PR commit(s); the DPA UI repair is
otherwise stateless.

## Remaining release evidence

The mandatory unfiltered 90-test run, full unit suite, security suites, and
independent review remain required. This branch therefore remains **NO-GO**.
