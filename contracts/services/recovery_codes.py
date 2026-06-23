"""Canonical recovery-code consumption service (Phase 5L).

Both entry paths — the MFA challenge view and the profile page — call this
function so that:

- Consumption is atomic: UserProfile.verify_mfa_recovery_code() removes the
  consumed hash and increments session_revocation_counter in one DB save.
  Replay is structurally impossible (hash absent on second call).
- Exactly one tenant-attributed mfa.recovery_code_used audit event is emitted
  per consumption regardless of entry path.
- The session is marked mfa_verified=True when request is supplied.
- A suspicious-use notification is sent to the account owner.
- The recovery code value itself is never written to audit metadata or logs.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def consume_recovery_code(
    profile,
    code: str,
    *,
    request=None,
    organization=None,
) -> bool:
    """Attempt to consume one recovery code.

    Returns True if consumed (valid + not yet used); False otherwise.

    Side effects on True only:
    - Hash removed from profile; session_revocation_counter incremented.
    - request.session['mfa_verified'] = True (when request supplied).
    - mfa.recovery_code_used audit event appended to the org chain.
    - Suspicious-use notification emailed to the user.

    The code value is never logged or stored in audit metadata.
    """
    if not profile.verify_mfa_recovery_code(code):
        return False

    # Mark this session as MFA-verified.
    if request is not None:
        request.session['mfa_verified'] = True

    # Emit one tenant-attributed audit event.
    # organization_id is required for tenant-owned events; None → system chain.
    try:
        from contracts.services.audit import append_audit
        append_audit(
            action='UPDATE',
            model_name='UserProfile',
            organization=organization,
            user=profile.user,
            object_id=profile.pk,
            object_repr=str(profile),
            event_type='mfa.recovery_code_used',
            actor_type='human',
            outcome='success',
            changes={
                'event': 'mfa.recovery_code_used',
                'organization_id': getattr(organization, 'id', None),
                # Never store the code value here.
            },
        )
    except Exception:
        logger.exception(
            'mfa.recovery_code_used audit write failed user=%s', profile.user_id
        )

    # Notify the account owner that a recovery code was used.
    try:
        from contracts.services.notifications import send_suspicious_recovery_use_notification
        send_suspicious_recovery_use_notification(profile.user)
    except Exception:
        logger.exception(
            'suspicious_recovery_use notification failed user=%s', profile.user_id
        )

    return True
