"""Tenant-scoped HTML endpoints for the default-off repository CSV import."""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from config.feature_flags import is_repository_csv_import_enabled
from contracts.permissions import can_manage_organization
from contracts.services.repository_csv_import import (
    ImportConflictError,
    ImportTokenError,
    RepositoryCsvImportError,
    csv_template_text,
    get_repository_csv_import_service,
)
from contracts.tenancy import get_user_organization


def _organization_for_import(request):
    organization = getattr(request, 'organization', None) or get_user_organization(request.user)
    if organization is None or not can_manage_organization(request.user, organization):
        raise PermissionDenied('Workspace owner or administrator access is required.')
    return organization


def _require_feature() -> None:
    if not is_repository_csv_import_enabled():
        raise Http404


def _csv_bytes(request) -> bytes | None:
    uploaded = request.FILES.get('csv_file')
    if uploaded is None:
        return None
    return uploaded.read()


@login_required
@require_http_methods(['GET', 'POST'])
def repository_csv_import(request):
    _require_feature()
    try:
        organization = _organization_for_import(request)
    except PermissionDenied:
        return HttpResponseForbidden('Workspace owner or administrator access is required.')

    context = {
        'preview': None,
        'commit_result': None,
        'form_error': '',
    }
    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        csv_bytes = _csv_bytes(request)
        if action not in {'dry_run', 'commit'}:
            context['form_error'] = 'Choose dry-run or commit.'
        elif csv_bytes is None:
            context['form_error'] = 'Choose a CSV file.'
        else:
            service = get_repository_csv_import_service()
            try:
                if action == 'dry_run':
                    context['preview'] = service.preview(
                        organization=organization,
                        actor=request.user,
                        csv_bytes=csv_bytes,
                    )
                else:
                    context['commit_result'] = service.commit(
                        organization=organization,
                        actor=request.user,
                        csv_bytes=csv_bytes,
                        preview_token=request.POST.get('preview_token') or '',
                        request=request,
                    )
            except (ImportTokenError, ImportConflictError, RepositoryCsvImportError):
                context['form_error'] = (
                    'The import could not be committed. Run a new dry-run with the same workspace and CSV.'
                )

    return render(request, 'contracts/repository_csv_import.html', context)


@login_required
@require_GET
def repository_csv_import_template(request):
    _require_feature()
    try:
        _organization_for_import(request)
    except PermissionDenied:
        return HttpResponseForbidden('Workspace owner or administrator access is required.')
    response = HttpResponse(csv_template_text(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="clmone-contract-import-template.csv"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
@require_POST
def repository_csv_import_rollback(request):
    # Rollback remains reachable after the exposure flag is switched off.
    try:
        organization = _organization_for_import(request)
    except PermissionDenied:
        return HttpResponseForbidden('Workspace owner or administrator access is required.')

    context = {
        'preview': None,
        'commit_result': None,
        'rollback_result': None,
        'form_error': '',
    }
    try:
        context['rollback_result'] = get_repository_csv_import_service().rollback(
            organization=organization,
            actor=request.user,
            rollback_token=request.POST.get('rollback_token') or '',
            request=request,
        )
    except (ImportTokenError, ImportConflictError, RepositoryCsvImportError):
        context['form_error'] = (
            'Rollback was not applied. The token is invalid, expired, or an imported record changed.'
        )
    return render(request, 'contracts/repository_csv_import.html', context)
