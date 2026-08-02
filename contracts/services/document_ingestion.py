"""Quarantine-first document ingestion boundary.

Untrusted bytes remain outside canonical ``Document`` storage until a named
scanner returns CLEAN and an authorized caller explicitly releases them.  The
service is committed default-off and emits content-minimized append-only audit
evidence for every material transition.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.files.storage import storages
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string

from contracts.middleware import log_action
from contracts.models import (
    AuditLog,
    Document,
    DocumentIngestionAttempt,
    LegalHold,
    OrganizationMembership,
)
from contracts.services.document_upload_policy import (
    DocumentUploadValidationError,
    validate_document_upload,
)
from contracts.services.document_version_service import create_document_version


class IngestionState(Enum):
    LEGACY = 'legacy'
    ENFORCE = 'enforce'
    FAIL_CLOSED = 'fail_closed'


class ScanVerdict(str, Enum):
    CLEAN = 'CLEAN'
    MALICIOUS = 'MALICIOUS'
    UNSCANNABLE = 'UNSCANNABLE'
    ERROR = 'ERROR'


@dataclass(frozen=True)
class ScanResult:
    verdict: ScanVerdict
    provider: str
    signature_version: str = ''
    failure_code: str = ''


class DocumentIngestionError(Exception):
    """Base error with deliberately content-free caller text."""


class DocumentIngestionUnavailable(DocumentIngestionError):
    pass


class DocumentIngestionRejected(DocumentIngestionError):
    pass


class DocumentReleaseDenied(DocumentIngestionError):
    pass


def _csv_setting(name: str) -> set[str]:
    value = getattr(settings, name, '') or ''
    return {part.strip() for part in str(value).split(',') if part.strip()}


def document_ingestion_state(organization) -> IngestionState:
    """Resolve the bounded environment/workspace gate without granting access."""
    enabled = bool(getattr(settings, 'DOCUMENT_QUARANTINE_ENFORCEMENT_ENABLED', False))
    abort = bool(getattr(settings, 'DOCUMENT_QUARANTINE_ABORT_FAIL_CLOSED', False))
    if abort:
        return IngestionState.FAIL_CLOSED
    if not enabled:
        return IngestionState.LEGACY
    environments = _csv_setting('DOCUMENT_QUARANTINE_ENVIRONMENTS')
    organizations = _csv_setting('DOCUMENT_QUARANTINE_ORG_ALLOWLIST')
    environment = str(getattr(settings, 'DJANGO_ENV', '') or '').strip()
    slug = str(getattr(organization, 'slug', '') or '').strip()
    if not environments or not organizations or environment not in environments or slug not in organizations:
        return IngestionState.FAIL_CLOSED
    return IngestionState.ENFORCE


def _assert_actor_access(actor, organization) -> None:
    if actor is None or not getattr(actor, 'is_authenticated', False):
        raise PermissionDenied('Document ingestion requires an authenticated workspace member.')
    if not OrganizationMembership.objects.filter(
        organization=organization,
        user=actor,
        is_active=True,
        organization__is_active=True,
    ).exists():
        raise PermissionDenied('Document ingestion is not available.')


def _assert_target_tenant(organization, *targets) -> None:
    for target in targets:
        if target is None:
            continue
        if getattr(target, 'organization_id', None) != organization.pk:
            raise PermissionDenied('Document ingestion is not available.')


def _detect_media_type(spooled_file, extension: str) -> str:
    """Validate byte signatures and bounded DOCX archive structure."""
    spooled_file.seek(0)
    header = spooled_file.read(8192)
    spooled_file.seek(0)
    if extension == '.pdf':
        if not header.startswith(b'%PDF-'):
            raise DocumentIngestionRejected('The document could not be accepted.')
        return 'application/pdf'
    if extension == '.docx':
        if not header.startswith(b'PK'):
            raise DocumentIngestionRejected('The document could not be accepted.')
        try:
            with zipfile.ZipFile(spooled_file) as archive:
                entries = archive.infolist()
                if len(entries) > 2000:
                    raise DocumentIngestionRejected('The document could not be accepted.')
                names = {entry.filename for entry in entries}
                if '[Content_Types].xml' not in names or not any(
                    name.startswith('word/') for name in names
                ):
                    raise DocumentIngestionRejected('The document could not be accepted.')
                total_uncompressed = 0
                for entry in entries:
                    total_uncompressed += entry.file_size
                    if total_uncompressed > 200 * 1024 * 1024:
                        raise DocumentIngestionRejected('The document could not be accepted.')
                    if entry.file_size > 0 and entry.compress_size == 0:
                        raise DocumentIngestionRejected('The document could not be accepted.')
                    if entry.compress_size and entry.file_size / entry.compress_size > 100:
                        raise DocumentIngestionRejected('The document could not be accepted.')
                    nested_extension = os.path.splitext(entry.filename.lower())[1]
                    if nested_extension in {'.zip', '.7z', '.rar', '.tar', '.gz'}:
                        raise DocumentIngestionRejected('The document could not be accepted.')
        except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
            raise DocumentIngestionRejected('The document could not be accepted.') from exc
        finally:
            spooled_file.seek(0)
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    if b'\x00' in header:
        raise DocumentIngestionRejected('The document could not be accepted.')
    try:
        header.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise DocumentIngestionRejected('The document could not be accepted.') from exc
    return {
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.csv': 'text/csv',
        '.html': 'text/html',
        '.xml': 'application/xml',
        '.json': 'application/json',
    }[extension]


def _audit(attempt, event_type: str, *, actor, outcome=AuditLog.Outcome.SUCCESS, extra=None) -> None:
    changes = {
        'event': event_type,
        'correlation_id': str(attempt.correlation_id),
        'digest': attempt.file_hash,
        'size': attempt.file_size,
        'media_type': attempt.detected_media_type,
        'status': attempt.status,
        'verdict': attempt.verdict,
    }
    if extra:
        changes.update(extra)
    log_action(
        actor,
        AuditLog.Action.CREATE,
        'DocumentIngestionAttempt',
        attempt.pk,
        f'Ingestion {attempt.correlation_id}',
        organization=attempt.organization,
        event_type=event_type,
        outcome=outcome,
        changes=changes,
    )


def _load_scanner():
    scanner_path = str(getattr(settings, 'DOCUMENT_MALWARE_SCANNER_CLASS', '') or '').strip()
    if not scanner_path:
        raise DocumentIngestionUnavailable('Document scanning is unavailable.')
    scanner_class = import_string(scanner_path)
    return scanner_class()


class DocumentIngestionService:
    storage_alias = 'quarantine'

    def quarantine(
        self,
        *,
        organization,
        uploaded_file,
        actor,
        contract=None,
        matter=None,
        client=None,
    ) -> DocumentIngestionAttempt:
        if document_ingestion_state(organization) is not IngestionState.ENFORCE:
            raise DocumentIngestionUnavailable('Document ingestion is unavailable.')
        _assert_actor_access(actor, organization)
        _assert_target_tenant(organization, contract, matter, client)
        try:
            validate_document_upload(uploaded_file)
        except DocumentUploadValidationError as exc:
            raise DocumentIngestionRejected('The document could not be accepted.') from exc

        extension = os.path.splitext(getattr(uploaded_file, 'name', '') or '')[1].lower()
        digest = hashlib.sha256()
        size = 0
        with tempfile.SpooledTemporaryFile(max_size=5 * 1024 * 1024) as staged:
            for chunk in uploaded_file.chunks():
                size += len(chunk)
                digest.update(chunk)
                staged.write(chunk)
            staged.seek(0)
            detected_media_type = _detect_media_type(staged, extension)
            file_hash = digest.hexdigest()
            correlation_id = uuid.uuid4()
            key = f'{organization.pk}/{correlation_id}/{file_hash}'
            storage = storages[self.storage_alias]
            stored_key = storage.save(key, File(staged, name=file_hash))
            try:
                with transaction.atomic():
                    attempt = DocumentIngestionAttempt.objects.create(
                        organization=organization,
                        correlation_id=correlation_id,
                        status=DocumentIngestionAttempt.Status.QUARANTINED,
                        quarantine_object_key=stored_key,
                        file_hash=file_hash,
                        file_size=size,
                        detected_media_type=detected_media_type,
                        contract=contract,
                        matter=matter,
                        client=client,
                        uploaded_by=actor,
                    )
                    _audit(attempt, 'document.ingestion.received', actor=actor)
                    _audit(attempt, 'document.ingestion.quarantined', actor=actor)
            except Exception:
                storage.delete(stored_key)
                raise
        return attempt

    @transaction.atomic
    def scan(self, *, attempt, actor) -> DocumentIngestionAttempt:
        attempt = DocumentIngestionAttempt.objects.select_for_update().select_related(
            'organization',
        ).get(pk=attempt.pk)
        if document_ingestion_state(attempt.organization) is not IngestionState.ENFORCE:
            raise DocumentIngestionUnavailable('Document scanning is unavailable.')
        _assert_actor_access(actor, attempt.organization)
        if attempt.status in {
            DocumentIngestionAttempt.Status.CLEAN,
            DocumentIngestionAttempt.Status.REJECTED,
            DocumentIngestionAttempt.Status.RELEASED,
        }:
            return attempt
        if attempt.status not in {
            DocumentIngestionAttempt.Status.QUARANTINED,
            DocumentIngestionAttempt.Status.ERROR,
        }:
            raise DocumentIngestionUnavailable('Document scanning is unavailable.')

        attempt.status = DocumentIngestionAttempt.Status.SCANNING
        attempt.scan_started_at = timezone.now()
        attempt.failure_code = ''
        attempt.save(update_fields=['status', 'scan_started_at', 'failure_code'])
        _audit(attempt, 'document.ingestion.scan_started', actor=actor)

        storage = storages[self.storage_alias]
        try:
            scanner = _load_scanner()
            with storage.open(attempt.quarantine_object_key, 'rb') as quarantined:
                result = scanner.scan(
                    quarantined,
                    timeout_seconds=int(
                        getattr(settings, 'DOCUMENT_MALWARE_SCAN_TIMEOUT_SECONDS', 30)
                    ),
                    file_size=attempt.file_size,
                    digest=attempt.file_hash,
                    media_type=attempt.detected_media_type,
                )
            if not isinstance(result, ScanResult) or not isinstance(result.verdict, ScanVerdict):
                raise ValueError('invalid scanner response')
        except Exception:
            attempt.status = DocumentIngestionAttempt.Status.ERROR
            attempt.verdict = DocumentIngestionAttempt.Verdict.ERROR
            attempt.failure_code = 'SCANNER_ERROR'
            attempt.scanned_at = timezone.now()
            attempt.save(update_fields=['status', 'verdict', 'failure_code', 'scanned_at'])
            _audit(
                attempt,
                'document.ingestion.verdict_recorded',
                actor=actor,
                outcome=AuditLog.Outcome.FAILURE,
                extra={'failure_code': 'SCANNER_ERROR'},
            )
            return attempt

        attempt.scanner_provider = str(result.provider or '')[:100]
        attempt.scanner_signature_version = str(result.signature_version or '')[:120]
        attempt.failure_code = str(result.failure_code or '')[:64]
        attempt.verdict = result.verdict.value
        attempt.scanned_at = timezone.now()
        if result.verdict is ScanVerdict.CLEAN:
            attempt.status = DocumentIngestionAttempt.Status.CLEAN
            outcome = AuditLog.Outcome.SUCCESS
        else:
            attempt.status = DocumentIngestionAttempt.Status.REJECTED
            outcome = AuditLog.Outcome.BLOCKED
        attempt.save(update_fields=[
            'scanner_provider', 'scanner_signature_version', 'failure_code',
            'verdict', 'scanned_at', 'status',
        ])
        _audit(
            attempt,
            'document.ingestion.verdict_recorded',
            actor=actor,
            outcome=outcome,
            extra={
                'provider': attempt.scanner_provider,
                'signature_version': attempt.scanner_signature_version,
                'failure_code': attempt.failure_code,
            },
        )
        return attempt

    @transaction.atomic
    def release(
        self,
        *,
        attempt,
        actor,
        title,
        document_type=Document.DocType.OTHER,
        status=Document.Status.DRAFT,
        description='',
        source='manual_upload',
        tags='',
        is_privileged=False,
        is_confidential=False,
        request=None,
    ):
        attempt = DocumentIngestionAttempt.objects.select_for_update().select_related(
            'organization', 'contract', 'matter', 'client', 'released_document',
            'released_document_version',
        ).get(pk=attempt.pk)
        _assert_actor_access(actor, attempt.organization)
        if attempt.status == DocumentIngestionAttempt.Status.RELEASED:
            return attempt.released_document, attempt.released_document_version
        if (
            document_ingestion_state(attempt.organization) is not IngestionState.ENFORCE
            or not bool(getattr(settings, 'DOCUMENT_QUARANTINE_RELEASE_ENABLED', False))
        ):
            raise DocumentReleaseDenied('Document release is unavailable.')
        if attempt.status != DocumentIngestionAttempt.Status.CLEAN or attempt.verdict != ScanVerdict.CLEAN.value:
            raise DocumentReleaseDenied('Document release is unavailable.')
        if not str(title or '').strip():
            raise DocumentReleaseDenied('Document release is unavailable.')
        if document_type not in {value for value, _label in Document.DocType.choices}:
            raise DocumentReleaseDenied('Document release is unavailable.')
        if status not in {value for value, _label in Document.Status.choices}:
            raise DocumentReleaseDenied('Document release is unavailable.')
        _assert_target_tenant(attempt.organization, attempt.contract, attempt.matter, attempt.client)
        _audit(attempt, 'document.ingestion.release_started', actor=actor)

        storage = storages[self.storage_alias]
        try:
            with transaction.atomic():
                with storage.open(attempt.quarantine_object_key, 'rb') as quarantined:
                    released_file = File(quarantined, name=attempt.file_hash)
                    released_file.content_type = attempt.detected_media_type
                    document, version = create_document_version(
                        organization=attempt.organization,
                        title=str(title).strip()[:300],
                        document_type=document_type,
                        status=status,
                        description=description,
                        file=released_file,
                        contract=attempt.contract,
                        matter=attempt.matter,
                        client=attempt.client,
                        uploaded_by=actor,
                        actor=actor,
                        source=source,
                        tags=tags,
                        is_privileged=bool(is_privileged),
                        is_confidential=bool(is_confidential),
                        share_with_counterparty=False,
                        request=request,
                        supersede_prior=False,
                    )
        except Exception:
            _audit(
                attempt,
                'document.ingestion.release_failed',
                actor=actor,
                outcome=AuditLog.Outcome.FAILURE,
                extra={'failure_code': 'RELEASE_ERROR'},
            )
            raise DocumentReleaseDenied('Document release is unavailable.')

        attempt.status = DocumentIngestionAttempt.Status.RELEASED
        attempt.released_document = document
        attempt.released_document_version = version
        attempt.released_at = timezone.now()
        attempt.failure_code = ''
        attempt.save(update_fields=[
            'status', 'released_document', 'released_document_version',
            'released_at', 'failure_code',
        ])
        _audit(
            attempt,
            'document.ingestion.released',
            actor=actor,
            extra={'document_id': document.pk, 'document_version_id': version.pk},
        )
        attempt_id = attempt.pk
        transaction.on_commit(
            lambda: self._cleanup_released_quarantine(attempt_id=attempt_id, actor=actor)
        )
        return document, version

    def _cleanup_released_quarantine(self, *, attempt_id, actor) -> None:
        attempt = DocumentIngestionAttempt.objects.select_related('organization').get(pk=attempt_id)
        storage = storages[self.storage_alias]
        try:
            storage.delete(attempt.quarantine_object_key)
        except Exception:
            attempt.failure_code = 'CLEANUP_PENDING'
            attempt.save(update_fields=['failure_code'])
            _audit(
                attempt,
                'document.ingestion.release_failed',
                actor=actor,
                outcome=AuditLog.Outcome.FAILURE,
                extra={'failure_code': 'CLEANUP_PENDING'},
            )
            return
        attempt.cleanup_completed_at = timezone.now()
        attempt.save(update_fields=['cleanup_completed_at'])
        _audit(attempt, 'document.ingestion.cleanup_completed', actor=actor)

    def is_held(self, attempt) -> bool:
        matter_id = attempt.matter_id or getattr(attempt.contract, 'matter_id', None)
        client_id = attempt.client_id or getattr(attempt.contract, 'client_id', None)
        holds = LegalHold.objects.filter(
            organization=attempt.organization,
            status=LegalHold.Status.ACTIVE,
        )
        return bool(
            (matter_id and holds.filter(matter_id=matter_id).exists())
            or (client_id and holds.filter(client_id=client_id).exists())
        )

    @transaction.atomic
    def expire(self, *, attempt, actor=None, system=False) -> DocumentIngestionAttempt:
        attempt = DocumentIngestionAttempt.objects.select_for_update().select_related(
            'organization', 'contract',
        ).get(pk=attempt.pk)
        if not system:
            _assert_actor_access(actor, attempt.organization)
        retention_days = int(getattr(settings, 'DOCUMENT_QUARANTINE_RETENTION_DAYS', 0) or 0)
        if (
            retention_days <= 0
            or not bool(getattr(settings, 'DOCUMENT_QUARANTINE_PURGE_ENABLED', False))
            or document_ingestion_state(attempt.organization) is not IngestionState.ENFORCE
        ):
            _audit(
                attempt,
                'document.ingestion.retention_blocked',
                actor=actor,
                outcome=AuditLog.Outcome.BLOCKED,
                extra={'failure_code': 'RETENTION_NOT_AUTHORIZED'},
            )
            raise DocumentReleaseDenied('Quarantine retention is not authorized.')
        cutoff = timezone.now() - timedelta(days=retention_days)
        if attempt.received_at > cutoff or attempt.status == DocumentIngestionAttempt.Status.RELEASED:
            raise DocumentReleaseDenied('Quarantine retention is not applicable.')
        if self.is_held(attempt):
            _audit(
                attempt,
                'document.ingestion.retention_blocked',
                actor=actor,
                outcome=AuditLog.Outcome.BLOCKED,
                extra={'failure_code': 'LEGAL_HOLD'},
            )
            raise DocumentReleaseDenied('Quarantine retention is blocked.')
        storage = storages[self.storage_alias]
        if attempt.quarantine_object_key and storage.exists(attempt.quarantine_object_key):
            storage.delete(attempt.quarantine_object_key)
        attempt.status = DocumentIngestionAttempt.Status.EXPIRED
        attempt.expires_at = timezone.now()
        attempt.cleanup_completed_at = timezone.now()
        attempt.save(update_fields=['status', 'expires_at', 'cleanup_completed_at'])
        _audit(attempt, 'document.ingestion.expired', actor=actor)
        return attempt


def get_document_ingestion_service() -> DocumentIngestionService:
    return DocumentIngestionService()


def quarantine_and_scan_if_enforced(
    *, organization, uploaded_file, actor, contract=None, matter=None, client=None,
):
    """Route a browser upload through quarantine when the bounded gate is active.

    ``None`` means the legacy path remains authoritative while the committed
    gate is off.  A fail-closed/abort state raises rather than restoring direct
    canonical storage.
    """
    state = document_ingestion_state(organization)
    if state is IngestionState.LEGACY:
        return None
    if state is IngestionState.FAIL_CLOSED:
        raise DocumentIngestionUnavailable('Document ingestion is unavailable.')
    service = get_document_ingestion_service()
    attempt = service.quarantine(
        organization=organization,
        uploaded_file=uploaded_file,
        actor=actor,
        contract=contract,
        matter=matter,
        client=client,
    )
    return service.scan(attempt=attempt, actor=actor)
