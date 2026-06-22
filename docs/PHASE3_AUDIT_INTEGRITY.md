# Audit Integrity — Architecture & Operations (Phase 3)

## Canonical architecture

- **Model:** `contracts.models.AuditLog` (single audit model — there is no second
  audit system).
- **Write path:** `contracts.middleware.log_action()` → `contracts.services.audit.append_audit()`.
  The domain helpers (`workflow_audit.py`, `signature_audit.py`) and the auth
  signal receivers (`contracts/signals.py`) all funnel through `log_action`.
- **Tenant boundary:** `AuditLog.organization` (FK, `PROTECT`). `NULL` = a
  system/global event. Reads are scoped to the caller's organization.
- **Chain boundary:** **one hash chain per organization** (plus a separate chain
  for `organization IS NULL`). Per-tenant chains keep verification and export
  isolated.
- **Actor representation:** `actor_type` ∈ {human, service, system, scheduled_job,
  webhook, migration} + `user` FK + optional display snapshot in `changes`.
- **Event taxonomy:** stable `event_type` keys (e.g. `auth.login_succeeded`,
  `approval.delegated`, `document.deleted`, `retention.contract_archived`,
  `job.failed`). UI labels are display translations of these keys.
- **Immutable fields:** the entire row once written (see Immutability).

## Hash chain

Each entry stores `seq` (per-org monotonic order), `prev_hash`, and `entry_hash`.
`entry_hash = SHA-256(canonical_json(v, prev_hash, org, seq, event_type, action,
actor_type, actor_id, model, object_id, outcome, request_id, job_run_id,
changes))`. Serialization is key-sorted and locale-independent, so it does not
depend on dict insertion order. The volatile display `timestamp` is intentionally
NOT hashed — `seq` is the canonical ordering value. Genesis: the first entry of a
chain has `prev_hash == ''` and `seq == 1`. Hashes are computed **before** insert
(single INSERT, no post-hoc update), so a row is immutable from creation.

Legacy rows written before Phase 3 have `seq IS NULL` and `hash_version = 1`; they
are preserved but excluded from chain verification (the chain begins at the
Phase 3 cutover). Historical hashes are not regenerated.

## Immutability guarantee

**Tamper-evident and application-append-only.**

- Application code cannot modify or delete audit rows: `AuditLog.save()` rejects
  updates, `AuditLog.delete()` and the manager's `update()`/`delete()` raise
  `AuditWriteError`, and the Django admin is registered read-only.
- On PostgreSQL, a database trigger (`migration 0053`) rejects `UPDATE`/`DELETE`
  on `contracts_auditlog` — defense-in-depth below the application.
- `organization` uses `on_delete=PROTECT` so audit history is never cascade-
  deleted; organizations are soft-deactivated in product, not hard-deleted.

This is **not** a claim of immutability against a database superuser, who can
disable the trigger. It is not externally notarized. A privileged repair path
must explicitly disable the trigger / pass `_allow_audit_update`/`_allow_audit_delete`
and should itself be recorded.

## Verifying integrity

```bash
python manage.py verify_audit_chain                      # all org chains
python manage.py verify_audit_chain --organization <slug>
python manage.py verify_audit_chain --since 2026-06-01 --until 2026-06-22
python manage.py verify_audit_chain --json
```

Read-only. Exits non-zero (raises `CommandError`) if any chain fails. Reports the
first broken entry's `seq` / `event_type` / reason only (never sensitive
`changes` content). Reasons: `valid`, `empty`, `missing_predecessor`,
`broken_link`, `hash_mismatch`, `malformed`.

Operators also see a per-organization chain-verification badge on the Audit Log
page (`/contracts/audit-log/`), which is tenant-scoped and read-only.

## Concurrency & sequence allocation

Appending an entry must atomically (1) read the chain tail, (2) pick the next
`seq`, (3) compute `prev_hash`, (4) insert. Serialization:

- **PostgreSQL:** a transaction-scoped advisory lock — `pg_advisory_xact_lock(classid, key)`
  where `key` = organization id, or a fixed sentinel (`0`) for the system chain.
  This is a **stable lock target** that works even at genesis (no row exists to
  lock yet) and for the NULL system chain. The lock releases at transaction end.
- **SQLite (tests):** writes are already serialized; the lock is a no-op.
- **Backstop (all backends):** partial unique constraints on `(organization, seq)`
  (tenant chains) and `(seq) WHERE organization IS NULL` (system chain) — a plain
  `(organization, seq)` unique would NOT constrain the system chain because
  PostgreSQL treats NULLs as distinct. `append_audit` retries on `IntegrityError`
  and recomputes from the new tail.

Proven on PostgreSQL by `tests/test_audit_postgres.py` (concurrent appends from
genesis on both tenant and system chains stay contiguous and verify clean) and
the `audit-postgres` CI job.

## Tenant attribution invariant

Every audit event about an organization-owned object **must** carry an
organization; only explicitly-platform targets may use the NULL system chain.
`append_audit` enforces this: for a contracts-app model with an `organization`
field it derives the org from the target row when the caller omits it, and
**raises `AuditMisclassificationError`** (re-raised by `log_action`, never
swallowed) if it cannot — so a tenant event can never silently fall onto the
system chain. Platform targets (`User`, `ScheduledJobRun`, `ESignEvent`,
`RetentionExecution`, `SignaturePacket`) are exempt and carry org explicitly when
tenant-scoped.

## Operating the append-only trigger (escape hatch)

The PostgreSQL trigger (`migration 0053`) blocks all UPDATE/DELETE. Legitimate
operations:

- **Schema migrations that alter audit storage:** add new *columns*/indexes
  normally — `ALTER TABLE ... ADD COLUMN` is not UPDATE/DELETE and is not
  blocked. A migration that must rewrite rows has to drop the trigger first
  (`migration 0053` reverse) and re-create it after.
- **Emergency repair / GDPR erasure of an audit row:** only a database
  superuser, in a maintenance window:
  1. `ALTER TABLE contracts_auditlog DISABLE TRIGGER USER;`
  2. perform the minimal change;
  3. `ALTER TABLE contracts_auditlog ENABLE TRIGGER USER;`
  4. `python manage.py verify_audit_chain` and record the result;
  5. record who/why/when in an out-of-band operations log (the change itself is,
     by design, not self-auditable while the trigger is off).
- **Database restore:** restoring from a logical dump re-runs `migrate`, which
  re-installs the trigger; verify it exists (`select tgname from pg_trigger`)
  and run `verify_audit_chain` after any restore.

## Retention vs. legal retention

Ordinary record deletion / tenant cleanup does NOT remove audit evidence
(append-only + `PROTECT`). Audit retention is therefore distinct from product
data retention; deleting a contract or deactivating a member leaves the audit
trail intact.
