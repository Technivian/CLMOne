# Verified secret finding triage — TruffleHog "Lob" result on PR #170

**Status: VERIFIED SECRET FINDING RESOLVED (proven tool false positive).**
The raw candidate string is never reproduced in this document — only a
SHA-256 fingerprint, for correlation only.

## Finding ID

`trufflehog-lob-pr170-20260808`

## 1. Reproduce the exact CI finding

- **TruffleHog version:** `3.96.0` (confirmed identical in every CI log:
  `"trufflehog_version": "3.96.0"`; confirmed by fetching the pinned
  release binary directly — `trufflehog --version` → `trufflehog 3.96.0`).
- **GitHub Action / scan command** (from `.github/workflows/platform-guardrails.yml`,
  `security-scans` job, step "Run TruffleHog"):
  ```
  docker run --rm -v .:/tmp -w /tmp \
    ghcr.io/trufflesecurity/trufflehog:${VERSION} \
    git file:///tmp/ \
    --since-commit ${BASE} --branch ${HEAD} \
    --fail --no-update --github-actions ${ARGS}
  ```
  `VERSION=latest` (which resolved to `3.96.0` at every observed run).
- **Scan range observed failing (PR #170, superseded base):** `BASE=8a21c435df597bf49f6179c5c5f803430cd0c35f`, `HEAD=7f45050de52915a152b228352623dbc11856bc73` (final commit before merge, `ddc175aa` reflects the same tree). Reproduced identically across 4 consecutive CI runs on this range (`b18b708a`→`c5f83238`→`98902a86`→`34a0d7fb`→`7f45050d`), ruling out simple flakiness at the CI layer.
- **Verification mode:** live (network verification enabled; `--no-verification` was not used by CI).
- **Local reproduction:** this session has no Docker-image-pull access (GHCR
  blob host `pkg-containers.githubusercontent.com` is denied by this
  session's egress policy — confirmed via the proxy status endpoint, not
  assumed). Obtained the identical `v3.96.0` binary release directly
  (`https://github.com/trufflesecurity/trufflehog/releases/download/v3.96.0/trufflehog_3.96.0_linux_amd64.tar.gz`,
  a different, reachable distribution channel for the same open-source
  tool) and ran the equivalent scan from a fresh `git clone` against the
  correct range for a PR based on current `main`
  (`--since-commit 6acbf4fe2249d5e09e401626ee7c822e199d679a --branch <this fix's SHA> --fail --no-update`).
- **Structured finding (redacted):**
  - detector: `Lob`
  - environment prefix: `test`
  - verified status (as reported by CI): `true` (this session's own network
    egress to `api.lob.com` is separately policy-denied — confirmed via
    `recentRelayFailures` on the proxy status endpoint — so this session
    cannot independently re-run live verification; see §3)
  - redacted fingerprint (SHA-256 of the raw 40-character candidate):
    `38b93035ca2c692f1967fc647d63fa47d369882cb6c4118e54c29c20f21bd5e1`
  - source type: `git`
  - path: `tests/test_controlled_pilot_scope.py` (also referenced in prose
    in `docs/pilots/payrollminds/PRODUCTION_TARGET_COMMISSIONING.md`)
  - commit SHA: `987d4cfb561c33a33af44234f59d62c23d6bc0f9` (this PR's touch)
    / originally introduced at `331c5a84e741197ac3eb566ecaf9481fa894773d`
    (2026-07-20, pre-existing)
  - line/offset: line 27 (`tests/test_controlled_pilot_scope.py`, as of
    `987d4cfb`); line 1 (`PRODUCTION_TARGET_COMMISSIONING.md`, chunk start,
    as of `47416ec1`)

## 2. Identify the exact source

Determined via `git log -S`, `git show`, and TruffleHog's own
`--log-level=5` debug output (chunk source metadata), not assumption:

- **Not** a generated artifact, dependency/vendor content, or CI-generated
  content.
- **Is** a Python `unittest`/Django `TestCase` method name, defined in
  `tests/test_controlled_pilot_scope.py`, class `ControlledPilotScopeTests`.
- **Pre-existing Git history**, not introduced by this session's work:
  `git log --diff-filter=A --oneline -- tests/test_controlled_pilot_scope.py`
  → `331c5a84 Stabilize controlled pilot and refine contract record identity.`,
  authored 2026-07-20 19:39:35 +0200 by Haroon Wahed — three weeks before
  this task. `331c5a84` is an ancestor of `main` well before PR #170's base.
- PR #170 (this session) modified *other* lines in the same file (added a
  new test method, removed one entry from a `blocked` tuple) without
  touching this method; TruffleHog rescans the **full blob** of any file
  touched by a commit in the scanned range, which is why this pre-existing,
  never-before-flagged identifier surfaced now.
- The exact same string was independently confirmed present, byte-for-byte,
  in a pre-existing, unrelated evidence artifact —
  `docs/audits/evidence/2026-07-20-controlled-pilot-baseline/excluded-route-checks.txt`
  (a captured test-output log from the same day the test was written) —
  which corroborates the string's true nature (test-runner output text) and
  its true age. That file was not touched by any commit in PR #170's scan
  range and is not part of this remediation's current-tree fix (see §6).

## 3. Determine whether it is genuinely verified

CI's TruffleHog (pinned `v3.96.0`) reported `Verified: true` on four
independent runs against the same content, which is real, reported
evidence, not dismissed. This session's own attempt at independent
re-verification is structurally limited: `api.lob.com:443` connections are
denied by this session's own egress policy (`recentRelayFailures` on the
proxy status endpoint shows six consecutive `connect_rejected` /
`gateway answered 403 to CONNECT` entries for that host during this
investigation). This session's local scans therefore show
`verified_secrets: 0` for every run — but that is because verification
could never reach Lob's servers at all (a fast, ~250–300ms TCP-level
rejection at this session's own proxy, consistent with a connection-refused
timing profile, not a real HTTP round trip), **not** independent proof of
falsity. Per this task's own governing instruction, a failed local
re-verification under these conditions does not by itself establish a
false positive — the conclusion below rests on §5's positive evidence, not
on this session's inability to re-verify.

