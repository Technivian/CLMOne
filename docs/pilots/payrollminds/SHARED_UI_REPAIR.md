# Shared UI repair

Status: **Proposed / NO-GO pending final Linux CI evidence**. This document is
repair evidence only. It does not authorize merge, deployment, production use,
real customer data, MFA, external AI, inbound email, signatures, portals, or
live integrations.

## Source, ownership, and isolation

- Remote `main` recorded at task start:
  `5c73b060d28bca914d570cfc19d205a768ffb3e2`.
- Foundation: PR #163 head
  `b0f09bbef6a625a8b60b2b9058399f0e7ee7a614` and its approved predecessor
  chain.
- Repair branch: `codex/payrollminds-shared-ui-repair`.
- Draft PR: pending creation.
- Resolving implementation commit:
  `3f5bb5c3ee65367a2bcd9c86810bad1a3235719a`.
- PR #162 head `ab0bf3669939c0f77186671c6ce6eede7ff0851b`
  is not included. No authentication code or configuration changed and no MFA
  activation occurred.
- All browser evidence uses the synthetic E2E workspace. No real customer data
  or production credential was used.

## Exact 26-record working table

The original signatures and artifact references remain on each immutable
registry record in `release-baseline/browser-failures.json`.

| Test ID | Route | Surface/component | Expected behavior | Actual root cause | UI category | Owning shared component |
| --- | --- | --- | --- | --- | --- | --- |
| `fcac23b42f5942783f9d-afc9dfafbd8fbb3b76cf` | canonical workspaces | 390px page shell | No document/body overflow | DPA and Obligations wide tables escaped their scroll containers | Responsive containment | list shell/table wrapper |
| `fcac23b42f5942783f9d-52edd03349ac746fa499` | canonical workspaces | desktop page shell | Current titles and contained layout | Privacy Reviews retained a retired DPA title expectation | Governed semantic expectation | authenticated page header |
| `9e24326c6c84b9aae2de-7d2490bc0040d4b5e052` | `/dashboard/` | Command Center priorities | Workflow-specific links open the owned work | Generic repository target and retired row selectors | Navigation/action hierarchy | Command Center priority/queue rows |
| `e14dd59f59bd59baee8e-1de963c13317565a8828` | billing/time routes | critical form flow | Valid precision is accepted on supported routes | In-house invoice route was retired; test still drove it | Obsolete route assertion | governed route boundary/time-entry form |
| `33901bce72702da02a7d-924b55790fb2e244e84d` | repository/list routes | list controls | Focus and responsive sizing remain operable | File-local screenshot was not a governed Linux baseline | Semantic replacement for snapshot | list controls |
| `33901bce72702da02a7d-46f8026b65fb76299c74` | contract form | form actions/errors | Canonical actions and validation feedback | Stale selector/snapshot expectation | Form semantics | shared form/action bar |
| `33901bce72702da02a7d-cf6b99e1f41720e7eb2f` | Contract Record | note dialog | Modal controls work and focus returns | Close did not return focus to the opener | Focus management | Contract Record note dialog |
| `29ed2972350ecb1766f9-4753e2042891a08768bb` | list family | buttons/badges | Canonical actions and text-backed status | File-local screenshot assertion | Semantic replacement for snapshot | list buttons/status badges |
| `29ed2972350ecb1766f9-7c315d97f921507e9e10` | detail/modal | actions | Visible actions preserve keyboard focus | Hidden global-shell matches and snapshot expectation | Focus/selectors | detail and modal actions |
| `29ed2972350ecb1766f9-e09ae741f62c7a897c38` | settings/admin | destructive action | Primary/destructive hierarchy remains clear | File-local screenshot assertion | Semantic replacement for snapshot | admin action bar |
| `f1901f02f341fbefe840-92185555d7fd73f84572` | dense status routes | badges | Status is textual, semantic, and responsive | File-local screenshot assertion | Non-colour status | canonical badges |
| `0b7a7653555a0bd633f1-7598607be74a1d7e0e62` | Contract Record/document routes | status and drawer | Current state and populated drawer stay operable | Stale selectors and file-local screenshot | Shared state/selectors | status badge and record drawer |
| `cff08f68624ffecd25a5-545a22d21fa4d130cc03` | record form | field/actions | Labels, validation and compact layout persist | File-local screenshot assertion | Form semantics | standard record form |
| `cff08f68624ffecd25a5-9a416527281cc4a7c777` | approval administration | admin form | Shared field partial and panels remain canonical | File-local screenshot assertion | Form semantics | admin form panels |
| `6ac8114eb10074ca31d4-2282b3f4c2acb3e15cb7` | `/contracts/repository/` | async repository table | Loading, error, paging and mobile states are explicit | Error state retained `aria-busy`; failure was not announced | Accessible async state | repository client/table wrapper |
| `6ac8114eb10074ca31d4-97be321eba251589a641` | `/contracts/my-work/` | summary filters | Current non-zero quick views remain inline | Test required a retired always-populated count set | Governed state expectation | My Work summary filters |
| `6ac8114eb10074ca31d4-d4521cc6c2c1d5a62cad` | documents/approvals | list/empty states | Table semantics work with empty or populated synthetic state | Earlier journeys can legitimately create a document | Deterministic state assertion | standard table/empty state |
| `6ac8114eb10074ca31d4-dce0702d4ecd05ca65b9` | clause library | empty table | Canonical table or populated state remains accessible | File-local screenshot assertion | Semantic replacement for snapshot | standard table/empty state |
| `ef99e9621f4244b0bbc2-bacaa791acb7959a2d87` | repository | shell/tabs | Keyboard-operable canonical list tabs | Retired broad selector/snapshot | Stale selector | workspace/list shell |
| `ef99e9621f4244b0bbc2-161a7278eaf25f5f0fd5` | documents/clause library | compact headers | Current action hierarchy stays contained | Retired title/action selector and snapshot | Header semantics | list page header |
| `ef99e9621f4244b0bbc2-30d4582f3ac064a46bd6` | approval rules | administration shell | Workflow Designer owns approval rules | Test expected retired standalone Approvals shell | Obsolete route/component assertion | Workflow Designer shell |
| `779d1e2ca76bed658459-ef73927f33eef8ba5272` | legacy clients/counterparties | create form | Canonical counterparty creation is labelled and focusable | In-house Client surface is retired | Obsolete route assertion | standard Counterparty form |
| `4f7fc92a3a82dbbe723a-f4b58c519c9a4a8b7ff5` | counterparties/privacy | governance forms | Shell header, actions, labels and focus work | Retired Client/DPA terminology and snapshot | Governed semantic expectation | standard record form |
| `4f7fc92a3a82dbbe723a-6c913a7f199853eb98b7` | compliance/governance | forms | Subtitles and action hierarchy fit compact screens | File-local screenshot assertion | Semantic replacement for snapshot | governance form shell |
| `a0f8a50d9100f29fce8e-b4bc5a22a5e8d17a654a` | `/dashboard/` | Command Center mobile | 390px remains operable with explicit states | Retired Command Center selectors/snapshot | Responsive/state semantics | Command Center v3 |
| `a0f8a50d9100f29fce8e-e6913fb8435b5f8e86c0` | `/dashboard/` | section links | Toolbar links use canonical link buttons | Retired selector/snapshot | Stale selector | Command Center toolbar |

