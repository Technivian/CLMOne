"""Canonical audit append path — per-organization tamper-evident hash chain.

There is ONE audit model (``contracts.models.AuditLog``) and ONE write path
(``append_audit`` here, reached via ``contracts.middleware.log_action`` and the
domain helpers in ``workflow_audit`` / ``signature_audit``). Do not add a second
audit system.

Chain design
------------
* Boundary: **one chain per organization** (plus a separate chain for
  ``organization IS NULL`` system/global events). A per-tenant chain keeps
  verification and export tenant-isolated — a single global cross-tenant chain
  would couple tenants' orderings and leak activity volume across the boundary.
* Ordering value: ``seq`` (per-org monotonic integer). The display ``timestamp``
  is intentionally NOT hashed (it is informational and could vary); ``seq`` is
  the canonical order.
* Genesis: the first entry in a chain has ``prev_hash == ''`` and ``seq == 1``.
* Hash input: a canonical, key-sorted JSON document (version-tagged) covering
  the immutable evidence — previous hash, org, seq, event type, action, actor,
  target, outcome, correlation ids and the structured ``changes`` metadata.
  Serialization is order-independent (``sort_keys``) and locale-independent.

Guarantee: **tamper-evident and application-append-only.** Application code
cannot modify or delete rows (model guards + read-only admin), and on
PostgreSQL a trigger blocks UPDATE/DELETE at the database level. This does not
claim protection against a database superuser who disables the trigger — see the
runbook. It is not cryptographically notarized off-box.
"""
from __future__ import annotations

import hashlib
import json
import logging

from django.apps import apps
from django.db import IntegrityError, connection, transaction

from contracts.models import AuditLog

logger = logging.getLogger(__name__)

HASH_VERSION = 2
GENESIS_PREV_HASH = ''  # prev_hash of the first entry in each org chain
_MAX_SEQ_RETRIES = 6
# Advisory-lock namespace (arbitrary stable int) used to serialize appends per
# chain on PostgreSQL. Paired with the org id (0 = system chain) as the 2nd key.
_AUDIT_LOCK_CLASSID = 0x41554454  # "AUDT"
_SYSTEM_CHAIN_LOCK_KEY = 0        # org ids are >= 1, so 0 is a safe sentinel

# Models that are NOT contracts-app org-owned models but legitimately appear as
# audit targets on the system chain (no tenant), or carry org explicitly.
_PLATFORM_TARGET_MODELS = frozenset({
    'User',                 # auth events; org passed explicitly when known
    'ScheduledJobRun',      # job.failed carries org when tenant-scoped
    'ESignEvent',           # webhook reconcile carries org explicitly
    'RetentionExecution',   # synthetic; carries org explicitly
    'SignaturePacket',      # synthetic; carries org explicitly
})


class AuditMisclassificationError(Exception):
    """An organization-owned event was about to be written with no organization.

    Raised (not swallowed) so a tenant event can never silently fall into the
    system chain — the caller must supply or make the organization resolvable.
    """


def _is_org_owned_model(model_name):
    """True if `model_name` is a contracts-app model carrying an organization FK."""
    if not model_name or model_name in _PLATFORM_TARGET_MODELS:
        return False
    try:
        model = apps.get_model('contracts', model_name)
    except Exception:
        return False
    return any(getattr(f, 'name', None) == 'organization' for f in model._meta.fields)


def _resolve_org_id_from_target(model_name, object_id):
    """Best-effort resolve organization_id from an org-owned target row."""
    if object_id is None:
        return None
    try:
        model = apps.get_model('contracts', model_name)
    except Exception:
        return None
    return (
        model.objects.filter(pk=object_id)
        .values_list('organization_id', flat=True)
        .first()
    )


def canonical_material(
    *,
    prev_hash,
    organization_id,
    seq,
    event_type,
    action,
    actor_type,
    actor_id,
    model_name,
    object_id,
    outcome,
    request_id,
    job_run_id,
    changes,
) -> str:
    """Deterministic, order-independent serialization of the hashed evidence."""
    payload = {
        'v': HASH_VERSION,
        'prev': prev_hash or '',
        'org': organization_id,
        'seq': seq,
        'event_type': event_type or '',
        'action': action or '',
        'actor_type': actor_type or '',
        'actor_id': actor_id,
        'model': model_name or '',
        'object_id': object_id,
        'outcome': outcome or '',
        'request_id': request_id or '',
        'job_run_id': str(job_run_id) if job_run_id else '',
        'changes': changes if changes is not None else None,
    }
    return json.dumps(payload, sort_keys=True, separators=(',', ':'), default=str)