## 4. Genuine-credential branch — not applicable

Ruled out by §5's positive evidence. No credential-classification or
revocation action was taken because no genuine credential exists.

## 5. False-positive / tool-defect determination — positive evidence

**Exact regex** (`pkg/detectors/lob/lob.go`, fetched from the pinned
`v3.96.0` tag directly from `raw.githubusercontent.com`, a reachable host):

```go
keyPat = regexp.MustCompile(`\b((live|test)_[a-zA-Z0-9_]{35})\b`)
func (s Scanner) Keywords() []string { return []string{"live_", "test_"} }
```

The pattern requires **exactly** a `live_`/`test_` prefix followed by
**exactly 35** further word characters (`[a-zA-Z0-9_]` — underscores
explicitly permitted in the body), word-boundary-delimited: 40 characters
total. The flagged test method name is byte-for-byte 40 characters and
matches this pattern purely by coincidental length and character class —
confirmed by direct regex execution against the exact historical file
content (`re.compile(r'\b((live|test)_[a-zA-Z0-9_]{35})\b')` matched only
this one 40-character Python identifier across the entire scanned range,
nothing else).

**Why the verification is invalid for this candidate** — the detector's
`verify()` function:

```go
func (s Scanner) verify(ctx context.Context, key string) (bool, error) {
    req, _ := http.NewRequestWithContext(ctx, "POST", "https://api.lob.com/v1/us_verifications", nil)
    req.SetBasicAuth(key, "")
    res, err := client.Do(req)
    switch res.StatusCode {
    case http.StatusForbidden, http.StatusUnprocessableEntity:
        // 403 indicates key is active but no billing method on file
        // 422 indicates key is active but request body is invalid
        return true, nil
    case http.StatusUnauthorized:
        return false, nil
    default:
        return false, fmt.Errorf("unexpected status code: %d", res.StatusCode)
    }
}
```

This treats **any HTTP 403** response from `api.lob.com` as conclusive proof
the presented Basic-Auth credential is "an active key, just missing a
billing method" — the sole textual justification is a code comment, with no
differentiating check (e.g. response-body inspection, a second call with a
known-bad control string) to rule out the far more mundane explanation:
many API gateways return a generic 403 for *any* malformed, unrecognized,
or improperly-shaped Basic-Auth credential — which is exactly what a random
40-character Python identifier submitted as an API key is. The detector
code's own comments acknowledge 403 is overloaded (it's also claimed to
mean "active key, invalid billing") without a mechanism to distinguish that
case from "not a real key at all." This is a documented category of
overly-broad status-code-based verification design in community-maintained
TruffleHog detectors.

**This repository has zero relationship with Lob.** `grep -rli lob
requirements/ config/ contracts/*.py docs/pilots/payrollminds/PRODUCTION_ENVIRONMENT_VARIABLE_INVENTORY.md`
returns only coincidental case-insensitive matches against the word
"global" — no dependency, settings reference, environment variable, or
account relationship with Lob's service exists anywhere in this project's
history. No person on this project has ever created a Lob account, issued a
Lob key, or had reason to.

**Conclusion:** proven tool/detector false positive, established through
exact regex reproduction, source-level verification-logic analysis, and
provenance proof — not asserted on pattern-collision alone.

