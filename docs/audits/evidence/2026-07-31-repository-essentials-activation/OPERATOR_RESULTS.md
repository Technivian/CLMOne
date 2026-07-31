# Repository Essentials bounded activation results

**Result:** PASS

**Implementation SHA:** `88350bbc36f7f1efdc992741be0bfa3bfb73b53e`

**Named environment:** `repo-essentials-synthetic-2026-07-31`

**Workspace allowlist:** `synthetic-repository-activation` only

**Data:** disposable synthetic records only

**Final state:** CSV, repository enforcement, repository abort, search
enforcement, search abort, and external collaboration all off

## Scope

This was a process-scoped local non-production observation of the already
implemented CSV import, repository boundary, and search/facet boundary. It did
not use PayrollMinds or client data, activate a deployed environment, change a
permission, connect an identity provider, upload a document, call an external
service, or enable external collaboration.

The observation temporarily enabled only:

- `REPOSITORY_CSV_IMPORT_ENABLED=true`;
- repository enforcement for the exact named environment and workspace;
- search/facet enforcement for the same environment and workspace; and
- no abort switch during the observation.

Committed defaults were unchanged.

## Acceptance results

| Control | Result |
|---|---|
| Downloadable CSV template and import page | PASS |
| Dry-run valid and zero database/audit/document mutation | PASS |
| Preview token rejected in another workspace | PASS |
| Two synthetic contracts created with canonical mapping | PASS |
| No document created or exposed | PASS |
| Provenance correlation ID exact on every created contract | PASS |
| Append-only batch/row/completion audit chain present | PASS |
| Repeat submission reported deterministic create-only duplicates and produced no commit token | PASS |
| Compensating rollback archived both records without deletion | PASS |
| Rollback append-only audit chain present | PASS |
| Repository rows and metadata hid direct and inherited Ethical-Wall records | PASS |
| Repository hid the cross-workspace record | PASS |
| Denied detail returned generic 404; eligible detail remained available | PASS |
| Search results and status facets used the same eligible set | PASS |
| Search hid direct, inherited, and cross-workspace records | PASS |

## Abort and restoration

The abort probe disabled normal repository/search enforcement, enabled both
abort switches for the same allowlisted workspace, and proved:

- repository state resolved to `abort_fail_closed`;
- repository API returned HTTP 200 with zero rows and total zero; and
- search state resolved to `abort_fail_closed` with zero results.

The activation processes then ended. A clean process with no overrides proved:

- CSV import was off and its route returned 404;
- repository enforcement and abort were off;
- search enforcement and abort were off;
- both policy evaluators returned the inactive legacy state; and
- external collaboration remained off.

The disposable SQLite database was isolated from the developer database and
contained only the synthetic evidence corpus. This observation authorizes no
deployed, production, real-data, document, identity, or external-access use.
