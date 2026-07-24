# Solo-maintainer standing authorization

**Status:** Active while the repository has one active maintainer

**Authority:** Repository-owner standing authorization

**Purpose:** Preserve a controlled, auditable merge path for low-risk changes
when an independent GitHub Engineering or Security reviewer is unavailable.

## Eligible changes

A pull request may merge under this authorization only when every condition is
met:

- its scope is limited to documentation, tests, or a narrowly scoped dependency
  update;
- it introduces no migration;
- it changes no runtime authority, permission, role, feature flag,
  canonical-read authority, or production activation;
- it weakens, bypasses, or suppresses no CI or security control;
- all required CI checks pass, including security scans for a dependency
  update;
- its exact scope and rollback method are documented; and
- the repository owner explicitly confirms that this standing authorization
  applies to the exact PR and reviewed head.

GitHub-generated PR, check, merge, and comment metadata are the authoritative
audit evidence. Do not enter a manual vote timestamp.

## Stronger controls

This authorization never applies to:

- canonical-read or canonical-write authority;
- production activation;
- privilege, role, permission, or ADMIN authority changes;
- automatic repair or automatic decision authority;
- destructive migrations;
- legacy retirement;
- security-control suppression; or
- material tenant-isolation changes.

Those changes require their separate explicit authorization and, when
available, independent review. This rule does not turn a proxy, inferred,
generated, or copied approval into genuine evidence.

## Operating procedure

Before merging under this authorization, verify the current PR head and scope,
green required CI, dependency-scan result where applicable, rollback method,
and the repository owner's explicit confirmation. Record direct GitHub links
to the PR, checks, owner confirmation when it exists in GitHub, and merge.
Do not have an agent author a confirmation or review on the owner's behalf.

## Recorded application: PR #83

PR [#83](https://github.com/Technivian/CLMOne/pull/83) qualified as a narrowly
scoped dependency update: the reviewed head
[`d6e7cb2195bda54a3777d1f6f07d6a2ecc9d82f4`](https://github.com/Technivian/CLMOne/commit/d6e7cb2195bda54a3777d1f6f07d6a2ecc9d82f4)
changed only `requirements/runtime.txt`, updating `pypdf` from `6.13.3` to
`6.14.2`. Required CI was green, `security-scans` reported no known
vulnerabilities, and the tenant audit passed on a clean migrated disposable
database. It merged by merge commit
[`decd7a996dc5d1749be8fa226441e8488180484c`](https://github.com/Technivian/CLMOne/commit/decd7a996dc5d1749be8fa226441e8488180484c).

This is an application of the standing authorization, not Engineering or
Security review evidence and not an authorization for any stronger-control
change.

## Rollback

Revert this documentation and CODEOWNERS correction in a follow-up docs-only
PR if solo-maintainer mode ends or the repository owner withdraws the standing
authorization. Preserve historical GitHub evidence.
