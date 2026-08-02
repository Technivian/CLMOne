# PayrollMinds AI governance validation

**Status:** Draft implementation evidence, 2026-08-02. This is not approval,
release, deployment, provider, or customer-data evidence.

## Exact local validation

Run from the isolated AI-governance branch:

```text
/Users/haroonwahed/Documents/Projects/CLMOne/.venv/bin/python manage.py test \
  tests.test_payrollminds_ai_governance_gate \
  tests.test_upload_ocr_pipeline \
  tests.test_controlled_pilot_scope \
  tests.test_legal_front_door.DocumentExtractPreviewApiTests -v 1
```

Result: **PASS — 26 tests in 1.165s; exit status 0.** This covers a configured
provider denied in controlled-pilot mode, direct resolver denial, workspace
kill switch, manual metadata preview, no unattended OCR provider call, and
existing pilot-path/preview behavior.

```text
/Users/haroonwahed/Documents/Projects/CLMOne/.venv/bin/python manage.py test \
  tests.test_ai_extraction -v 1
```

Result: **PASS — 16 tests in 0.044s; exit status 0.**

```text
/Users/haroonwahed/Documents/Projects/CLMOne/.venv/bin/python manage.py \
  makemigrations --check --dry-run
```

Result: **PASS — `No changes detected`; no migration is introduced.**

```text
/Users/haroonwahed/Documents/Projects/CLMOne/.venv/bin/python manage.py check
git diff --check
```

Result: **PASS — `System check identified no issues (0 silenced)`; no
whitespace errors.**

The 26-test command emitted an audit-append error from an existing mocked OCR
pipeline test whose mocked organization ID is a list; the test process still
completed successfully. This AI-governance change neither adds nor weakens an
audit write path; no provider suggestion is created while the pilot boundary
is enabled.

## Security impact

- Controlled-pilot provider routes return `403` with a manual-entry recovery
  message even if `GEMINI_AI_ENABLED=true` and a provider key is present.
- The same resolver check protects direct view invocation without relying on
  client-side hiding or middleware.
- OCR jobs never send extracted contract text to an external provider.
- A diagnostic no longer writes a document excerpt to application logs.
- No persistent model, schema, data migration, credential, provider call, or
  production setting activation is included.

## Remaining accepted risks and blockers

No risk is accepted by this record. The pilot remains **NO-GO** under the
launch-readiness report. Enabling AI is blocked until there is accepted
authority and evidence for canonical suggestion persistence, object-level
context authorization, data classification/redaction, provider
retention/training/deletion/residency/DPA terms, audit coverage, and an
operator release record. Existing repository-wide full-suite drift is not
represented as green by this focused evidence.

## Rollback

There is no migration or data rollback. Keep
`CONTROLLED_PILOT_ENABLED=true` and `GEMINI_AI_ENABLED=false`; restart through
the normal configuration procedure. This denies external AI while preserving
documents, OCR reviews, Contract Records, Document Versions, and audit
evidence. Manual entry remains available.
