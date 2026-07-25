# Playwright baseline classification

Baseline: `809b576043f1aecef2d22da2d89d7df625b6eb89`; isolated migrated SQLite
checkout, Node 25 / Chromium headless, one worker. Raw result: **39 passed, 41
failed, 6 timed out**. The exact 47 identities, outcomes, signatures, owners,
expiry and evidence fields are in `PLAYWRIGHT_BASELINE.json`.

This is a temporary regression baseline, not a release or activation exception.
The canonical NDA journey remains evidence-limited; a targeted canonical NDA
browser journey must be green before activation.

| Group | Count | Classification | Evidence and disposition |
| --- | ---: | --- | --- |
| PWB-01 visual snapshots | 12 | VISUAL_BASELINE_DRIFT | Screenshot pixel/size mismatches in Phase 1–3 components and visual-baselines. Quality owns snapshot review; expire 2026-08-31. |
| PWB-02 stale surface contracts | 21 | STALE_ASSERTION | Exact selector, title, route and visibility assertions observe redesigned surfaces. No application change is authorized here; owning surface tests must be reconciled. |
| PWB-03 generated fixture links | 3 | FIXTURE_OR_TEST_DATA | Timestamped contract titles are not found after the generated workflow path. Reproduce fixture creation before changing a route or assertion. |
| PWB-04 timeout outcomes | 6 | UNKNOWN | Three 60-second and three 180-second timeouts are preserved as timed_out, never assertion failures. Investigate each flow’s trace/server output; no Commercial v1 claim. |
| PWB-05 pilot assertions | 5 | UNKNOWN | Authentication, finance and NDA pilot assertions have unresolved route/policy/fixture evidence. Product and Quality must decide each case before expiry. |

Every record has a hard 2026-08-31 expiry, CLM One Quality owner, exact
identity/signature safeguard, remediation reference and exit criterion. The
comparator rejects missing, changed, expired, unmatched or wildcard records and
does not allow a failure to become a timeout, crash, skip or removed test.