def compute_entry_hash(**kwargs) -> str:
    return hashlib.sha256(canonical_material(**kwargs).encode('utf-8')).hexdigest()


def _lock_chain(organization_id):
    """Serialize appends to one chain.

    On PostgreSQL, take a transaction-scoped advisory lock keyed by the chain
    (org id, or a sentinel for the system chain). This is a STABLE lock target
    that works even at genesis (no row to lock yet) and for the NULL system
    chain — locking the latest AuditLog row would not. The lock is released at
    transaction end. On other backends (SQLite in tests) writes are already
    serialized, so this is a no-op; the unique constraints + retry remain the
    backstop.
    """
    if connection.vendor != 'postgresql':
        return
    key2 = organization_id if organization_id is not None else _SYSTEM_CHAIN_LOCK_KEY
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_xact_lock(%s, %s)', [_AUDIT_LOCK_CLASSID, int(key2)])


def _chain_tail(organization_id):
    """Most recent chained entry for a chain (called while holding the lock)."""
    return (
        AuditLog.objects
        .filter(organization_id=organization_id, seq__isnull=False)
        .order_by('-seq')
        .first()
    )


def append_audit(
    *,
    action,
    model_name,
    organization=None,
    organization_id=None,
    user=None,
    object_id=None,
    object_repr='',
    changes=None,
    event_type=None,
    actor_type=None,
    outcome=AuditLog.Outcome.SUCCESS,
    request_id='',
    job_run_id=None,
    ip_address=None,
    user_agent='',
) -> AuditLog:
    """Append one entry to the appropriate per-org chain and return it.

    Computes ``seq``, ``prev_hash`` and ``entry_hash`` BEFORE insert (single
    INSERT, no post-hoc update) so the row is immutable from creation and
    compatible with the database-level append-only trigger.
    """
    org_id = organization.id if organization is not None else organization_id
    actor_id = getattr(user, 'id', None)

    # Tenant-attribution guard: an organization-owned target must never be
    # written to the system (NULL) chain. Resolve the org from the target row if
    # the caller didn't provide it; reject if it cannot be resolved.
    if org_id is None and _is_org_owned_model(model_name):
        org_id = _resolve_org_id_from_target(model_name, object_id)
        if org_id is None:
            raise AuditMisclassificationError(
                f'Org-owned audit target {model_name}#{object_id} has no '
                f'organization; refusing to file it on the system chain.'
            )

    if not event_type:
        event_type = (changes or {}).get('event') if isinstance(changes, dict) else None
        event_type = event_type or f'{model_name}.{action}'.lower()
    if not actor_type:
        actor_type = AuditLog.ActorType.HUMAN if actor_id else AuditLog.ActorType.SYSTEM

    last_error = None
    for _attempt in range(_MAX_SEQ_RETRIES):
        try:
            with transaction.atomic():
                _lock_chain(org_id)
                tail = _chain_tail(org_id)
                seq = (tail.seq + 1) if tail else 1
                prev_hash = tail.entry_hash if tail else GENESIS_PREV_HASH
                entry_hash = compute_entry_hash(
                    prev_hash=prev_hash, organization_id=org_id, seq=seq,
                    event_type=event_type, action=action, actor_type=actor_type,
                    actor_id=actor_id, model_name=model_name, object_id=object_id,
                    outcome=outcome, request_id=request_id, job_run_id=job_run_id,
                    changes=changes,
                )
                entry = AuditLog(
                    organization_id=org_id, user=user, actor_type=actor_type,
                    action=action, event_type=event_type, outcome=outcome,
                    model_name=model_name, object_id=object_id,
                    object_repr=(object_repr or '')[:300], changes=changes,
                    ip_address=ip_address, user_agent=(user_agent or '')[:500],
                    request_id=(request_id or '')[:64], job_run_id=job_run_id,
                    seq=seq, prev_hash=prev_hash, entry_hash=entry_hash,
                    hash_version=HASH_VERSION,
                )
                entry.save(force_insert=True)
                return entry
        except IntegrityError as exc:
            # Concurrent appender took this seq (unique constraint). Retry.
            last_error = exc
            continue
    raise last_error if last_error else RuntimeError('append_audit failed')


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

