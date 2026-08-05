# Browser mandatory repair plan

Status: **NO-GO**. Prompt 21 and Prompt 22 source-owned repairs are recorded;
the remaining shared-UI and visual-baseline backlog still blocks release.

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
- Resolution: commit `50aae7d4f090e36eff08a1a0b19ad747373185c6` repairs one
  structured-review renderer regression and six stale governed expectations.
- Verification: 7 focused passed, 11 affected-file tests passed, and all seven
  identifiers passed in the one unfiltered 90-test source-SHA run.
- Migration impact: none expected; confirm during repair.
- Rollback: revert the owning source-PR commit.

## D-SHARED-UI (26 tests)

- Classification: D — Shared-platform defect
- Owner: browser shared UI repair branch
- Repair: Trace canonical component and route; correct implementation or stale assertion only after proof.
- Verification: focused affected tests, then the unfiltered 90-test suite twice on one SHA.
- Migration impact: none expected; confirm during repair.
- Rollback: revert the owning source-PR commit.
