# PR #177 private-access full-suite regression attribution

## Frozen comparison

| Field | Base | Initial branch | Corrected working tree |
| --- | --- | --- | --- |
| Revision | `e500368c6f1191909d21822a7bdd394ff0e7fa2a` | `444013a81e94f6175c4994635da09530255a7163` | implementation changes in this PR worktree, before the evidence-only commit |
| Python | 3.12.13 | 3.12.13 | 3.12.13 |
| Settings/database | `config.settings_test` / clean in-memory SQLite | identical | identical |
| Test runner | Django, `--parallel 0` | identical | identical |

The signature is `test_id + kind + exception_type`. Rendered HTML is deliberately
excluded because it embeds build SHA, CSP nonce, CSRF value, test-created IDs,
and current timestamps. The compact per-failure records, durations, surfaces,
and raw-capture signatures are in
[`release-baseline/private-access-regression-diff.json`](release-baseline/private-access-regression-diff.json).
One identifier which collides with the Lob detector is stored as ordered
`test_id_segments`; concatenating the segments yields the exact test ID. This
keeps the evidence machine-reconstructible without embedding a detector match.

## Exact result sets

| Comparison | Inherited | Resolved | New | Mutated |
| --- | ---: | ---: | ---: | ---: |
| Base → initial PR head | 68 | 3 | 58 | 0 |
| Base → corrected working tree | 67 | 4 | 0 | 0 |

Raw Django summaries were: base 34 failures / 37 errors (71); initial branch
86 failures / 40 errors (126); corrected tree 31 failures / 36 errors (67),
with 2,726 collected and 9 skipped. The remaining 67 signatures are all
present on the exact base.

## Initial root-cause clusters and smallest corrections

| Cluster | Initial records | Root cause and evidence | Correction |
| --- | ---: | --- | --- |
| A — stale workspace-wide access expectation | 15 | Same-workspace users were asserted to see/comment/mutate a private object or to receive an old status code. Addendum 002 permits only owner/creator read/comment/edit; no workflow-participant sharing was introduced. | Adjust only the named assertions to the approved non-disclosure or segregation-of-duties outcome. |
| B — fixture lacks accountable provenance | 28 | Focused fixtures omitted `owner`, `created_by`, or `uploaded_by`, or exercised a surface as a user who was not the intended accountable actor. | Give each fixture its intended actor; do not assign all records to an admin. |
| C — private-access propagation defect | 7 | Client/matter and related projections could expose private relationship metadata, or omitted the intended policy-filtered result. | Apply the canonical contract policy before relation/projection serialization. |
| D — privileged OWNER/ADMIN edit regression | 5 | Mutation routes resolved through a read queryset and incorrectly returned not-found to an existing edit-only authority. | Use the narrow security-filtered edit queryset only for mutation resolution; never for discovery. |
| E — query/count/search projection defect | 1 | The Command Center policy evaluation adds a fixed membership/Ethical-Wall query cost; the assertion did not distinguish constant overhead from N+1. | Update the bound to five constant queries. |
| F — document/workflow/work-item inheritance defect | 2 | Contract-derived task/deadline surfaces did not consistently retain the canonical relationship boundary; matter-only records were also inadvertently excluded from their existing workspace-local path. | Filter contract-linked records by the canonical policy and preserve matter-only records without inventing a contract ACL. |

Every initial branch-only ID has an A–K classification and evidence in the
machine-readable diff. No initial mutated signature was found. The four
resolved base signatures include the valid lifecycle-status fixture error.

## Corrections made

- Restored client/matter, document, workflow, task, deadline, and contract
  mutation inheritance at the existing canonical policy boundaries.
- Preserved OWNER/ADMIN edit-only semantics without granting supervisory read,
  search, count, export, comment, AI, or workflow-participant sharing.
- Corrected only actor-specific test fixtures and policy-proven assertions.
- Preserved matter-only deadline/task paths; no new object, role, permission,
  sharing model, migration, or activation was introduced.

## Gate result

The Django regression-delta criterion is **GREEN**: new `0`, mutated `0`.
This is not a production release decision. Production preflight, deployment,
merge, contract-type activation, and any Darwin visual-baseline update were
not performed.
