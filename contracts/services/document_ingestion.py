"""Controlled multi-document and inbound-email ingestion.

This service intentionally reuses Contract, DocumentVersion, DocumentReviewRun,
provenance, and audit services.  Extraction output is review metadata only: it
never writes an authoritative contract field without a human confirmation.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass, field

from django.db import transaction
from django.urls import reverse

from contracts.middleware import log_action
from contracts.models import AuditLog, Contract, Document, DocumentReviewRun, Organization
from contracts.services.agreement_metadata_extract import extract_agreement_metadata, extract_text_from_upload
from contracts.services.contract_import_lifecycle import persist_contract_with_imported_lifecycle
from contracts.services.document_version_service import create_document_version


ALLOWED_EXTENSIONS = frozenset({'.pdf', '.docx', '.txt', '.md', '.csv', '.html', '.xml', '.json'})
MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
MAX_DOCUMENTS_PER_REQUEST = 50
MAX_BATCH_BYTES = 250 * 1024 * 1024


class DocumentIngestionError(ValueError):
    """A validation failure that is safe to return to an ingestion caller."""


@dataclass
class IngestionResult:
    created: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    correlation_id: str = ''

    def to_dict(self) -> dict:
        return {
            'created_count': len(self.created),
            'skipped_count': len(self.skipped),
            'created': self.created,
            'skipped': self.skipped,
            'correlation_id': self.correlation_id,
        }


def _filename_title(upload) -> str:
    filename = os.path.basename(getattr(upload, 'name', '') or '')
    title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').strip()
    return title[:200] or 'Imported agreement'


def _validate_uploads(files) -> list:
    uploads = [upload for upload in files if upload is not None]
    if not uploads:
        raise DocumentIngestionError('Attach at least one supported agreement file.')
    if len(uploads) > MAX_DOCUMENTS_PER_REQUEST:
        raise DocumentIngestionError(f'Import at most {MAX_DOCUMENTS_PER_REQUEST} documents in one request.')
    total_size = 0
    for upload in uploads:
        size = int(getattr(upload, 'size', 0) or 0)
        extension = os.path.splitext(getattr(upload, 'name', '') or '')[1].lower()
        if not extension or extension not in ALLOWED_EXTENSIONS:
            raise DocumentIngestionError(
                f'{getattr(upload, "name", "File")}: unsupported file type. '
                f'Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
            )
        if size <= 0:
            raise DocumentIngestionError(f'{getattr(upload, "name", "File")}: the file is empty.')
        if size > MAX_DOCUMENT_BYTES:
            raise DocumentIngestionError(
                f'{getattr(upload, "name", "File")}: each file must be at most '
                f'{MAX_DOCUMENT_BYTES // (1024 * 1024)} MB.'
            )
        total_size += size
    if total_size > MAX_BATCH_BYTES:
        raise DocumentIngestionError(
            f'The combined upload must be at most {MAX_BATCH_BYTES // (1024 * 1024)} MB.'
        )
    return uploads


def _review_metadata(extraction, *, channel: str, correlation_id: str) -> dict:
    """Keep all derived values explicitly unverified and evidence-linked."""
    payload = extraction.to_dict()
    return {
        'metadata_extraction': payload,
        'extraction_status': 'extracted_unverified',
        'governing_law_confirmed': False,
        'value_confirmed': False,
        'payment_terms_confirmed': False,
        'ingestion_channel': channel,
        'ingestion_correlation_id': correlation_id,
    }


class DocumentIngestionService:
    """Application service for batch and email-forwarded document ingress."""

    def ingest_batch(
        self,
        *,
        organization,
        files,
        actor=None,
        channel: str,
        request=None,
        correlation_id: str | None = None,
        source_message_id: str = '',
    ) -> IngestionResult:
        if organization is None or not organization.is_active:
            raise DocumentIngestionError('The workspace is not available for import.')
        uploads = _validate_uploads(files)
        correlation_id = correlation_id or uuid.uuid4().hex
        result = IngestionResult(correlation_id=correlation_id)

        # A workspace row lock makes the email Message-ID replay check safe in
        # PostgreSQL as well as in local SQLite development.
        with transaction.atomic():
            Organization.objects.select_for_update().get(pk=organization.pk)
            for index, upload in enumerate(uploads, start=1):
                external_id = self._external_id(source_message_id, index)
                if external_id and Contract.objects.filter(
                    organization=organization,
                    source_system='email_forwarding',
                    source_system_id=external_id,
                ).exists():
                    result.skipped.append({
                        'filename': upload.name,
                        'reason': 'This email attachment was already ingested.',
                    })
                    continue
                try:
                    # A savepoint keeps a single broken document from
                    # poisoning the rest of a requested batch.
                    with transaction.atomic():
                        result.created.append(self._ingest_one(
                            organization=organization,
                            upload=upload,
                            actor=actor,
                            channel=channel,
                            request=request,
                            correlation_id=correlation_id,
                            external_id=external_id,
                        ))
                except DocumentIngestionError as exc:
                    result.skipped.append({'filename': upload.name, 'reason': str(exc)})
                except Exception:
                    # The server-side exception is logged by the normal Django
                    # handler; do not disclose document-derived detail to an
                    # email provider or batch-import browser response.
                    result.skipped.append({
                        'filename': upload.name,
                        'reason': 'The document could not be stored. Try it again or import it individually.',
                    })
        return result

    @staticmethod
    def _external_id(message_id: str, index: int) -> str:
        if not message_id:
            return ''
        digest = hashlib.sha256(message_id.strip().encode('utf-8')).hexdigest()
        return f'{digest}:{index}'

    def _ingest_one(
        self,
        *,
        organization,
        upload,
        actor,
        channel: str,
        request,
        correlation_id: str,
        external_id: str,
    ) -> dict:
        # Readable-text extraction is deterministic and runs before storage;
        # extract_text_from_upload rewinds the upload for immutable persistence.
        text, extraction_source = extract_text_from_upload(upload, upload.name)
        extraction = extract_agreement_metadata(
            text,
            filename=upload.name,
            extraction_source=extraction_source,
        )
        source = 'email_forwarded' if channel == 'email_forwarded' else 'inbound_import'
        contract = Contract(
            organization=organization,
            title=_filename_title(upload),
            contract_type=Contract.ContractType.OTHER,
            owner=actor if getattr(actor, 'is_authenticated', False) else None,
            created_by=actor if getattr(actor, 'is_authenticated', False) else None,
            source_system='email_forwarding' if external_id else '',
            source_system_id=external_id,
        )
        contract, _ = persist_contract_with_imported_lifecycle(
            contract,
            desired_status=Contract.Status.IN_PROGRESS,
            desired_lifecycle_stage=Contract.LifecycleStage.INTAKE,
            actor=actor,
            reason=f'{channel.replace("_", " ")} document ingestion',
            source=source,
            request=request,
            provenance_correlation_id=correlation_id,
        )
        document, _ = create_document_version(
            organization=organization,
            title=upload.name[:300],
            document_type=Document.DocType.CONTRACT,
            status=Document.Status.DRAFT,
            contract=contract,
            uploaded_by=actor if getattr(actor, 'is_authenticated', False) else None,
            actor=actor,
            source='import',
            file=upload,
            request=request,
            supersede_prior=False,
        )
        review_run = DocumentReviewRun.objects.create(
            organization=organization,
            contract=contract,
            document=document,
            status=DocumentReviewRun.Status.CLASSIFICATION_REQUIRED,
            current_step='Classifying',
            progress_steps=[],
            extracted_metadata=_review_metadata(
                extraction,
                channel=channel,
                correlation_id=correlation_id,
            ),
            governance_sources={
                'metadata_extraction': {
                    'use_case': 'metadata_extraction',
                    'source': extraction_source,
                    'authority': 'unverified',
                },
            },
            primary_next_action='Confirm the extracted contract information before review or routing.',
        )
        actor_type = AuditLog.ActorType.HUMAN if getattr(actor, 'is_authenticated', False) else AuditLog.ActorType.WEBHOOK
        log_action(
            actor,
            AuditLog.Action.CREATE,
            'Document',
            document.pk,
            str(document),
            organization=organization,
            request=request,
            event_type='document.ingested',
            actor_type=actor_type,
            changes={
                'event': 'document.ingested',
                'channel': channel,
                'correlation_id': correlation_id,
                'document_id': document.pk,
                'file_hash': document.file_hash,
            },
        )
        log_action(
            actor,
            AuditLog.Action.CREATE,
            'DocumentReviewRun',
            review_run.pk,
            f'Review metadata for document {document.pk}',
            organization=organization,
            request=request,
            event_type='document.metadata_extracted',
            actor_type=actor_type,
            changes={
                'event': 'document.metadata_extracted',
                'document_id': document.pk,
                'extraction_source': extraction_source,
                'status': 'unverified',
            },
        )
        return {
            'filename': upload.name,
            'contract_id': contract.pk,
            'document_id': document.pk,
            'review_run_id': review_run.pk,
            'review_url': reverse('contracts:contract_review_workspace', kwargs={'pk': contract.pk}),
            'metadata': extraction.to_dict(),
        }


_service = DocumentIngestionService()


def get_document_ingestion_service() -> DocumentIngestionService:
    return _service
