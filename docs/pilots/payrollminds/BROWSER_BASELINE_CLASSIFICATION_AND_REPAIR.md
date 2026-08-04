# Browser baseline classification and repair

Status: **NO-GO**. This is evidence, not release approval. No merge,
deployment, executable UAT, release-envelope design, real customer data, or
feature activation occurred.

## Frozen source and execution identities

The validation branch is `codex/payrollminds-browser-baseline-integration` at
`3d1d60a34eebd8544a613e98bd204bd5acba20f1`. GitHub executed PR #157 as its
frozen merge commit `45b45a4a` (branch head into then-current main
`5c73b060d28bca914d570cfc19d205a768ffb3e2`) for both attempts. The branch
was created from the task-start main `4d194dcc0663b94accf4eb892c508fe70cf2d3a7`;
no prohibited PR was rebased.

The manifest contains and CI collected exactly 90 Chromium tests. Existing
stable IDs were retained. The MSA source line moved only because its browser
helper now waits for same-URL postback navigation; its title and ID did not
change.

## Terminal runs

| Evidence set | SHA | Executed | Passed | Failed | Terminal state |
| --- | --- | ---: | ---: | ---: | --- |
| PR #153 clean run 1 | `12c82a34…` | 90 | 38 | 52 | terminal |
| PR #153 clean run 2 | `12c82a34…` | 90 | 38 | 52 | terminal |
| Security-clean run 1 | `45b45a4a` | 90 | 42 | 48 | terminal |
| Security-clean run 2 | `45b45a4a` | 90 | 42 | 48 | terminal |

The final two runs have the same 48-failure set, no skipped, not-run,
collection, setup, teardown, or runner failures, and all 17
`pilot-verification.spec.js` tests pass.

Raw CI evidence is retained under UI Verification run
[`30910072964`](https://github.com/Technivian/CLMOne/actions/runs/30910072964),
attempts 1 and 2. The clean-run references and per-test artifact locations are
recorded in `release-baseline/browser-failures.json`.

## Repairs confirmed on the integrated baseline

1. The PR #153 runner repair remains active: Bash 3.2-safe optional arguments,
   eight-shard execution, and propagated Playwright exits. Its argument harness
   passes locally.
2. PR #154's governed-action expectation corrections remain in place.
3. MSA fixtures now supply `special_conditions` and the threshold acknowledgement
   through the normal form path where applicable. The browser helper also waits
   for the actual same-URL postback before inspecting the next governed state.
   This repaired a CI-only race that left one exception and one review state
   visible despite a submitted resolution; no lifecycle state is mutated
   directly and human confirmation remains required.
4. Focused evidence: the exact shard-7 configuration passes all 11 tests;
   `tests.test_msa_workflow` passes 25 tests; the complete
   `pilot-verification.spec.js` passes 17 tests.

Migration impact is none. The test-only MSA repair does not expand access or
alter authorization, tenancy, audit, or production feature configuration.

## Registry and classification

`release-baseline/browser-failures.json` has one complete record for every
manifest test, including both clean and both security-clean terminal results,
shards, durations, source locations, artifact references, provenance, and
relevance fields.

| Classification | Count | Disposition |
| --- | ---: | --- |
| Terminal pass | 42 | Retained evidence |
| H — Unresolved | 48 | Blocks progression |
| A–G classified failures | 0 | None claimed without proof |

The remaining failures are deliberately **not** placed in category G. Although
their signatures are stable, no complete proof yet establishes the required
non-pilot scope, disabled state, absence of shared/pilot/security impact, and
named remediation ownership for every one. No exception, expiry, or release
envelope has been created.

## Next gate

Root-cause triage must classify and repair every applicable mandatory failure
before any executable UAT or release-envelope work can be authorized. This
baseline is therefore **NO-GO**.
