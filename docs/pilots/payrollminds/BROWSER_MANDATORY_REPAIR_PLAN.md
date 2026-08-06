# Browser mandatory repair plan

Status: **NO-GO**. Prompt 21, Prompt 22, and the focused Prompt 23 source-owned
repairs are recorded. Final Linux evidence and the four visual-baseline records
still block release.

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
- Resolution: commits `50aae7d4f090e36eff08a1a0b19ad747373185c6` and
  `361e4739aabc1de38ca51e500d1eae6a2b23d865` repair the structured-review
  renderer, its fast-response duplicate-submit race, and six stale governed
  expectations.
- Verification: 7 focused passed, 11 affected-file tests passed, the duplicate
  guard passed 20/20 stress repetitions, and all seven identifiers passed in
  the local unfiltered 90-test source-SHA run. Final-SHA CI is pending.
- Migration impact: none expected; confirm during repair.
- Rollback: revert the owning source-PR commit.

## D-SHARED-UI (26 tests)

- Classification: D — Shared-platform defect
- Owner: browser shared UI repair branch
- Resolution: implementation commit
  `3f5bb5c3ee65367a2bcd9c86810bad1a3235719a` corrects table containment,
  async error semantics, focus return, owned navigation, stale governed
  selectors, and non-governed file-local screenshot assertions.
- Verification: exact records 26 passed; 13 affected files 34 passed; UI
  integrity 11 passed; final Linux 90-test CI evidence pending.
- Migration impact: none; no model or migration file changed.
- Rollback: revert `3f5bb5c3ee65367a2bcd9c86810bad1a3235719a`.
- Evidence: `SHARED_UI_REPAIR.md`.