Registry extraction selected exactly 26 `D-SHARED-UI` records. It selected no
`B-PILOT-JOURNEY`, `D-SHARED-WORKFLOW`, or `A-CI-SNAPSHOT` record.

## Evidence-backed root-cause subclusters

| Subcluster | Test IDs | Common cause and smallest repair | Accessibility/responsive/pilot impact |
| --- | --- | --- | --- |
| Responsive table containment | `fcac…6cf`, `6ac…5cb7` | Add layout/paint containment to the existing DPA and Obligations scroll wrappers; keep the 1,180px tables internally scrollable | Removes page-level mobile overflow without clipping table content |
| Accessible async and dialog state | `339…eb2f`, `6ac…5cb7` | Clear repository loading state before showing an alert; return note-dialog focus to its opener | Announces failures and restores predictable keyboard position |
| Operational navigation ownership | `9e24…e052`, `ef99…5272`, `779d…5272`, `e14d…8828` | Use workflow-owned links and verify retired routes fail closed | Users reach the intended work without reviving legacy modules |
| Governed terminology and canonical markup | `fcac…a499`, `339…9c74`, `0b7a…0e62`, `6ac…a641`, `ef99…e8ba`, `ef99…0fd5`, `4f7f…98b7`, `a0f8…86c0` | Align selectors with Privacy Reviews, Counterparties, current status badges, visible shell content, and Command Center v3 | Preserves accessible names and current product language |
| Semantic replacement for non-governed local screenshots | `339…e84d`, `339…bb3b`, `29ed…e84d`, `29ed…e10`, `29ed…8c38`, `f190…4572`, `0b7a…0e62`, `cff0…5cb7`, `cff0…c777`, `6ac…65b9`, `ef99…a641`, `4f7f…98b7`, `4f7f…eb98`, `a0f8…654a`, `a0f8…86c0` | Retain each browser test but replace file-local Darwin screenshot assertions with explicit role, name, focus, status, error and containment assertions | Increases cross-platform determinism while leaving the five governed visual-baseline tests and all assets untouched |
| Synthetic-state determinism | `6ac…62cad` | Accept either the canonical empty state or a real row created by an earlier journey, while requiring the table/link semantics in both states | Full-suite order no longer changes the result; no fixture or product mutation |

