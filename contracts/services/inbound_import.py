"""Inbound import service for integrations."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, timedelta

from contracts.models import Contract, OrganizationMembership
from contracts.services.contract_import_lifecycle import (
    ImportLifecycleError,
    persist_contract_with_imported_lifecycle,
)


@dataclass
class ImportResult:
    imported_count: int
    skipped_count: int
    errors: list[dict]
    dry_run: bool


class InboundImportService:
    CSV_FIELDS = frozenset({
        'title', 'counterparty', 'contract_type', 'status', 'lifecycle_stage',
        'owner_email', 'start_date', 'end_date', 'renewal_date',
        'notice_period_days', 'termination_notice_date',
    })
    REQUIRED_CSV_FIELDS = frozenset({'title'})
    VALID_STATUSES = {
        'IN_PROGRESS', 'ACTIVE', 'EXPIRED', 'TERMINATED', 'CANCELLED', 'ARCHIVED',
        # Legacy aliases accepted on import and mapped below
        'DRAFT', 'PENDING', 'IN_REVIEW', 'APPROVED', 'COMPLETED',
    }
    VALID_CONTRACT_TYPES = None  # deprecated — use contract_type_catalogue.validate_import_contract_type
    VALID_STAGES = {
        'INTAKE', 'DRAFTING', 'INTERNAL_REVIEW', 'NEGOTIATION', 'APPROVAL',
        'SIGNATURE', 'EXECUTED', 'OBLIGATION_TRACKING', 'RENEWAL',
    }

    def import_contracts_from_csv(self, org, csv_text: str, user, dry_run: bool = False) -> ImportResult:
        reader = csv.DictReader(io.StringIO(csv_text))
        header_errors = self._csv_header_errors(reader.fieldnames)
        if header_errors:
            return ImportResult(
                imported_count=0,
                skipped_count=0,
                errors=[{'row': 'file', 'message': message} for message in header_errors],
                dry_run=dry_run,
            )
        rows = list(reader)
        return self._process_rows(org, rows, user, dry_run)

    def import_contracts_from_json(self, org, data: list[dict], user, dry_run: bool = False) -> ImportResult:
        return self._process_rows(org, data, user, dry_run)

    def _process_rows(self, org, rows: list[dict], user, dry_run: bool) -> ImportResult:
        imported = 0
        skipped = 0
        errors: list[dict] = []
        existing_keys = {
            self._duplicate_key({'title': title, 'counterparty': counterparty})
            for title, counterparty in Contract.objects.filter(organization=org).values_list('title', 'counterparty')
        }
        seen_keys = set()

        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append({'row': i + 1, 'message': 'row must be an object'})
                skipped += 1
                continue
            row_errors = self.validate_import_row(row, organization=org)
            if row.get(None):
                row_errors.append('row contains more values than the CSV header')
            duplicate_key = self._duplicate_key(row)
            if duplicate_key in seen_keys:
                row_errors.append('potential duplicate: another CSV row has the same title and counterparty')
            elif duplicate_key in existing_keys:
                row_errors.append('potential duplicate: a contract with the same title and counterparty already exists in this workspace')
            if row_errors:
                errors.append({'row': i + 1, 'message': '; '.join(row_errors)})
                skipped += 1
                continue

            seen_keys.add(duplicate_key)

            if not dry_run:
                try:
                    raw_status = self._text(row, 'status').upper() or 'IN_PROGRESS'
                    raw_stage = self._text(row, 'lifecycle_stage').upper() or None
                    contract = Contract(
                        organization=org,
                        title=self._text(row, 'title'),
                        counterparty=self._text(row, 'counterparty'),
                        start_date=self._parse_date(row.get('start_date')),
                        end_date=self._parse_date(row.get('end_date')),
                        renewal_date=self._parse_date(row.get('renewal_date')),
                        notice_period_days=self._parse_notice_period_days(row.get('notice_period_days')),
                        termination_notice_date=self._termination_notice_date(row),
                        owner=self._active_workspace_owner(org, row.get('owner_email')),
                        created_by=user,
                    )
                    from contracts.services.contract_type_catalogue import assign_contract_type
                    assign_contract_type(
                        contract,
                        code=self._text(row, 'contract_type') or 'OTHER',
                    )
                    persist_contract_with_imported_lifecycle(
                        contract,
                        desired_status=raw_status,
                        desired_lifecycle_stage=raw_stage,
                        actor=user,
                        reason='inbound import',
                        source='inbound_import',
                    )
                    imported += 1
                except (ImportLifecycleError, Exception) as e:
                    errors.append({'row': i + 1, 'message': str(e)})
                    skipped += 1
            else:
                # Dry-run still rejects illegal status/stage pairs.
                try:
                    from contracts.services.contract_import_lifecycle import resolve_import_status_stage
                    raw_status = self._text(row, 'status').upper() or 'IN_PROGRESS'
                    raw_stage = self._text(row, 'lifecycle_stage').upper() or None
                    resolve_import_status_stage(status=raw_status, lifecycle_stage=raw_stage)
                    imported += 1
                except ImportLifecycleError as e:
                    errors.append({'row': i + 1, 'message': str(e)})
                    skipped += 1

        return ImportResult(
            imported_count=imported,
            skipped_count=skipped,
            errors=errors,
            dry_run=dry_run,
        )

    def validate_import_row(self, row: dict, *, organization=None) -> list[str]:
        errors: list[str] = []

        title = self._text(row, 'title')
        if not title:
            errors.append('title is required')

        status = self._text(row, 'status').upper()
        if status and status not in self.VALID_STATUSES:
            errors.append(f'invalid status "{status}"')

        stage = self._text(row, 'lifecycle_stage').upper()
        if stage and stage not in self.VALID_STAGES:
            errors.append(f'invalid lifecycle_stage "{stage}"')

        if status and stage:
            try:
                from contracts.services.contract_import_lifecycle import resolve_import_status_stage
                resolve_import_status_stage(status=status, lifecycle_stage=stage)
            except ImportLifecycleError as exc:
                errors.append(str(exc))

        contract_type = self._text(row, 'contract_type').upper()
        if contract_type:
            from contracts.services.contract_type_catalogue import validate_import_contract_type
            errors.extend(validate_import_contract_type(contract_type))

        parsed_dates = {}
        for date_field in ('start_date', 'end_date', 'renewal_date', 'termination_notice_date'):
            val = self._text(row, date_field)
            if val:
                try:
                    parsed_dates[date_field] = date.fromisoformat(val)
                except ValueError:
                    errors.append(f'{date_field} must be YYYY-MM-DD format')

        start_date = parsed_dates.get('start_date')
        end_date = parsed_dates.get('end_date')
        if start_date and end_date and end_date < start_date:
            errors.append('end_date must be on or after start_date')

        notice_period_days = self._parse_notice_period_days(row.get('notice_period_days'))
        raw_notice_period_days = self._text(row, 'notice_period_days')
        if raw_notice_period_days and notice_period_days is None:
            errors.append('notice_period_days must be a whole number of days')
        termination_notice_date = parsed_dates.get('termination_notice_date')
        if end_date and notice_period_days is not None and termination_notice_date:
            expected_notice_date = end_date - timedelta(days=notice_period_days)
            if termination_notice_date != expected_notice_date:
                errors.append('termination_notice_date must match end_date minus notice_period_days')

        owner_email = self._text(row, 'owner_email')
        if owner_email and organization and not self._active_workspace_owner(organization, owner_email):
            errors.append('owner_email must identify exactly one active member of this workspace')

        return errors

    @classmethod
    def _csv_header_errors(cls, fieldnames: list[str] | None) -> list[str]:
        normalized_headers = [field.strip() if field else '' for field in (fieldnames or [])]
        headers = {field for field in normalized_headers if field}
        errors = []
        duplicate_headers = sorted({
            field for field in headers if normalized_headers.count(field) > 1
        })
        missing = sorted(cls.REQUIRED_CSV_FIELDS - headers)
        unsupported = sorted(headers - cls.CSV_FIELDS)
        if not normalized_headers:
            errors.append('CSV header row is required')
        if '' in normalized_headers:
            errors.append('CSV column names must not be empty')
        if duplicate_headers:
            errors.append(f'duplicate column: {", ".join(duplicate_headers)}')
        if missing:
            errors.append(f'missing required column: {", ".join(missing)}')
        if unsupported:
            errors.append(f'unsupported column: {", ".join(unsupported)}')
        return errors

    @staticmethod
    def _parse_date(val: str | None) -> date | None:
        value = str(val).strip() if val is not None else ''
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_notice_period_days(val: str | None) -> int | None:
        value = str(val).strip() if val is not None else ''
        if not value or not value.isdecimal():
            return None
        return int(value)

    def _termination_notice_date(self, row: dict) -> date | None:
        explicit_date = self._parse_date(row.get('termination_notice_date'))
        if explicit_date:
            return explicit_date
        end_date = self._parse_date(row.get('end_date'))
        notice_period_days = self._parse_notice_period_days(row.get('notice_period_days'))
        if end_date and notice_period_days is not None:
            return end_date - timedelta(days=notice_period_days)
        return None

    @staticmethod
    def _active_workspace_owner(organization, owner_email: str | None):
        email = str(owner_email).strip() if owner_email is not None else ''
        if not email:
            return None
        memberships = list(
            OrganizationMembership.objects.filter(
                organization=organization,
                is_active=True,
                user__email__iexact=email,
            ).select_related('user')[:2]
        )
        return memberships[0].user if len(memberships) == 1 else None

    @staticmethod
    def _duplicate_key(row: dict) -> tuple[str, str]:
        return (
            InboundImportService._text(row, 'title').casefold(),
            InboundImportService._text(row, 'counterparty').casefold(),
        )

    @staticmethod
    def _text(row: dict, field: str) -> str:
        value = row.get(field)
        return str(value).strip() if value is not None else ''


def get_inbound_import_service() -> InboundImportService:
    return InboundImportService()
