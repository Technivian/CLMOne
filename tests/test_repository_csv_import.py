from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from contracts.models import (
    AuditLog,
    AuditWriteError,
    Contract,
    ContractType,
    Counterparty,
    Document,
    Organization,
    OrganizationMembership,
)
from contracts.services.contract_type_catalogue import ensure_catalogue_row
from contracts.services.repository_csv_import import (
    EVENT_BATCH_COMPLETED,
    EVENT_BATCH_STARTED,
    EVENT_ROLLBACK_COMPLETED,
    EVENT_ROLLBACK_STARTED,
    EVENT_ROW_CREATED,
    EVENT_ROW_REVERSED,
    ImportConflictError,
    ImportTokenError,
    RepositoryCsvImportService,
    TEMPLATE_COLUMNS,
)


User = get_user_model()
FIXTURE_PATH = (
    Path(__file__).parent
    / 'fixtures'
    / 'repository_essentials'
    / 'payrollminds_synthetic_import.csv'
)


def csv_bytes(*rows):
    header = ','.join(TEMPLATE_COLUMNS)
    return (header + '\n' + '\n'.join(rows) + '\n').encode('utf-8')


def valid_row(
    *,
    title='Synthetic Services Agreement',
    contract_type='MSA',
    counterparty='Synthetic Payroll Services B.V.',
    status='ACTIVE',
    lifecycle_stage='OBLIGATION_TRACKING',
    start_date='2026-01-01',
    end_date='2027-01-01',
    renewal_date='2027-01-01',
    notice_period_days='90',
    termination_notice_date='2026-10-03',
):
    return ','.join(
        (
            title,
            contract_type,
            counterparty,
            status,
            lifecycle_stage,
            start_date,
            end_date,
            renewal_date,
            notice_period_days,
            termination_notice_date,
        )
    )


