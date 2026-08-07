# PayrollMinds browser source ownership and merge plan

Status: **Proposed / NO-GO**. This is attribution evidence, not a release
approval, exception, merge instruction, or deployment authorization.

## Recorded sources

| Item | SHA / state |
| --- | --- |
| Current remote main at attribution start | `5c73b060d28bca914d570cfc19d205a768ffb3e2` |
| Frozen security-clean source baseline | `3d1d60a34eebd8544a613e98bd204bd5acba20f1` |
| CI merge SHA used for the recorded 90-test runs | `45b45a4a` |
| PR #153 runner repair | Open draft, `12c82a34c3d02227287dd97f56d758443082559e` |
| PR #154 browser expectation and MSA fixture repair | Open draft, `ba8be8884296cde7cda7e644a2d6086082ce4866` |
| PR #155 dependency remediation | Closed, `acf10c36898c5dca59397af6da753458fb212efd`; superseded for ownership |
| PR #157 integration/evidence branch | Open draft, `368c879e3649833dd3e8b103ae9048b39cd3bf79` |
| PR #158 replacement dependency-security PR | Open draft, `25585c0b7b171931ce90519317d01201c1e87a1e` |

## Ownership normalization

| Change | Current branch/PR | Correct owner | Permanent PR | Reason |
| --- | --- | --- | --- | --- |
| Safe browser runner argument propagation | PR #153 | Runner source branch | PR #153 | Runner-only correction with dedicated Bash validation. |
| PostCSS and brace-expansion remediation | Closed #155 / integrated #157 | Security source branch | PR #158 | Dependency and lockfile change must not be stranded in integration evidence. |
| Cryptography remediation | Closed #155 / integrated #157 | Security source branch | PR #158 | Runtime security pin needs independently reproducible security evidence. |
| Governed browser expectations | PR #154 | Browser repair source branch | PR #154 | Corrects stale role/menu visibility assertions without changing product controls. |
| MSA `special_conditions` fixture | PR #154 / integrated #157 | Browser repair source branch | PR #159, `96c31f32` | Test fixture must complete canonical drafting input; it is not a platform change. |
| MSA same-URL postback wait | Unique integration commit `3d1d60a3` | Browser repair source branch unless code-path analysis proves shared application repair | PR #159, `4f589684` | Synchronization correction must not remain integration-only. |
| Browser manifest and failure registry generation | PR #154 / #157 | Attribution/evidence branch | This branch | Evidence and classification are not product ownership. |
| Shared workflow/Contract Record repairs | Prompt 22 | PayrollMinds shared repair branch | `codex/payrollminds-shared-workflow-repair`, `50aae7d4` | One renderer regression and verified stale governed expectations; permanent change is source-owned. |
| Shared UI repairs | Prompt 23 | Browser shared UI repair branch | `codex/payrollminds-shared-ui-repair`, `3f5bb5c3` | Permanent semantic, responsive, focus, route and test corrections remain isolated from workflow and MFA ownership. |

## Proposed foundation order

1. PR #153 runner repair;
2. PR #158 dependency-security remediation;
3. shared workflow repair, `50aae7d4`, after source tracing proved the
   structured-review renderer regression and isolated six stale expectations;
4. PR #154 browser expectation repair, then PR #159 fixture and postback repair;
5. Prompt 23 shared UI repair, based on the PR #163 head;
6. integration/evidence branch.

No item above is authorized to merge until its required reviews and CI gates are
complete. Focused source evidence resolves the 11 category-B, seven shared
workflow/record, and 26 shared-UI records. The only intended unresolved browser
records are the four `A-CI-SNAPSHOT` visual baselines; final Linux CI must prove
that exact residual set. No category-G candidate or exception exists.

## Addendum: PAR-SEC-002 security repair and reconstruction

| Item | Change | Correct owner | Permanent PR |
| --- | --- | --- | --- |
| PAR-SEC-002 search-enforcement fixture repair | `test_par_sec_002_search_enforcement.py` fixtures aligned to the already-governed private-by-default ownership boundary (`416818ab`); zero production code changed | Security source branch | `codex/par-sec-002-search-enforcement-repair`, PR #167, `c7a6b7ba` |
| pypdf CVE-2026-71852 remediation | `requirements/runtime.txt` pin `6.14.2` → `6.15.0` | Security source branch | Integrated in PR #167, `e742a3dc` |
| Release stack reconstruction on security base | Merges the security repair (PR #167) on top of the browser-repair chain tip and PR #165's tip, superseding the prior `codex/payrollminds-remote-rc-reconstruction` (PR #166) as the current source-of-truth reconstruction | Attribution/evidence branch | `codex/payrollminds-remote-rc-security-reconstruction`, PR #168, `7b237912` |

Full root-cause, authorization-path, and test evidence for the PAR-SEC-002 repair is recorded in `PAR_SEC_002_SEARCH_ENFORCEMENT_REPAIR.md`. This addendum does not change the proposed foundation order above; the security repair sits between item 2 (dependency-security remediation) and item 6 (integration/evidence branch), since it depends on nothing but plain `main` and is itself a prerequisite for any UAT-gate evidence. Still **NO-GO** — nothing above is merged or deployed.