VERDICT_VALID = 'valid'
VERDICT_EMPTY = 'empty'
VERDICT_MISSING_PREDECESSOR = 'missing_predecessor'
VERDICT_DUPLICATE_SEQ = 'duplicate_seq'
VERDICT_HASH_MISMATCH = 'hash_mismatch'
VERDICT_BROKEN_LINK = 'broken_link'
VERDICT_MALFORMED = 'malformed'


def verify_chain(organization_id, *, since=None, until=None) -> dict:
    """Verify one organization's chain without modifying data.

    Returns a dict: ``{status, checked, organization_id, first_broken: {...}}``.
    ``first_broken`` (when present) reports seq/event_type/reason only — never
    sensitive ``changes`` content.
    """
    qs = AuditLog.objects.filter(organization_id=organization_id, seq__isnull=False)
    if since is not None:
        qs = qs.filter(timestamp__gte=since)
    if until is not None:
        qs = qs.filter(timestamp__lt=until)
    entries = list(qs.order_by('seq'))

    if not entries:
        return {'status': VERDICT_EMPTY, 'checked': 0, 'organization_id': organization_id}

    expected_prev = GENESIS_PREV_HASH
    expected_seq = entries[0].seq  # range may start mid-chain; link-check relatively
    full_range = since is None and until is None

    for idx, e in enumerate(entries):
        # Duplicate sequence number — explicitly rejected even if a DB unique
        # constraint is somehow absent (defense-in-depth for the verifier).
        if idx > 0 and e.seq == entries[idx - 1].seq:
            return _broken(organization_id, e, VERDICT_DUPLICATE_SEQ, len(entries))
        # Sequence continuity (no missing predecessor within the examined set).
        if idx > 0 and e.seq != entries[idx - 1].seq + 1:
            return _broken(organization_id, e, VERDICT_MISSING_PREDECESSOR, len(entries))
        # Genesis rule only applies when verifying from the true start.
        if idx == 0 and full_range and e.seq != 1:
            return _broken(organization_id, e, VERDICT_MISSING_PREDECESSOR, len(entries))
        # Link check (skip the very first row of a partial range).
        if idx > 0 and e.prev_hash != entries[idx - 1].entry_hash:
            return _broken(organization_id, e, VERDICT_BROKEN_LINK, len(entries))
        if idx == 0 and full_range and e.prev_hash != GENESIS_PREV_HASH:
            return _broken(organization_id, e, VERDICT_BROKEN_LINK, len(entries))
        # Recompute the entry hash from stored protected fields.
        try:
            recomputed = compute_entry_hash(
                prev_hash=e.prev_hash, organization_id=e.organization_id, seq=e.seq,
                event_type=e.event_type, action=e.action, actor_type=e.actor_type,
                actor_id=e.user_id, model_name=e.model_name, object_id=e.object_id,
                outcome=e.outcome, request_id=e.request_id, job_run_id=e.job_run_id,
                changes=e.changes,
            )
        except Exception:
            return _broken(organization_id, e, VERDICT_MALFORMED, len(entries))
        if recomputed != e.entry_hash:
            return _broken(organization_id, e, VERDICT_HASH_MISMATCH, len(entries))

    return {'status': VERDICT_VALID, 'checked': len(entries), 'organization_id': organization_id}


def verify_chain_cached(organization_id, ttl=300) -> dict:
    """Cached chain status for cheap UI badges.

    Keyed by (org, latest seq) so the O(n) verification runs only when a new
    entry appends (or the short TTL lapses); repeated page loads are O(1). Use
    the management command / verify_chain for an authoritative on-demand check.
    """
    from django.core.cache import cache
    latest_seq = (
        AuditLog.objects.filter(organization_id=organization_id, seq__isnull=False)
        .order_by('-seq').values_list('seq', flat=True).first()
    )
    key = f'audit_chain_status:{organization_id}:{latest_seq}'
    cached = cache.get(key)
    if cached is not None:
        return cached
    result = verify_chain(organization_id)
    cache.set(key, result, ttl)
    return result


def _broken(organization_id, entry, reason, checked) -> dict:
    return {
        'status': reason,
        'checked': checked,
        'organization_id': organization_id,
        'first_broken': {
            'seq': entry.seq,
            'event_type': entry.event_type,
            'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
            'reason': reason,
        },
    }


def organization_ids_with_chains():
    # .order_by() clears the model's Meta ordering (-timestamp); otherwise the
    # ordering column leaks into SELECT DISTINCT and defeats de-duplication.
    return list(
        AuditLog.objects.filter(seq__isnull=False)
        .order_by()
        .values_list('organization_id', flat=True)
        .distinct()
    )