class RepositoryCsvImportFixtureMixin:
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Synthetic Payroll Workspace',
            slug='synthetic-payroll-workspace',
        )
        self.owner = User.objects.create_user(
            username='synthetic-import-owner',
            password='safe-test-password',
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.owner,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.counterparty = Counterparty.objects.create(
            organization=self.organization,
            name='Synthetic Payroll Services B.V.',
            is_active=True,
        )
        self.msa_type = ensure_catalogue_row('MSA')
        self.sow_type = ensure_catalogue_row('SOW')
        self.service = RepositoryCsvImportService()


class RepositoryCsvImportServiceTests(RepositoryCsvImportFixtureMixin, TestCase):
    def test_dry_run_is_zero_mutation_and_returns_signed_commit_token(self):
        before = {
            'contracts': Contract.objects.count(),
            'counterparties': Counterparty.objects.count(),
            'types': ContractType.objects.count(),
            'audit': AuditLog.objects.count(),
            'documents': Document.objects.count(),
        }

        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=csv_bytes(valid_row()),
        )

        self.assertTrue(preview.is_valid)
        self.assertTrue(preview.preview_token)
        self.assertEqual(preview.valid_count, 1)
        self.assertEqual(
            before,
            {
                'contracts': Contract.objects.count(),
                'counterparties': Counterparty.objects.count(),
                'types': ContractType.objects.count(),
                'audit': AuditLog.objects.count(),
                'documents': Document.objects.count(),
            },
        )

    def test_validation_errors_are_row_level_and_deterministic(self):
        payload = csv_bytes(
            valid_row(
                title='',
                contract_type='UNKNOWN',
                counterparty='Foreign Secret Counterparty',
                status='ACTIVE',
                lifecycle_stage='DRAFTING',
                start_date='not-a-date',
                end_date='2025-01-01',
                renewal_date='2024-01-01',
                notice_period_days='-1',
                termination_notice_date='2030-01-01',
            )
        )

        first = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )
        second = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )

        first_errors = [issue.as_dict() for issue in first.issues]
        self.assertEqual(first_errors, [issue.as_dict() for issue in second.issues])
        self.assertEqual(
            [(item['row'], item['field'], item['code']) for item in first_errors],
            [
                (2, 'title', 'required'),
                (2, 'contract_type', 'invalid'),
                (2, 'counterparty', 'not_found'),
                (2, 'lifecycle_stage', 'invalid_pair'),
                (2, 'start_date', 'invalid_date'),
                (2, 'notice_period_days', 'out_of_range'),
                (2, 'termination_notice_date', 'date_order'),
            ],
        )
        self.assertFalse(first.preview_token)

    def test_duplicate_detection_is_create_only_for_file_and_workspace(self):
        existing = Contract(
            organization=self.organization,
            title='Existing Agreement',
            counterparty=self.counterparty.name,
            owner=self.owner,
            created_by=self.owner,
            start_date=date_from_iso('2026-01-01'),
            end_date=date_from_iso('2027-01-01'),
        )
        from contracts.services.contract_type_catalogue import assign_contract_type
        from contracts.services.contract_import_lifecycle import persist_contract_with_imported_lifecycle

        assign_contract_type(existing, catalogue=self.msa_type)
        persist_contract_with_imported_lifecycle(
            existing,
            desired_status=Contract.Status.ACTIVE,
            desired_lifecycle_stage=Contract.LifecycleStage.OBLIGATION_TRACKING,
            actor=self.owner,
            source='csv_import',
            provenance_correlation_id='existing-fixture',
        )
        duplicate_row = valid_row(title='Existing Agreement')
        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=csv_bytes(duplicate_row, duplicate_row),
        )

        self.assertEqual(
            [(issue.row, issue.code) for issue in preview.issues],
            [
                (2, 'duplicate_existing'),
                (3, 'duplicate_existing'),
                (3, 'duplicate_file'),
            ],
        )
        self.assertEqual(Contract.objects.filter(title='Existing Agreement').count(), 1)

    def test_other_workspace_records_and_counterparties_are_never_mapped_or_disclosed(self):
        other = Organization.objects.create(name='Foreign Workspace', slug='foreign-workspace')
        Counterparty.objects.create(
            organization=other,
            name='Foreign Secret Counterparty',
            is_active=True,
        )
        foreign_contract = Contract.objects.create(
            organization=other,
            title='Foreign Secret Agreement',
            counterparty='Foreign Secret Counterparty',
            created_by=None,
        )
        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=csv_bytes(
                valid_row(
                    title=foreign_contract.title,
                    counterparty='Foreign Secret Counterparty',
                )
            ),
        )

        self.assertEqual([(issue.field, issue.code) for issue in preview.issues], [('counterparty', 'not_found')])
        self.assertNotIn('Foreign Workspace', preview.issues[0].message)
        self.assertNotIn(str(foreign_contract.pk), preview.issues[0].message)

    def test_commit_requires_exact_preview_bytes_and_maps_canonical_fields(self):
        payload = csv_bytes(valid_row())
        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )
        with self.assertRaises(ImportTokenError):
            self.service.commit(
                organization=self.organization,
                actor=self.owner,
                csv_bytes=csv_bytes(valid_row(title='Changed after preview')),
                preview_token=preview.preview_token,
            )
        self.assertEqual(Contract.objects.count(), 0)

        result = self.service.commit(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
            preview_token=preview.preview_token,
        )
        contract = Contract.objects.get(pk=result.contract_ids[0])
        self.assertEqual(contract.contract_type_catalogue, self.msa_type)
        self.assertEqual(contract.contract_type, 'MSA')
        self.assertEqual(contract.counterparty, self.counterparty.name)
        self.assertEqual(contract.owner, self.owner)
        self.assertEqual(contract.start_date.isoformat(), '2026-01-01')
        self.assertEqual(contract.end_date.isoformat(), '2027-01-01')
        self.assertEqual(contract.renewal_date.isoformat(), '2027-01-01')
        self.assertEqual(contract.notice_period_days, 90)
        self.assertEqual(contract.termination_notice_date.isoformat(), '2026-10-03')
        self.assertEqual(contract.status, Contract.Status.ACTIVE)
        self.assertEqual(contract.lifecycle_stage, Contract.LifecycleStage.OBLIGATION_TRACKING)
        self.assertEqual(contract.origin_kind, Contract.OriginKind.IMPORT_CSV)
        self.assertEqual(contract.origin_channel, 'csv_import')
        self.assertEqual(contract.provenance_correlation_id, result.correlation_id)
        self.assertIsNotNone(contract.provenance_locked_at)
        self.assertEqual(Document.objects.filter(contract=contract).count(), 0)

    def test_repeat_submission_is_detected_and_never_overwrites(self):
        payload = csv_bytes(valid_row())
        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )
        first = self.service.commit(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
            preview_token=preview.preview_token,
        )
        second_preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )

        self.assertEqual([issue.code for issue in second_preview.issues], ['duplicate_existing'])
        self.assertFalse(second_preview.preview_token)
        self.assertEqual(Contract.objects.filter(pk__in=first.contract_ids).count(), 1)

    def test_commit_writes_append_only_correlation_evidence(self):
        payload = csv_bytes(valid_row())
        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )
        result = self.service.commit(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
            preview_token=preview.preview_token,
        )

        events = list(
            AuditLog.objects.filter(
                organization=self.organization,
                event_type__in=[EVENT_BATCH_STARTED, EVENT_ROW_CREATED, EVENT_BATCH_COMPLETED],
            ).order_by('seq')
        )
        self.assertEqual([event.event_type for event in events], [
            EVENT_BATCH_STARTED,
            EVENT_ROW_CREATED,
            EVENT_BATCH_COMPLETED,
        ])
        self.assertTrue(all(event.model_name == 'Contract' for event in events))
        self.assertTrue(all(event.entry_hash for event in events))
        self.assertTrue(all(event.changes['correlation_id'] == result.correlation_id for event in events))
        with self.assertRaises(AuditWriteError):
            AuditLog.objects.filter(pk=events[0].pk).update(outcome=AuditLog.Outcome.FAILURE)

    def test_compensating_rollback_archives_unchanged_records_and_keeps_evidence(self):
        payload = csv_bytes(valid_row())
        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )
        committed = self.service.commit(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
            preview_token=preview.preview_token,
        )
        rolled_back = self.service.rollback(
            organization=self.organization,
            actor=self.owner,
            rollback_token=committed.rollback_token,
        )

        contract = Contract.objects.get(pk=committed.contract_ids[0])
        self.assertEqual(rolled_back.archived_contract_ids, committed.contract_ids)
        self.assertEqual(contract.status, Contract.Status.ARCHIVED)
        self.assertEqual(contract.lifecycle_stage, Contract.LifecycleStage.OBLIGATION_TRACKING)
        self.assertEqual(contract.provenance_correlation_id, committed.correlation_id)
        self.assertEqual(Document.objects.filter(contract=contract).count(), 0)
        self.assertEqual(
            list(
                AuditLog.objects.filter(
                    organization=self.organization,
                    event_type__in=[
                        EVENT_ROLLBACK_STARTED,
                        EVENT_ROW_REVERSED,
                        EVENT_ROLLBACK_COMPLETED,
                    ],
                )
                .order_by('seq')
                .values_list('event_type', flat=True)
            ),
            [EVENT_ROLLBACK_STARTED, EVENT_ROW_REVERSED, EVENT_ROLLBACK_COMPLETED],
        )

    def test_rollback_refuses_every_record_when_one_was_independently_changed(self):
        payload = csv_bytes(
            valid_row(title='Synthetic Agreement One'),
            valid_row(
                title='Synthetic Agreement Two',
                contract_type='SOW',
                status='IN_PROGRESS',
                lifecycle_stage='DRAFTING',
                end_date='2026-09-01',
                renewal_date='',
                termination_notice_date='',
            ),
        )
        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )
        committed = self.service.commit(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
            preview_token=preview.preview_token,
        )
        changed = Contract.objects.get(pk=committed.contract_ids[0])
        changed.title = 'Independently corrected title'
        changed.save(update_fields=['title', 'updated_at'])

        with self.assertRaises(ImportConflictError):
            self.service.rollback(
                organization=self.organization,
                actor=self.owner,
                rollback_token=committed.rollback_token,
            )
        self.assertFalse(
            Contract.objects.filter(
                pk__in=committed.contract_ids,
                status=Contract.Status.ARCHIVED,
            ).exists()
        )

    def test_preview_and_tokens_cannot_cross_workspace_or_actor_boundaries(self):
        other = Organization.objects.create(name='Other Synthetic Workspace', slug='other-synthetic')
        OrganizationMembership.objects.create(
            organization=other,
            user=self.owner,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        Counterparty.objects.create(
            organization=other,
            name=self.counterparty.name,
            is_active=True,
        )
        payload = csv_bytes(valid_row())
        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )
        with self.assertRaises(ImportTokenError):
            self.service.commit(
                organization=other,
                actor=self.owner,
                csv_bytes=payload,
                preview_token=preview.preview_token,
            )
        self.assertEqual(Contract.objects.count(), 0)

        member = User.objects.create_user(username='workspace-member')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=member,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        with self.assertRaises(PermissionDenied):
            self.service.preview(
                organization=self.organization,
                actor=member,
                csv_bytes=payload,
            )

        second_admin = User.objects.create_user(username='second-workspace-admin')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=second_admin,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )
        committed = self.service.commit(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
            preview_token=preview.preview_token,
        )
        with self.assertRaises(ImportTokenError):
            self.service.rollback(
                organization=self.organization,
                actor=second_admin,
                rollback_token=committed.rollback_token,
            )
        self.assertFalse(
            Contract.objects.filter(
                pk__in=committed.contract_ids,
                status=Contract.Status.ARCHIVED,
            ).exists()
        )

    def test_synthetic_fixture_commit_and_compensating_reset(self):
        payload = FIXTURE_PATH.read_bytes()
        preview = self.service.preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
        )
        self.assertTrue(preview.is_valid, [issue.as_dict() for issue in preview.issues])
        committed = self.service.commit(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=payload,
            preview_token=preview.preview_token,
        )
        self.assertEqual(len(committed.contract_ids), 2)
        self.assertEqual(Document.objects.filter(contract_id__in=committed.contract_ids).count(), 0)

        reset = self.service.rollback(
            organization=self.organization,
            actor=self.owner,
            rollback_token=committed.rollback_token,
        )
        self.assertEqual(reset.archived_contract_ids, committed.contract_ids)
        self.assertEqual(
            Contract.objects.filter(
                pk__in=committed.contract_ids,
                status=Contract.Status.ARCHIVED,
            ).count(),
            2,
        )


