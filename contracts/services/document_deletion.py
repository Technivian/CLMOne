"""Canonical document deletion service (Phase 4E).

Deletion of legal documents is authorized, retention-aware, and audited:

- Ordinary MEMBER users may delete only documents they uploaded; ADMIN/OWNER may
  delete any document in their organization.
- Documents whose matter/client is under an ACTIVE legal hold cannot be deleted.
- Deletion is a SOFT delete (tombstone): the row and the stored object are
  preserved for evidence; the document is hidden from normal views/search and
  the download endpoint. Permanent purge / GDPR erasure is a separate,
  higher-privilege path (not exposed here).
- Tenant isolation is enforced by callers (org-scoped queryset); the service
  re-checks the actor's membership/role against the document's organization.
"""
from __future__ import annotations

import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


class DocumentDeletionError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class DocumentDeletionForbidden(DocumentDeletionError):
    status_code = 403


class DocumentDeletionBlocked(DocumentDeletionError):
    status_code = 409  # legal hold / retention


def can_delete_document(user, document) -> bool:
    """OWNER/ADMIN may delete any org document; MEMBER only their own uploads."""
    from contracts.permissions import can_manage_organization
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    if can_manage_organization(user, document.organization):  # OWNER/ADMIN
        return True
    return bool(document.uploaded_by_id and document.uploaded_by_id == user.id)


def soft_delete_document(user, document, *, request=None):
    """Authorize, enforce legal hold, soft-delete, and audit. Idempotent."""
    from contracts.middleware import log_action
    from contracts.models import AuditLog

    if document.is_deleted:
        return document  # idempotent

    if not can_delete_document(user, document):
        raise DocumentDeletionForbidden(
            'You do not have permission to delete this document.')

    # Legal hold / retention (reuses the model rule; PermissionError -> blocked).
    try:
        document._check_retention_hold()
    except PermissionError as exc:
        raise DocumentDeletionBlocked(str(exc))

    document.is_deleted = True
    document.deleted_at = timezone.now()
    document.deleted_by = user
    document.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_at'])

    log_action(
        user, AuditLog.Action.DELETE, 'Document',
        object_id=document.pk, object_repr=document.title[:300],
        organization=document.organization, request=request,
        event_type='document.deleted',
        changes={'event': 'document.deleted', 'document_id': document.pk,
                 'contract_id': document.contract_id, 'mode': 'soft'},
    )
    return document
