"""Private-workspace, create-only CSV contract import.

The preview path is deliberately stateless: it performs reads only and returns
a signed token binding the exact CSV bytes, workspace, actor, and correlation
identifier. Commit revalidates under a workspace lock before creating canonical
Contract rows. Rollback is compensating: unchanged imported rows are archived,
never deleted.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from django.core import signing
from django.core.exceptions import PermissionDenied
from django.db import transaction

from contracts.models import (
    AuditLog,
    Contract,
    ContractType,
    Counterparty,
    Organization,
    OrganizationMembership,
)
from contracts.permissions import can_manage_organization
from contracts.services.audit import append_audit
from contracts.services.contract_import_lifecycle import (
    ImportLifecycleError,
    persist_contract_with_imported_lifecycle,
    resolve_import_status_stage,
)
from contracts.services.contract_lifecycle import get_contract_lifecycle_service
from contracts.services.contract_type_catalogue import assign_contract_type, normalize_import_code
from contracts.services.contract_type_activation import is_contract_type_activated
from contracts.services.lifecycle_dimensions import (
    LEGACY_STATUS_TO_RECORD,
    RECORD_STATUSES,
    WORKFLOW_STAGES,
    map_legacy_status_to_record,
)


TEMPLATE_COLUMNS = (
    'title',
    'contract_type',
    'counterparty',
    'owner_email',
    'status',
    'lifecycle_stage',
    'start_date',
    'end_date',
    'renewal_date',
    'notice_period_days',
    'termination_notice_date',
)
REQUIRED_COLUMNS = ('title', 'contract_type', 'counterparty')
MAX_CSV_BYTES = 1_048_576
MAX_ROWS = 500
PREVIEW_TOKEN_MAX_AGE_SECONDS = 30 * 60
ROLLBACK_TOKEN_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
PREVIEW_TOKEN_SALT = 'contracts.repository-csv-import.preview.v1'
ROLLBACK_TOKEN_SALT = 'contracts.repository-csv-import.rollback.v1'

EVENT_BATCH_STARTED = 'contract.import.batch_started'
EVENT_ROW_CREATED = 'contract.import.row_created'
EVENT_BATCH_COMPLETED = 'contract.import.batch_completed'
EVENT_ROLLBACK_STARTED = 'contract.import.rollback_started'
EVENT_ROW_REVERSED = 'contract.import.row_reversed'
EVENT_ROLLBACK_COMPLETED = 'contract.import.rollback_completed'

_VALID_STATUSES = set(RECORD_STATUSES) | set(LEGACY_STATUS_TO_RECORD)
_VALID_STAGES = set(WORKFLOW_STAGES)


class RepositoryCsvImportError(Exception):
    """Base error suitable for a generic, non-leaking UI message."""


class ImportTokenError(RepositoryCsvImportError):
    pass


class ImportConflictError(RepositoryCsvImportError):
    pass


@dataclass(frozen=True)
class ImportIssue:
    row: int
    field: str
    code: str
    message: str

    def as_dict(self) -> dict:
        return {
            'row': self.row,
            'field': self.field,
            'code': self.code,
            'message': self.message,
        }


@dataclass(frozen=True)
class PreparedRow:
    row: int
    title: str
    contract_type: str
    contract_type_id: int
    counterparty: str
    counterparty_id: int
    owner_email: str
    owner_id: int | None
    status: str
    lifecycle_stage: str
    start_date: date | None
    end_date: date | None
    renewal_date: date | None
    notice_period_days: int | None
    termination_notice_date: date | None

    @property
    def duplicate_key(self) -> tuple:
        return (
            _normalize_text(self.title),
            self.contract_type,
            _normalize_text(self.counterparty),
            self.start_date,
            self.end_date,
        )

    def as_preview_dict(self) -> dict:
        return {
            'row': self.row,
            'title': self.title,
            'contract_type': self.contract_type,
            'counterparty': self.counterparty,
            'owner_email': self.owner_email,
            'status': self.status,
            'lifecycle_stage': self.lifecycle_stage,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'renewal_date': self.renewal_date,
            'notice_period_days': self.notice_period_days,
            'termination_notice_date': self.termination_notice_date,
        }


@dataclass(frozen=True)
class ImportPreview:
    correlation_id: str
    csv_digest: str
    rows: tuple[PreparedRow, ...]
    issues: tuple[ImportIssue, ...]
    preview_token: str

    @property
    def is_valid(self) -> bool:
        return not self.issues and bool(self.rows)

    @property
    def valid_count(self) -> int:
        invalid_rows = {issue.row for issue in self.issues if issue.row > 1}
        return sum(1 for row in self.rows if row.row not in invalid_rows)


@dataclass(frozen=True)
class ImportCommitResult:
    correlation_id: str
    contract_ids: tuple[int, ...]
    rollback_token: str


@dataclass(frozen=True)
class ImportRollbackResult:
    correlation_id: str
    archived_contract_ids: tuple[int, ...]


def csv_template_text() -> str:
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(TEMPLATE_COLUMNS)
    writer.writerow(
        (
            'Synthetic payroll services agreement',
            'MSA',
            'Synthetic Payroll Services B.V.',
            '',
            'ACTIVE',
            'OBLIGATION_TRACKING',
            '2026-01-01',
            '2027-01-01',
            '2027-01-01',
            '90',
            '2026-10-03',
        )
    )
    return output.getvalue()


def _normalize_text(value: str | None) -> str:
    return ' '.join((value or '').split()).casefold()


def _clean_text(value: str | None) -> str:
    return ' '.join((value or '').split())


def _digest(csv_bytes: bytes) -> str:
    return hashlib.sha256(csv_bytes).hexdigest()


def _issue(row: int, field: str, code: str, message: str) -> ImportIssue:
    return ImportIssue(row=row, field=field, code=code, message=message)


def _sorted_issues(issues: Iterable[ImportIssue]) -> tuple[ImportIssue, ...]:
    field_order = {field: index for index, field in enumerate(TEMPLATE_COLUMNS)}
    return tuple(
        sorted(
            issues,
            key=lambda item: (
                item.row,
                field_order.get(item.field, len(field_order)),
                item.field,
                item.code,
                item.message,
            ),
        )
    )


def _parse_date(raw: str, *, row: int, field: str, issues: list[ImportIssue]) -> date | None:
    value = (raw or '').strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        issues.append(_issue(row, field, 'invalid_date', f'{field} must use YYYY-MM-DD.'))
        return None


def _parse_notice_period(raw: str, *, row: int, issues: list[ImportIssue]) -> int | None:
    value = (raw or '').strip()
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError:
        issues.append(
            _issue(
                row,
                'notice_period_days',
                'invalid_integer',
                'notice_period_days must be a whole number from 0 to 3650.',
            )
        )
        return None
    if parsed < 0 or parsed > 3650:
        issues.append(
            _issue(
                row,
                'notice_period_days',
                'out_of_range',
                'notice_period_days must be a whole number from 0 to 3650.',
            )
        )
        return None
    return parsed


def _canonical_type(raw: str) -> str | None:
    return normalize_import_code(raw, unknown_to_other=False)


def _canonical_status(raw: str) -> str:
    normalized = (raw or '').strip().upper() or Contract.Status.IN_PROGRESS
    return map_legacy_status_to_record(normalized)


def _records_fingerprint(contracts: Iterable[Contract]) -> str:
    rows = [
        {
            'id': contract.pk,
            'status': contract.status,
            'lifecycle_stage': contract.lifecycle_stage,
            'updated_at': contract.updated_at.isoformat(),
        }
        for contract in contracts
    ]
    material = json.dumps(rows, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(material.encode('utf-8')).hexdigest()


class RepositoryCsvImportService:
    """Application service for the governed repository import lifecycle."""

    def _authorize(self, *, organization, actor) -> None:
        if not can_manage_organization(actor, organization):
            raise PermissionDenied('Workspace owner or administrator access is required.')

    def preview(self, *, organization, actor, csv_bytes: bytes) -> ImportPreview:
        self._authorize(organization=organization, actor=actor)
        correlation_id = str(uuid.uuid4())
        rows, issues, csv_digest = self._analyse(
            organization=organization,
            csv_bytes=csv_bytes,
        )
        token = ''
        if rows and not issues:
            token = signing.dumps(
                {
                    'v': 1,
                    'purpose': 'preview',
                    'organization_id': organization.pk,
                    'actor_id': actor.pk,
                    'csv_digest': csv_digest,
                    'correlation_id': correlation_id,
                    'row_count': len(rows),
                },
                salt=PREVIEW_TOKEN_SALT,
                compress=True,
            )
        return ImportPreview(
            correlation_id=correlation_id,
            csv_digest=csv_digest,
            rows=rows,
            issues=issues,
            preview_token=token,
        )

    @transaction.atomic
    def commit(
        self,
        *,
        organization,
        actor,
        csv_bytes: bytes,
        preview_token: str,
        request=None,
    ) -> ImportCommitResult:
        self._authorize(organization=organization, actor=actor)
        token = self._load_token(
            preview_token,
            salt=PREVIEW_TOKEN_SALT,
            max_age=PREVIEW_TOKEN_MAX_AGE_SECONDS,
            purpose='preview',
        )
        csv_digest = _digest(csv_bytes)
        if (
            token.get('organization_id') != organization.pk
            or token.get('actor_id') != actor.pk
            or token.get('csv_digest') != csv_digest
        ):
            raise ImportTokenError('The commit does not match the validated workspace, actor, or CSV file.')

        # Serialize imports within one tenant before the final duplicate check.
        Organization.objects.select_for_update().get(pk=organization.pk)
        rows, issues, analysed_digest = self._analyse(
            organization=organization,
            csv_bytes=csv_bytes,
        )
        if analysed_digest != csv_digest or token.get('row_count') != len(rows):
            raise ImportTokenError('The CSV changed after validation.')
        if issues:
            raise ImportConflictError('The CSV no longer passes validation; run a new dry-run.')

        correlation_id = str(token.get('correlation_id') or '')
        if not correlation_id:
            raise ImportTokenError('The validation token has no correlation identifier.')

        self._append_batch_audit(
            organization=organization,
            actor=actor,
            event_type=EVENT_BATCH_STARTED,
            action=AuditLog.Action.CREATE,
            correlation_id=correlation_id,
            changes={
                'event': EVENT_BATCH_STARTED,
                'correlation_id': correlation_id,
                'csv_digest': csv_digest,
                'row_count': len(rows),
                'mode': 'create_only',
                'visibility': 'private_workspace',
            },
            request=request,
        )

        contracts: list[Contract] = []
        counterparties = {
            counterparty.pk: counterparty
            for counterparty in Counterparty.objects.filter(
                organization=organization,
                pk__in={row.counterparty_id for row in rows},
                is_active=True,
            )
        }
        contract_types = {
            contract_type.pk: contract_type
            for contract_type in ContractType.objects.filter(
                pk__in={row.contract_type_id for row in rows},
                is_active=True,
            )
        }
        owner_memberships = {
            membership.user_id: membership
            for membership in OrganizationMembership.objects.select_related('user').filter(
                organization=organization,
                user_id__in={row.owner_id for row in rows if row.owner_id is not None},
                is_active=True,
                user__is_active=True,
            )
        }
        for row in rows:
            counterparty = counterparties.get(row.counterparty_id)
            contract_type = contract_types.get(row.contract_type_id)
            owner_membership = (
                owner_memberships.get(row.owner_id)
                if row.owner_id is not None
                else None
            )
            if (
                counterparty is None
                or _normalize_text(counterparty.name) != _normalize_text(row.counterparty)
                or contract_type is None
                or contract_type.code != row.contract_type
                or (
                    row.owner_id is not None
                    and (
                        owner_membership is None
                        or _normalize_text(owner_membership.user.email)
                        != _normalize_text(row.owner_email)
                    )
                )
            ):
                raise ImportConflictError(
                    'A mapped owner, contract type, or counterparty changed; run a new dry-run.'
                )
            owner = owner_membership.user if owner_membership is not None else actor

            contract = Contract(
                organization=organization,
                title=row.title,
                counterparty=counterparty.name,
                owner=owner,
                created_by=actor,
                start_date=row.start_date,
                end_date=row.end_date,
                renewal_date=row.renewal_date,
                notice_period_days=row.notice_period_days,
                termination_notice_date=row.termination_notice_date,
            )
            assign_contract_type(contract, catalogue=contract_type)
            contract, created = persist_contract_with_imported_lifecycle(
                contract,
                desired_status=row.status,
                desired_lifecycle_stage=row.lifecycle_stage,
                actor=actor,
                reason='Repository CSV import',
                source='csv_import',
                request=request,
                provenance_correlation_id=correlation_id,
            )
            if not created:
                raise ImportConflictError('Create-only import refused to overwrite an existing contract.')
            contracts.append(contract)
            self._append_contract_audit(
                organization=organization,
                actor=actor,
                contract=contract,
                event_type=EVENT_ROW_CREATED,
                action=AuditLog.Action.CREATE,
                changes={
                    'event': EVENT_ROW_CREATED,
                    'correlation_id': correlation_id,
                    'row': row.row,
                    'contract_id': contract.pk,
                    'contract_type_id': contract_type.pk,
                    'counterparty_id': counterparty.pk,
                    'owner_id': owner.pk,
                    'mapped_fields': list(TEMPLATE_COLUMNS),
                    'visibility': 'private_workspace',
                },
                request=request,
            )

        self._append_batch_audit(
            organization=organization,
            actor=actor,
            event_type=EVENT_BATCH_COMPLETED,
            action=AuditLog.Action.CREATE,
            correlation_id=correlation_id,
            changes={
                'event': EVENT_BATCH_COMPLETED,
                'correlation_id': correlation_id,
                'csv_digest': csv_digest,
                'created_count': len(contracts),
                'contract_ids': [contract.pk for contract in contracts],
            },
            request=request,
        )
        rollback_token = signing.dumps(
            {
                'v': 1,
                'purpose': 'rollback',
                'organization_id': organization.pk,
                'actor_id': actor.pk,
                'correlation_id': correlation_id,
                'contract_count': len(contracts),
                'records_fingerprint': _records_fingerprint(contracts),
            },
            salt=ROLLBACK_TOKEN_SALT,
            compress=True,
        )
        return ImportCommitResult(
            correlation_id=correlation_id,
            contract_ids=tuple(contract.pk for contract in contracts),
            rollback_token=rollback_token,
        )

    @transaction.atomic
    def rollback(
        self,
        *,
        organization,
        actor,
        rollback_token: str,
        request=None,
    ) -> ImportRollbackResult:
        self._authorize(organization=organization, actor=actor)
        token = self._load_token(
            rollback_token,
            salt=ROLLBACK_TOKEN_SALT,
            max_age=ROLLBACK_TOKEN_MAX_AGE_SECONDS,
            purpose='rollback',
        )
        if (
            token.get('organization_id') != organization.pk
            or token.get('actor_id') != actor.pk
        ):
            raise ImportTokenError('The rollback token does not belong to this workspace.')

        Organization.objects.select_for_update().get(pk=organization.pk)
        correlation_id = str(token.get('correlation_id') or '')
        contracts = list(
            Contract.objects.select_for_update()
            .filter(
                organization=organization,
                origin_kind=Contract.OriginKind.IMPORT_CSV,
                provenance_correlation_id=correlation_id,
            )
            .order_by('pk')
        )
        if (
            not correlation_id
            or len(contracts) != token.get('contract_count')
            or _records_fingerprint(contracts) != token.get('records_fingerprint')
        ):
            raise ImportConflictError(
                'Rollback is unavailable because an imported record changed or the batch is incomplete.'
            )

        self._append_batch_audit(
            organization=organization,
            actor=actor,
            event_type=EVENT_ROLLBACK_STARTED,
            action=AuditLog.Action.UPDATE,
            correlation_id=correlation_id,
            changes={
                'event': EVENT_ROLLBACK_STARTED,
                'correlation_id': correlation_id,
                'contract_count': len(contracts),
                'strategy': 'archive_unchanged_records',
            },
            request=request,
        )

        archived: list[Contract] = []
        lifecycle = get_contract_lifecycle_service()
        for contract in contracts:
            contract = lifecycle.apply_operational_position(
                contract,
                status=Contract.Status.ARCHIVED,
                lifecycle_stage=Contract.LifecycleStage.OBLIGATION_TRACKING,
                actor=actor,
                system=True,
                reason=f'Compensating rollback for CSV import {correlation_id}',
                request=request,
                actor_type=AuditLog.ActorType.HUMAN,
            )
            archived.append(contract)
            self._append_contract_audit(
                organization=organization,
                actor=actor,
                contract=contract,
                event_type=EVENT_ROW_REVERSED,
                action=AuditLog.Action.UPDATE,
                changes={
                    'event': EVENT_ROW_REVERSED,
                    'correlation_id': correlation_id,
                    'contract_id': contract.pk,
                    'compensation': 'archived',
                },
                request=request,
            )

        self._append_batch_audit(
            organization=organization,
            actor=actor,
            event_type=EVENT_ROLLBACK_COMPLETED,
            action=AuditLog.Action.UPDATE,
            correlation_id=correlation_id,
            changes={
                'event': EVENT_ROLLBACK_COMPLETED,
                'correlation_id': correlation_id,
                'archived_count': len(archived),
                'contract_ids': [contract.pk for contract in archived],
            },
            request=request,
        )
        return ImportRollbackResult(
            correlation_id=correlation_id,
            archived_contract_ids=tuple(contract.pk for contract in archived),
        )

    def _analyse(
        self,
        *,
        organization,
        csv_bytes: bytes,
    ) -> tuple[tuple[PreparedRow, ...], tuple[ImportIssue, ...], str]:
        issues: list[ImportIssue] = []
        csv_digest = _digest(csv_bytes)
        if len(csv_bytes) > MAX_CSV_BYTES:
            issues.append(
                _issue(1, 'csv_file', 'file_too_large', 'CSV file must be 1 MiB or smaller.')
            )
            return (), _sorted_issues(issues), csv_digest
        if b'\x00' in csv_bytes:
            issues.append(_issue(1, 'csv_file', 'invalid_content', 'CSV file contains invalid data.'))
            return (), _sorted_issues(issues), csv_digest
        try:
            csv_text = csv_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            issues.append(_issue(1, 'csv_file', 'invalid_encoding', 'CSV file must be UTF-8 encoded.'))
            return (), _sorted_issues(issues), csv_digest

        try:
            reader = csv.DictReader(io.StringIO(csv_text), strict=True)
            headers = list(reader.fieldnames or [])
            raw_rows = list(reader)
        except csv.Error:
            issues.append(_issue(1, 'csv_file', 'malformed_csv', 'CSV file is malformed.'))
            return (), _sorted_issues(issues), csv_digest

        if not headers:
            issues.append(_issue(1, 'csv_file', 'missing_header', 'CSV header row is required.'))
            return (), _sorted_issues(issues), csv_digest
        duplicate_headers = sorted({header for header in headers if headers.count(header) > 1})
        for header in duplicate_headers:
            issues.append(
                _issue(1, header or 'csv_file', 'duplicate_column', f'Duplicate column "{header}" is not allowed.')
            )
        for column in REQUIRED_COLUMNS:
            if column not in headers:
                issues.append(
                    _issue(1, column, 'missing_column', f'Required column "{column}" is missing.')
                )
        for column in sorted(set(headers) - set(TEMPLATE_COLUMNS)):
            issues.append(
                _issue(1, column, 'unknown_column', f'Unknown column "{column}" is not allowed.')
            )
        if issues:
            return (), _sorted_issues(issues), csv_digest
        if not raw_rows:
            issues.append(_issue(1, 'csv_file', 'empty_csv', 'CSV file must contain at least one data row.'))
            return (), _sorted_issues(issues), csv_digest
        if len(raw_rows) > MAX_ROWS:
            issues.append(
                _issue(1, 'csv_file', 'too_many_rows', f'CSV file may contain at most {MAX_ROWS} rows.')
            )
            return (), _sorted_issues(issues), csv_digest

        counterparty_map: dict[str, list[Counterparty]] = {}
        for counterparty in Counterparty.objects.filter(
            organization=organization,
            is_active=True,
        ).order_by('pk'):
            counterparty_map.setdefault(_normalize_text(counterparty.name), []).append(counterparty)
        type_map = {
            contract_type.code: contract_type
            for contract_type in ContractType.objects.filter(is_active=True)
        }
        owner_map: dict[str, list[OrganizationMembership]] = {}
        for membership in OrganizationMembership.objects.select_related('user').filter(
            organization=organization,
            is_active=True,
            user__is_active=True,
        ).order_by('pk'):
            normalized_email = _normalize_text(membership.user.email)
            if normalized_email:
                owner_map.setdefault(normalized_email, []).append(membership)
        existing_keys = {
            (
                _normalize_text(title),
                contract_type,
                _normalize_text(counterparty),
                start_date,
                end_date,
            )
            for title, contract_type, counterparty, start_date, end_date in (
                Contract.objects.filter(organization=organization)
                .values_list('title', 'contract_type', 'counterparty', 'start_date', 'end_date')
            )
        }

        prepared: list[PreparedRow] = []
        seen_keys: dict[tuple, int] = {}
        for index, raw in enumerate(raw_rows, start=2):
            if raw.get(None):
                issues.append(
                    _issue(index, 'csv_file', 'extra_values', 'Row contains more values than the header.')
                )
            title = _clean_text(raw.get('title'))
            if not title:
                issues.append(_issue(index, 'title', 'required', 'title is required.'))
            elif len(title) > Contract._meta.get_field('title').max_length:
                issues.append(_issue(index, 'title', 'too_long', 'title must be 200 characters or fewer.'))

            raw_type = _clean_text(raw.get('contract_type'))
            contract_type_code = _canonical_type(raw_type)
            contract_type = type_map.get(contract_type_code) if contract_type_code else None
            if not raw_type:
                issues.append(_issue(index, 'contract_type', 'required', 'contract_type is required.'))
            elif contract_type_code is None:
                issues.append(
                    _issue(index, 'contract_type', 'invalid', f'contract_type "{raw_type}" is not supported.')
                )
            elif contract_type is None:
                issues.append(
                    _issue(index, 'contract_type', 'inactive', 'contract_type is not active in the catalogue.')
                )
            elif not is_contract_type_activated(contract_type_code):
                # The catalogue establishes a valid classification, not pilot
                # activation.  Recheck the same central allowlist used by all
                # intake routes so a separately exposed import surface cannot
                # create an inactive type.
                issues.append(
                    _issue(
                        index,
                        'contract_type',
                        'not_activated',
                        'contract_type is not enabled for controlled-pilot intake.',
                    )
                )

            raw_counterparty = _clean_text(raw.get('counterparty'))
            mapped_counterparties = counterparty_map.get(_normalize_text(raw_counterparty), [])
            counterparty = mapped_counterparties[0] if len(mapped_counterparties) == 1 else None
            if not raw_counterparty:
                issues.append(_issue(index, 'counterparty', 'required', 'counterparty is required.'))
            elif not mapped_counterparties:
                issues.append(
                    _issue(
                        index,
                        'counterparty',
                        'not_found',
                        'counterparty must exactly match one active counterparty in this workspace.',
                    )
                )
            elif len(mapped_counterparties) > 1:
                issues.append(
                    _issue(
                        index,
                        'counterparty',
                        'ambiguous',
                        'counterparty matches more than one active counterparty in this workspace.',
                    )
                )
            elif (
                len(mapped_counterparties[0].name)
                > Contract._meta.get_field('counterparty').max_length
            ):
                issues.append(
                    _issue(
                        index,
                        'counterparty',
                        'too_long',
                        'The mapped counterparty name is too long for a contract record.',
                    )
                )

            raw_owner_email = _clean_text(raw.get('owner_email'))
            mapped_owners = owner_map.get(_normalize_text(raw_owner_email), [])
            owner_membership = mapped_owners[0] if len(mapped_owners) == 1 else None
            if raw_owner_email and len(mapped_owners) != 1:
                issues.append(
                    _issue(
                        index,
                        'owner_email',
                        'invalid_mapping',
                        'owner_email must match exactly one active member in this workspace.',
                    )
                )

            raw_status = (raw.get('status') or '').strip().upper()
            status = _canonical_status(raw_status)
            raw_stage = (raw.get('lifecycle_stage') or '').strip().upper()
            lifecycle_stage = raw_stage or None
            if raw_status and raw_status not in _VALID_STATUSES:
                issues.append(
                    _issue(index, 'status', 'invalid', f'status "{raw_status}" is not supported.')
                )
            if raw_stage and raw_stage not in _VALID_STAGES:
                issues.append(
                    _issue(
                        index,
                        'lifecycle_stage',
                        'invalid',
                        f'lifecycle_stage "{raw_stage}" is not supported.',
                    )
                )
            resolved_status = status
            resolved_stage = raw_stage or Contract.LifecycleStage.DRAFTING
            if (not raw_status or raw_status in _VALID_STATUSES) and (
                not raw_stage or raw_stage in _VALID_STAGES
            ):
                try:
                    resolved_status, resolved_stage = resolve_import_status_stage(
                        status=status,
                        lifecycle_stage=lifecycle_stage,
                    )
                except ImportLifecycleError:
                    issues.append(
                        _issue(
                            index,
                            'lifecycle_stage',
                            'invalid_pair',
                            'status and lifecycle_stage are not a valid canonical combination.',
                        )
                    )

            start_date = _parse_date(
                raw.get('start_date') or '',
                row=index,
                field='start_date',
                issues=issues,
            )
            end_date = _parse_date(
                raw.get('end_date') or '',
                row=index,
                field='end_date',
                issues=issues,
            )
            renewal_date = _parse_date(
                raw.get('renewal_date') or '',
                row=index,
                field='renewal_date',
                issues=issues,
            )
            termination_notice_date = _parse_date(
                raw.get('termination_notice_date') or '',
                row=index,
                field='termination_notice_date',
                issues=issues,
            )
            notice_period_days = _parse_notice_period(
                raw.get('notice_period_days') or '',
                row=index,
                issues=issues,
            )
            if start_date and end_date and end_date < start_date:
                issues.append(
                    _issue(index, 'end_date', 'date_order', 'end_date must be on or after start_date.')
                )
            if start_date and renewal_date and renewal_date < start_date:
                issues.append(
                    _issue(
                        index,
                        'renewal_date',
                        'date_order',
                        'renewal_date must be on or after start_date.',
                    )
                )
            if (
                termination_notice_date
                and renewal_date
                and termination_notice_date > renewal_date
            ):
                issues.append(
                    _issue(
                        index,
                        'termination_notice_date',
                        'date_order',
                        'termination_notice_date must be on or before renewal_date.',
                    )
                )

            if (
                title
                and contract_type
                and counterparty
                and (not raw_owner_email or owner_membership is not None)
            ):
                row = PreparedRow(
                    row=index,
                    title=title,
                    contract_type=contract_type.code,
                    contract_type_id=contract_type.pk,
                    counterparty=counterparty.name,
                    counterparty_id=counterparty.pk,
                    owner_email=(
                        owner_membership.user.email
                        if owner_membership is not None
                        else ''
                    ),
                    owner_id=(
                        owner_membership.user_id
                        if owner_membership is not None
                        else None
                    ),
                    status=resolved_status,
                    lifecycle_stage=resolved_stage,
                    start_date=start_date,
                    end_date=end_date,
                    renewal_date=renewal_date,
                    notice_period_days=notice_period_days,
                    termination_notice_date=termination_notice_date,
                )
                prepared.append(row)
                if row.duplicate_key in existing_keys:
                    issues.append(
                        _issue(
                            index,
                            'title',
                            'duplicate_existing',
                            'An equivalent contract already exists in this workspace; no overwrite is allowed.',
                        )
                    )
                first_row = seen_keys.get(row.duplicate_key)
                if first_row is not None:
                    issues.append(
                        _issue(
                            index,
                            'title',
                            'duplicate_file',
                            f'Row duplicates row {first_row} in this CSV file.',
                        )
                    )
                else:
                    seen_keys[row.duplicate_key] = index

        return tuple(prepared), _sorted_issues(issues), csv_digest

    @staticmethod
    def _load_token(token: str, *, salt: str, max_age: int, purpose: str) -> dict:
        try:
            payload = signing.loads(token or '', salt=salt, max_age=max_age)
        except signing.BadSignature as exc:
            raise ImportTokenError('The import token is invalid or expired.') from exc
        if not isinstance(payload, dict) or payload.get('purpose') != purpose or payload.get('v') != 1:
            raise ImportTokenError('The import token is invalid or expired.')
        return payload

    @staticmethod
    def _request_id(request) -> str:
        return (getattr(request, 'request_id', '') or '')[:64] if request else ''

    def _append_batch_audit(
        self,
        *,
        organization,
        actor,
        event_type,
        action,
        correlation_id,
        changes,
        request,
    ) -> None:
        append_audit(
            organization=organization,
            user=actor,
            actor_type=AuditLog.ActorType.HUMAN,
            action=action,
            event_type=event_type,
            model_name='Contract',
            object_repr=f'CSV import batch {correlation_id}',
            changes=changes,
            request_id=self._request_id(request),
        )

    def _append_contract_audit(
        self,
        *,
        organization,
        actor,
        contract,
        event_type,
        action,
        changes,
        request,
    ) -> None:
        append_audit(
            organization=organization,
            user=actor,
            actor_type=AuditLog.ActorType.HUMAN,
            action=action,
            event_type=event_type,
            model_name='Contract',
            object_id=contract.pk,
            object_repr=str(contract),
            changes=changes,
            request_id=self._request_id(request),
        )


def get_repository_csv_import_service() -> RepositoryCsvImportService:
    return RepositoryCsvImportService()
