# Canonical Remote Merge Plan

Derived from ancestry, not from numerical PR order (full evidence in
`REMOTE_RELEASE_SOURCE_REGISTRY.md`). The governance/security/UAT stack
(#147–#152, #156) is git-verified already on current main and requires no
action. The only work genuinely missing from main is the browser-repair
chain (#153→#154→#159→#161→#163→#164) and PR #165 (this session's
isolation repair, built independently on current main).

## Sequence actually used

| Step | PR | Head SHA | Prerequisite | Conflict risk | Migration impact | Rollback | Reason for inclusion |
| -- | -- | -- | -- | -- | -- | -- | -- |
| 0 | — | `main@5c73b060` | — | — | — | — | Base: current remote main, git-verified tip |
| 1 | #153 | `12c82a34` | main | Low (stale base, but chain is internally clean) | None | `git reset --hard 5c73b060` on the reconstruction branch, or delete the branch | Root of the real browser-repair chain: removes CI's `continue-on-error` masking, adds Playwright-arg tests |
| 2 | #154 | `ba8be888` | #153 (exact head match) | None (linear stack) | None | same | Adds `openWorkspaceActions()` helper, classifies/fixes governed workspace action expectations |
| 3 | #159 | `4f589684` | #154 (exact head match) | None | None | same | MSA browser postback stabilization |
| 4 | #161 | `0111b10d` | #159 (exact head match) | None | None | same | 11 PayrollMinds-critical browser journey repairs |
| 5 | #163 | `b0f09bbe` | #161 (exact head match) | None | None | same | 7 shared workflow/Contract Record repairs |
| 6 | #164 | `56b08b76` | #163 (exact head match) | None within chain | None | same | 26 shared UI repairs + finance-threshold readiness race repair (folded into the same branch's tail commits) |
| 7 | (merge 1→6 into reconstruction) | `e80e29c3` | current main + #164 tip | **None** — `git merge --no-ff` of #164's tip resolved cleanly against current main with zero conflicts (steps 1–6 collapse into one merge commit since they are a single linear branch) | None (verified: `manage.py check`, see evidence doc) | `git revert -m 1 e80e29c3` | Bring the entire verified chain in as one traceable merge |
| 8 | #165 | `6db7d41b` | main + browser-repair chain | **One conflict**, in `client/tests/e2e/pilot-verification.spec.js` — both #154 and #165 independently fixed the same locator bug in the same test. Resolved by keeping the chain's `openWorkspaceActions()` call (used consistently 11× in the file) and layering #165's `leakedContractId` cleanup-ownership capture on top. | None | `git revert -m 1 70ecf2a7` | Newest, independently-CI-validated work: the isolation repair itself |

Explicitly excluded (rationale in registry §4–5): #155, #158 (byte-identical
duplicates of already-merged #156), #157, #160 (independent branches that
delete security-relevant test files relative to their own base, not part
of the verified chain), #162/MFA.

## Patch-ID duplicate analysis

`git patch-id --stable` was run on #155, #156, and #158's diffs against
their respective bases. All three produced the identical id
`e419f6bb42933b3d553ec9568b2d38828b163d9c`. Only #156's copy (already on
main) is retained; #155 and #158 are not applied, satisfying "every
unique patch applied exactly once."

## Reconstructed branch

`codex/payrollminds-remote-rc-reconstruction`, pushed to remote.

Two merge commits:
1. `e80e29c3` — merges #164's tip (the full #153→#164 chain) into current main. Zero conflicts.
2. `70ecf2a7` — merges #165's tip (browser isolation repair) on top. One conflict, resolved as described above.

Reconstructed source SHA (branch tip): `70ecf2a7` (see evidence doc for the full hash).