## Implementation corrections and enterprise UI contract

- Command Center priority titles now use the existing owned workspace target;
  the explicit review action uses the feature-specific target. The visible
  hierarchy is unchanged except for truthful navigation.
- Repository errors end loading state and use an alert region. Restricted
  metadata, counts, and errors remain tenant scoped by the unchanged endpoint.
- Contract note dialogs return focus to the button that opened them. No note,
  audit, or Contract Record mutation rule changed.
- DPA and Obligations tables remain fully available through horizontal table
  scrolling while document/body overflow is prevented at 390px.
- Browser coverage now asserts semantic HTML, accessible names, keyboard focus,
  text-backed status, responsive containment, loading/error state, and route
  ownership. No test was skipped, retried, excluded, removed, or broadly
  accepted, and no snapshot was regenerated.

Lower-level coverage was added for the Command Center targets, repository error
semantics, dialog focus return, and table containment. No server-side business
rule, permission, lifecycle, workflow authority, provenance, DocumentVersion,
audit, external provider, or authentication path changed.

## Validation evidence

| Gate | Result |
| --- | --- |
| Exact shared-UI registry selection | 26 passed; 0 failed; 0 skipped; 0 not run |
| Complete affected Playwright files | 34 passed |
| Modified lower-level component/template suites | 91 passed |
| UI integrity suites | 11 passed |
| PR #161 preservation files | 16 passed |
| PR #163 exact owned records | 7 passed |
| PR #163 affected files | 11 passed |
| PayrollMinds verification | 17 passed |
| Duplicate-submit stress | 20/20 passed |
| Focused security/access/tenancy suite | 192 passed |
| Full 90-test browser run | Final Linux CI pending. Local macOS diagnostic: all 85 non-visual tests pass; the five visual tests cannot resolve Linux-only assets on macOS. |
| Full Django comparison | 2,627 run; 34 failures / 13 errors / 32 skipped. PR #163: 35 failures / 13 errors; normalized signature comparison is running against the exact PR #163 SHA. |
| Configuration/schema | Django check passed; no migration drift; NULL-organization audit passed after applying the existing migration set. |
| Accessibility/design | UI integrity 11 passed; contrast passed; anti-drift passed. |
| Dependency/security | `pip-audit`: no known vulnerabilities; Bandit high: passed; client and theme runtime npm audits: zero vulnerabilities; diff secret scan passed. |
| Frontend build | Production Tailwind/shell build completed; generated output was not retained because this repair changes no Tailwind source. |

## Screenshot hygiene, migrations, rollback

The eight browser-generated controlled-pilot screenshots were moved to
`/tmp/clmone-prompt23-generated-screenshots/` and their tracked source versions
restored. Playwright failure artifacts were moved under
`/tmp/clmone-prompt23-browser-artifacts/`. None is staged or committed. The
five files under `visual-baselines.spec.js-snapshots/` and the visual spec are
byte-for-byte unchanged from the PR #163 foundation.

No model or migration file changed. Rollback is a revert of implementation
commit `3f5bb5c3ee65367a2bcd9c86810bad1a3235719a`; it removes only the UI/test
corrections and has no data rollback step.

## Current recommendation

Unresolved shared-UI count: **0 in focused evidence; final registry closure is
conditional on the final Linux CI run**. Recommendation remains **NO-GO** until
the complete browser run proves exactly 86 passed and only the four unchanged
`A-CI-SNAPSHOT` records fail, the full Django signature comparison is complete,
and the draft-PR evidence is updated on its final SHA.