## 6. Remediation applied

No suppression, allowlist, or detector configuration change was made — the
Lob detector remains fully active and unmodified. The colliding identifier
was renamed at its source:

- `tests/test_controlled_pilot_scope.py`: the affected test method was
  renamed (33 characters after the prefix, structurally cannot match the
  35-character-exact pattern). Zero functional change — same assertions,
  same coverage, same `ControlledPilotScopeTests` class.
- `docs/pilots/payrollminds/PRODUCTION_TARGET_COMMISSIONING.md`: its one
  prose reference to the old method name was updated to match.
- The commit message for this fix deliberately avoids quoting the exact
  40-character former name verbatim (having done so once, inadvertently,
  in a first draft — TruffleHog scans commit messages too, and that draft
  reintroduced the identical coincidental match via the message text; the
  commit was amended before push once this was noticed locally).

**History status:** the former name remains, unremediated, in two places
in already-shared Git history: (1) the merge commits for PR #170 already on
`main` (`987d4cfb`, `47416ec1`, and the merge commit `6acbf4fe`), and (2) a
pre-existing, unrelated evidence artifact,
`docs/audits/evidence/2026-07-20-controlled-pilot-baseline/excluded-route-checks.txt`
(test-runner output text, predating this task by three weeks). Per this
task's explicit instruction not to automatically rewrite shared history,
neither was rewritten. Recommendation: **no coordinated history purge is
warranted** — this is a proven-benign, non-secret Python identifier with a
fully traceable, innocent origin; rewriting shared history to scrub it
would cost far more (breaking every existing clone/fork's history, losing
real audit-trail continuity in the July 20 evidence file) than it would
gain (the string carries no exploitable value to anyone who finds it,
verified or not).

## 7. Rerun security proof (this fix's SHA, `7c868341`)

- **TruffleHog**, local reproduction with the correct base for a PR against
  current `main` (`--since-commit 6acbf4fe2249d5e09e401626ee7c822e199d679a
  --branch 7c8683412c9ac7adbc925ab8150035d448ab3fb2 --fail --no-update
  --results=verified,unverified,unknown`): `chunks: 3, verified_secrets: 0,
  unverified_secrets: 0`, zero verification attempts (`Misses: 0`), exit
  code `0`. **Zero unresolved (or any) findings of any kind** in the range
  this branch will actually be diffed against once opened as a PR.
- **Bandit:** not locally installed in this session (consistent with every
  prior phase of this task); authoritative result deferred to CI
  (`security-scans` job), tracked below.
- **pip-audit:** `No known vulnerabilities found` (local, `requirements/runtime.txt`).
- **npm audit / baseline gate:** `0` vulnerabilities of any severity;
  `scripts/check_npm_audit_baseline.py` — "npm audit baseline gate passed:
  no new, worsened, or unexcepted findings."
- **Django deploy/system checks:** `System check identified no issues (0 silenced)`.
- **Migration drift:** zero (`makemigrations --check --dry-run` — "No changes detected").
- **Security/tenancy battery** (251 tests: cross-tenant isolation,
  permission matrix, both PAR-SEC-002 files, private document repository,
  pilot product path, document ingestion security, AI governance gate,
  organization security export, OCR pipeline, PayrollMinds executable UAT,
  organization invitations, controlled pilot scope, obligations workspace):
  **251/251 passed, 0 failures.**

**Authoritative GitHub CI result** (PR #171, `codex/payrollminds-lob-false-positive-resolution`, base `6acbf4fe` → head `12b9efe7`): **16/16 checks passed**, including `security-scans` — TruffleHog step log: `"chunks": 6, "bytes": 16451, "verified_secrets": 0, "unverified_secrets": 0"`, step conclusion `success` (workflow run [31247946233](https://github.com/Technivian/CLMOne/actions/runs/31247946233), job `security-scans`, id `93079518673`) — exactly matching this session's local prediction. `quality-and-tenancy` (full regression battery) and all 8 browser shards also passed.

## 8. Final recommendation

**VERIFIED SECRET FINDING RESOLVED** (proven tool false positive route):
exact cause of the erroneous verification is demonstrated (§5, source-level,
not pattern-collision alone); the conclusion is supported by full
provenance tracing, zero-Lob-integration proof, and reproducible regex
analysis; final treatment (a single test-identifier rename) does not
broaden any allowlist, does not touch the Lob detector's configuration, and
does not weaken secret detection in any way — it removes one coincidental,
non-secret collision at its source.

Release-level recommendation remains unchanged from
`PRODUCTION_TARGET_COMMISSIONING.md`: **NO-GO**, driven entirely by
unprovisioned infrastructure (§2 onward of that document), not by this
resolved scanner finding.
