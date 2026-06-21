"""Authoritative MFA-policy rules — one source of truth for every interface.

Background (blocker A3): MFA enforcement used to read ``OrgPolicy.mfa_required``
at login while the admin settings UI wrote ``Organization.require_mfa``. The two
were never synchronized, and ``OrgPolicy`` is a lazy one-to-one that may not
exist — so ``org.policy.mfa_required`` raised ``RelatedObjectDoesNotExist``,
which a broad ``except Exception: pass`` swallowed, silently disabling MFA.

Source of truth: ``Organization.require_mfa``.
  * It is a concrete column present on every Organization row, so reading it can
    never raise a missing-relation error — enforcement therefore cannot fail
    open through a missing record.
  * It is the field the admin settings UI actually toggles.
  * It is read by the session middleware and the SAML path already.

``OrgPolicy.mfa_required`` is kept as a synchronized *mirror* (it is surfaced in
the admin console / compliance exports), but it is never the authority for
enforcement. Always go through these helpers so HTML views, forms, APIs,
management commands and background jobs apply the identical rule.
"""
from __future__ import annotations

from django.db import transaction

from contracts.models import OrgPolicy, Organization


def ensure_org_policy(org: Organization) -> OrgPolicy:
    """Return the org's policy row, creating it (mirrored to require_mfa) if absent."""
    policy, created = OrgPolicy.objects.get_or_create(
        organization=org,
        defaults={'mfa_required': bool(getattr(org, 'require_mfa', False))},
    )
    return policy


def organization_requires_mfa(org) -> bool:
    """Authoritative check: does this organization require MFA?

    Fail-closed by construction — reads a plain boolean column that always
    exists. Returns False only when there is genuinely no organization.
    """
    if org is None:
        return False
    return bool(getattr(org, 'require_mfa', False))


@transaction.atomic
def set_organization_mfa_required(org: Organization, required: bool, *, user=None) -> None:
    """Set the authoritative flag and keep the OrgPolicy mirror in sync."""
    required = bool(required)
    if org.require_mfa != required:
        org.require_mfa = required
        org.save(update_fields=['require_mfa', 'updated_at'])
    policy = ensure_org_policy(org)
    if policy.mfa_required != required or (user is not None and policy.updated_by_id != getattr(user, 'id', None)):
        policy.mfa_required = required
        if user is not None:
            policy.updated_by = user
        policy.save(update_fields=['mfa_required', 'updated_by', 'updated_at'])


def mirror_policy_mfa_to_organization(org: Organization, policy: OrgPolicy, *, user=None) -> None:
    """When a policy write changes mfa_required, propagate it to the authority."""
    required = bool(policy.mfa_required)
    if org.require_mfa != required:
        org.require_mfa = required
        org.save(update_fields=['require_mfa', 'updated_at'])