@override_settings(REPOSITORY_CSV_IMPORT_ENABLED=True)
class RepositoryCsvImportViewTests(RepositoryCsvImportFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.force_login(self.owner)

    def test_template_is_downloadable_and_contains_only_csv_mapping_columns(self):
        response = self.client.get(reverse('contracts:repository_csv_import_template'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertEqual(
            response.content.decode('utf-8').splitlines()[0],
            ','.join(TEMPLATE_COLUMNS),
        )
        self.assertNotIn('document', response.content.decode('utf-8').lower())

    def test_member_is_forbidden_and_default_off_route_is_not_exposed(self):
        member = User.objects.create_user(username='synthetic-member')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=member,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        member_client = Client()
        member_client.force_login(member)
        self.assertEqual(
            member_client.get(reverse('contracts:repository_csv_import')).status_code,
            403,
        )

        with override_settings(REPOSITORY_CSV_IMPORT_ENABLED=False):
            self.assertEqual(
                self.client.get(reverse('contracts:repository_csv_import')).status_code,
                404,
            )
            self.assertEqual(
                self.client.get(reverse('contracts:repository_csv_import_template')).status_code,
                404,
            )

    def test_view_requires_dry_run_then_exact_commit_and_supports_flag_off_rollback(self):
        payload = csv_bytes(valid_row())
        dry_run = self.client.post(
            reverse('contracts:repository_csv_import'),
            data={
                'action': 'dry_run',
                'csv_file': SimpleUploadedFile('contracts.csv', payload, content_type='text/csv'),
            },
        )
        self.assertEqual(dry_run.status_code, 200)
        preview = dry_run.context['preview']
        self.assertTrue(preview.is_valid)
        self.assertEqual(Contract.objects.count(), 0)

        commit = self.client.post(
            reverse('contracts:repository_csv_import'),
            data={
                'action': 'commit',
                'preview_token': preview.preview_token,
                'csv_file': SimpleUploadedFile('contracts.csv', payload, content_type='text/csv'),
            },
        )
        self.assertEqual(commit.status_code, 200)
        result = commit.context['commit_result']
        self.assertEqual(len(result.contract_ids), 1)

        with override_settings(REPOSITORY_CSV_IMPORT_ENABLED=False):
            rollback = self.client.post(
                reverse('contracts:repository_csv_import_rollback'),
                data={'rollback_token': result.rollback_token},
            )
        self.assertEqual(rollback.status_code, 200)
        self.assertEqual(rollback.context['rollback_result'].archived_contract_ids, result.contract_ids)


def date_from_iso(value):
    from datetime import date

    return date.fromisoformat(value)
