"""Explicit quarantine, status and clean-release endpoints."""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from contracts.models import Contract, Document, DocumentIngestionAttempt
from contracts.permissions import ContractAction, can_access_contract_action
from contracts.services.document_ingestion import (
    DocumentIngestionError,
    IngestionState,
    document_ingestion_state,
    get_document_ingestion_service,
)
from contracts.services.repository import apply_repository_contract_policy
from contracts.tenancy import get_user_organization


def _not_available():
    return JsonResponse({'ok': False, 'error': 'Document ingestion is unavailable.'}, status=404)


def _attempt_for_user(request, correlation_id):
    organization = get_user_organization(request.user)
    if organization is None or document_ingestion_state(organization) is not IngestionState.ENFORCE:
        return None, organization
    attempt = DocumentIngestionAttempt.objects.filter(
        organization=organization,
        correlation_id=correlation_id,
    ).select_related('contract').first()
    if attempt is None:
        return None, organization
    if attempt.contract and not can_access_contract_action(
        request.user,
        attempt.contract,
        ContractAction.EDIT,
    ):
        return None, organization
    return attempt, organization


@login_required
@require_http_methods(['POST'])
def document_ingestion_quarantine_api(request):
    organization = get_user_organization(request.user)
    if organization is None or document_ingestion_state(organization) is not IngestionState.ENFORCE:
        return _not_available()
    uploaded_file = request.FILES.get('file')
    if uploaded_file is None:
        return JsonResponse({'ok': False, 'error': 'A document is required.'}, status=400)
    contract = None
    contract_id = request.POST.get('contract_id')
    if contract_id:
        contract = apply_repository_contract_policy(
            Contract.objects.filter(pk=contract_id, organization=organization),
            organization=organization,
            user=request.user,
            surface='document_ingestion_quarantine_contract',
        ).first()
        if contract is None or not can_access_contract_action(
            request.user,
            contract,
            ContractAction.EDIT,
        ):
            return _not_available()
    service = get_document_ingestion_service()
    try:
        attempt = service.quarantine(
            organization=organization,
            uploaded_file=uploaded_file,
            actor=request.user,
            contract=contract,
        )
        attempt = service.scan(attempt=attempt, actor=request.user)
    except (DocumentIngestionError, PermissionDenied):
        return JsonResponse(
            {'ok': False, 'error': 'The document could not be accepted.'},
            status=400,
        )
    return JsonResponse({
        'ok': True,
        'correlation_id': str(attempt.correlation_id),
        'status': attempt.status,
        'releasable': attempt.status == DocumentIngestionAttempt.Status.CLEAN,
    }, status=202)


@login_required
@require_http_methods(['GET'])
def document_ingestion_status_api(request, correlation_id):
    attempt, _organization = _attempt_for_user(request, correlation_id)
    if attempt is None:
        return _not_available()
    return JsonResponse({
        'ok': True,
        'correlation_id': str(attempt.correlation_id),
        'status': attempt.status,
        'releasable': attempt.status == DocumentIngestionAttempt.Status.CLEAN,
        'released_document_id': attempt.released_document_id,
    })


@login_required
@require_http_methods(['POST'])
def document_ingestion_release_api(request, correlation_id):
    attempt, _organization = _attempt_for_user(request, correlation_id)
    if attempt is None:
        return _not_available()
    document_type = request.POST.get('document_type') or Document.DocType.OTHER
    if document_type not in {value for value, _label in Document.DocType.choices}:
        return JsonResponse({'ok': False, 'error': 'Invalid document type.'}, status=400)
    title = (request.POST.get('title') or '').strip()
    if not title:
        return JsonResponse({'ok': False, 'error': 'A document title is required.'}, status=400)
    try:
        document, version = get_document_ingestion_service().release(
            attempt=attempt,
            actor=request.user,
            title=title,
            document_type=document_type,
            status=Document.Status.DRAFT,
            description=(request.POST.get('description') or '').strip(),
            source='manual_upload',
            tags=(request.POST.get('tags') or '').strip(),
            is_privileged=request.POST.get('is_privileged') in {'1', 'true', 'True', 'on'},
            is_confidential=request.POST.get('is_confidential') in {'1', 'true', 'True', 'on'},
            request=request,
        )
    except (DocumentIngestionError, PermissionDenied):
        return _not_available()
    return JsonResponse({
        'ok': True,
        'document_id': document.pk,
        'document_version_id': version.pk,
        'correlation_id': str(attempt.correlation_id),
    }, status=201)
