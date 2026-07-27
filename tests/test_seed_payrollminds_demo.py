"""Regression coverage for the coherent Payrollminds buyer-demo workspace."""
import shutil
import tempfile
from unittest import mock
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from contracts.models import (
    ApprovalRequest,
    Contract,
    ContractVersion,
    Counterparty,
    Deadline,
    DocumentOCRReview,
    DPAReviewPack,
    DPARiskItem,
    Organization,
    OrgPolicy,
    SignatureRequest,
)

User = get_user_model()


class PayrollmindsDemoSeedTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp(prefix='clmone-payrollminds-demo-')
        cls.settings_override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)
        super().tearDownClass()

    def test_seed_is_idempotent_and_creates_a_complete_contract_story(self):
        call_command('seed_payrollminds_demo')
        call_command('seed_payrollminds_demo')

        organization = Organization.objects.get(slug='payrollminds-demo')
        self.assertEqual(organization.contracts.count(), 6)
        self.assertEqual(organization.documents.count(), 6)
        self.assertEqual(
            ContractVersion.objects.filter(contract__organization=organization).count(),
            5,
        )
        self.assertEqual(
            Deadline.objects.filter(contract__organization=organization).count(),
            5,
        )

        msa = organization.contracts.get(title='Payrollminds Master Services Agreement')
        sow = organization.contracts.get(
            title='Global Payroll Transformation Engagement — Implementation SOW',
        )
        self.assertEqual(
            sow.contract_type,
            Contract.ContractType.SOW,
        )
        self.assertEqual(sow.parent_contract, msa)
        self.assertEqual(msa.linked_contracts.count(), 1)
        self.assertEqual(msa.renewal_date, msa.end_date)
        self.assertEqual(msa.termination_notice_date, msa.end_date - timedelta(days=60))
        self.assertTrue(
            Deadline.objects.filter(
                contract=msa,
                title='MSA renewal and notice decision',
                due_date=msa.termination_notice_date,
            ).exists()
        )
        self.assertIn('NL · DE · BE · GB', sow.business_unit)
        self.assertTrue(sow.personal_data_processing)
        self.assertTrue(sow.counterparty_privacy_review_required)
        self.assertEqual(Counterparty.objects.filter(organization=organization).count(), 4)
        self.assertFalse(OrgPolicy.objects.get(organization=organization).ai_features_enabled)
        self.assertFalse(
            DocumentOCRReview.objects.filter(document__contract=sow).exists(),
            'The presenter-visible SOW must not expose extraction review while AI is disabled.',
        )

        msa_documents = list(msa.documents.order_by('version'))
        self.assertEqual([document.version for document in msa_documents], [1, 2])
        self.assertEqual(msa_documents[1].parent_document, msa_documents[0])
        self.assertEqual(msa_documents[1].status, msa_documents[1].Status.FINAL)
        with msa_documents[1].file.open('rb') as uploaded:
            self.assertEqual(uploaded.read(5), b'%PDF-')

        signature = SignatureRequest.objects.get(
            organization=organization,
            contract=msa,
        )
        self.assertEqual(signature.status, SignatureRequest.Status.SIGNED)
        self.assertEqual(signature.document, msa_documents[1])
        self.assertTrue(signature.external_id)
        prepared_signature = SignatureRequest.objects.get(organization=organization, contract=sow)
        self.assertEqual(prepared_signature.status, SignatureRequest.Status.PENDING)

        approvals = {
            approval.approval_step: approval
            for approval in ApprovalRequest.objects.filter(
                organization=organization,
                contract=sow,
            )
        }
        self.assertEqual(approvals['LEGAL'].status, ApprovalRequest.Status.APPROVED)
        self.assertEqual(
            approvals['FINANCE — value exceeds EUR 100,000'].status,
            ApprovalRequest.Status.PENDING,
        )
        self.assertEqual(approvals['PRIVACY'].assigned_to.username, 'payrollminds_privacy')
        self.assertNotEqual(
            approvals['FINANCE — value exceeds EUR 100,000'].assigned_to,
            sow.created_by,
        )

        dpa = organization.contracts.get(contract_type=Contract.ContractType.DPA)
        review_pack = DPAReviewPack.objects.get(contract=dpa)
        self.assertEqual(
            review_pack.approval_status,
            DPAReviewPack.ApprovalStatus.UNDER_REVIEW,
        )
        self.assertEqual(list(review_pack.related_contracts.all()), [msa])
        self.assertEqual(review_pack.documents.count(), 2)
        self.assertEqual(review_pack.risk_items.count(), 3)
        self.assertEqual(
            review_pack.risk_items.filter(
                severity=DPARiskItem.Severity.CRITICAL,
                is_cross_document_conflict=True,
            ).count(),
            1,
        )

        self.assertEqual(
            organization.audit_logs.filter(event_type='contract.demo_imported').count(),
            1,
        )
        self.assertEqual(
            organization.audit_logs.filter(event_type='dpa.review_opened').count(),
            1,
        )
        self.assertEqual(
            organization.audit_logs.filter(event_type='contract.conditional_approval_routed').count(),
            1,
        )

    def test_reset_rebuilds_only_the_synthetic_workspace(self):
        call_command('seed_payrollminds_demo')
        other_org = Organization.objects.create(name='Unrelated workspace', slug='unrelated-workspace')
        other_user = User.objects.create_user(username='unrelated-user', password='not-a-demo-password')
        Contract.objects.create(organization=other_org, title='Unrelated contract', created_by=other_user)

        call_command('seed_payrollminds_demo', '--reset')

        organization = Organization.objects.get(slug='payrollminds-demo')
        self.assertEqual(organization.contracts.count(), 6)
        self.assertTrue(Counterparty.objects.filter(organization=organization).exists())
        self.assertTrue(Contract.objects.filter(organization=other_org, title='Unrelated contract').exists())

    def test_refuses_to_seed_on_a_deployed_platform(self):
        with mock.patch(
            'contracts.management.commands.seed_payrollminds_demo.is_running_on_deployed_platform',
            return_value=True,
        ):
            with self.assertRaises(CommandError):
                call_command('seed_payrollminds_demo')
        self.assertFalse(Organization.objects.filter(slug='payrollminds-demo').exists())
