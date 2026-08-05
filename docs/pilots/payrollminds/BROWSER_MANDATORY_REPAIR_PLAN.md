# Browser mandatory repair plan

Status: **NO-GO**. No repairs are implemented by Prompt 20.

## A-CI-SNAPSHOT (4 tests)

- Classification: A — Infrastructure or isolation defect
- Owner: browser visual-baseline source branch
- Repair: Add reviewed Linux snapshots; no broad acceptance.
- Verification: focused affected tests, then the unfiltered 90-test suite twice on one SHA.
- Migration impact: none expected; confirm during repair.
- Rollback: revert the owning source-PR commit.

## B-PILOT-JOURNEY (11 tests)

- Classification: B — PayrollMinds-critical defect
- Owner: payrollminds browser repair branch
- Repair: Trace route, fixture and policy state; repair smallest canonical-path defect.
- Verification: focused affected tests, then the unfiltered 90-test suite twice on one SHA.
- Migration impact: none expected; confirm during repair.
- Rollback: revert the owning source-PR commit.

## D-SHARED-WORKFLOW (7 tests)

- Classification: D — Shared-platform defect
- Owner: payrollminds shared repair branch
- Repair: Trace view, form and workflow runtime; add focused regression.
- Verification: focused affected tests, then the unfiltered 90-test suite twice on one SHA.
- Migration impact: none expected; confirm during repair.
- Rollback: revert the owning source-PR commit.

## D-SHARED-UI (26 tests)

- Classification: D — Shared-platform defect
- Owner: browser shared UI repair branch
- Repair: Trace canonical component and route; correct implementation or stale assertion only after proof.
- Verification: focused affected tests, then the unfiltered 90-test suite twice on one SHA.
- Migration impact: none expected; confirm during repair.
- Rollback: revert the owning source-PR commit.

