# AGENTS.md

## Cursor Cloud specific instructions

CLM One is a single Django 5.2 app (project `config`, main domain app `contracts`, Tailwind theme app `theme`). Dev runs on SQLite with all third-party integrations (Redis, Stripe, Gemini AI, S3, OIDC/SAML SSO, Salesforce, NetSuite, e-sign) feature-flagged off, so no external services are needed to run or test it.

### Environment
- Python 3.12 virtualenv lives at `.venv/`. Always invoke it explicitly (e.g. `.venv/bin/python manage.py ...`); the repo's `Makefile` and helper scripts assume `.venv`.
- The repo's `scripts/bootstrap_python312.sh` uses `uv`, but `uv` is not installed here. The environment is set up with a plain `python3 -m venv .venv` + `pip install -r requirements.txt` (which pulls `requirements/dev.txt` → `requirements/runtime.txt`). The update script handles this refresh automatically.
- `.env` (gitignored) is required and already created from `.env.example` with a dev `DJANGO_SECRET_KEY`. Settings auto-load `.env` via `config/settings_base.py`. Keep `DATABASE_URL` empty so dev uses SQLite; a dev safety guard refuses to start against a non-local `DATABASE_URL`.

### Run
- Dev server: `bash scripts/dev_server.sh` (foreground, port 8060, forces `DJANGO_SETTINGS_MODULE=config.settings_development` and empty `DATABASE_URL`). App at `http://127.0.0.1:8060/`, health at `/_health/`, auth at `/login/` and `/register/`.
- Registering at `/register/` auto-provisions an organization and logs you in (lands on `/dashboard/`).
- After changing models, run `.venv/bin/python manage.py migrate` manually (migrations are intentionally not in the update script). The dev `db.sqlite3` persists across sessions.

### Lint / test / build
- Tests: `make test` (full suite, forces `config.settings_test` = in-memory SQLite). Subset: `make test-fast APP=tests.<module>`. Django checks: `make check`.
- Known pre-existing test drift (NOT caused by environment setup): the suite currently has failures/errors from an in-progress Contract status/`lifecycle_stage` refactor (e.g. `'ContractForm' has no field named 'status'`, status/stage combination validation, `Document.Status`/lifecycle choices set mismatches). Additionally 3 test modules (`tests/test_canonical_url_builder.py`, `tests/test_5i_document_durability.py`, `tests/conftest.py`) import `pytest`, which is not a declared dependency and is skipped by the Django test runner. Do not treat these as regressions from setup.
- Static assets: compiled Tailwind CSS is committed under `theme/static/`, so no Node build is needed to run the app. Only rebuild styles when editing them: `cd theme/static_src && npm install && npm run dev`.
