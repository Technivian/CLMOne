"""Tests for the DPA Review Pack module.

Covers: model creation, the heuristic dpa_review analyzer detecting planted
issues in realistic DPA text (role qualification, payroll data categories,
subprocessor authorization conflicts, international transfer risk, vague
security language, unrealistic breach notification deadlines, chargeable
DSAR assistance, unbounded audit rights, statutory-retention deletion
conflicts, and DPA liability overriding the MSA cap), risk item
persistence via the analysis endpoint, human-only approval routing (the
analyzer must never set approval_status to APPROVED), audit logging,
cross-tenant isolation, the playbook reference list, and copy quality.
"""
import json
import re

from django.contrib.auth.models import User
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from contracts.models import (
    AuditLog,
    Contract,
    DPAPlaybookPosition,
    DPAReviewPack,
    DPARiskItem,
    Organization,
    OrganizationMembership,
)
from contracts.services.dpa_review import run_dpa_analysis

ISO_TIMESTAMP_RE = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}')

RISKY_DPA_TEXT = """DATA PROCESSING AGREEMENT

Client is the Controller of Personal Data processed under this DPA.
Payrollminds is the Processor and shall process Personal Data only on
Client's documented instructions.

Categories of Personal Data include employee name, salary and wage data,
tax ID and income tax withholding data, national insurance number and
social security data, bank account and IBAN details, pension and
retirement benefit enrollment data, sick leave and annual leave records,
employment contract terms, national identification number, payroll
correction history, and payslip data.

Payrollminds may engage subprocessors under a general authorization
without case-by-case approval. Notwithstanding the foregoing, Client's
prior written approval is also required before any new subprocessor is
engaged.

Payrollminds uses a payroll calculation subprocessor located in the
United States for overflow processing capacity.

Payrollminds shall implement encryption of data at rest and regular
backup of payroll records.

Payrollminds shall notify Client within 4 hours of becoming aware of a
Personal Data Breach.

Payrollminds shall assist Client with data subject requests at
Payrollminds' reasonable costs where the request requires substantial
effort.

Client may conduct an on-site audit of Payrollminds' processing
facilities upon reasonable notice.

Upon termination, Payrollminds shall delete or return all Personal Data
within 30 days, except that payroll and tax records subject to statutory
retention requirements shall be retained for the applicable statutory
period.

Notwithstanding the limitation of liability in the Agreement,
Payrollminds' liability for any breach of this DPA shall be uncapped.
Payrollminds shall indemnify Client for losses arising from a Personal
Data Breach.
"""

CLEAN_DPA_TEXT = """DATA PROCESSING AGREEMENT

Client is the Controller of Personal Data. Payrollminds is the Processor
and shall process Personal Data only on Client's documented instructions.

Payrollminds may engage subprocessors under a general written
authorization, subject to 30 days' prior notice to Client.

Payrollminds shall implement encryption of data at rest, role-based
access control with least privilege, multi-factor authentication for all
administrative access, audit logging of all access, regular backup of
payroll records, a documented incident response plan, and logical data
segregation between client tenants.

Payrollminds shall notify Client without undue delay and in any event
within 72 hours after becoming aware of a Personal Data Breach.

Payrollminds shall provide reasonable assistance with data subject
requests at no additional fee.

Client may audit Payrollminds' compliance no more than once per year;
a current SOC 2 report shall satisfy this obligation.

Upon termination, Payrollminds shall delete all Personal Data within 90
days and provide a certificate of deletion.
"""


def _make_org_and_contract(text=RISKY_DPA_TEXT, org_slug='dpa-test-firm'):
    organization = Organization.objects.create(name=f'DPA Test Firm ({org_slug})', slug=org_slug)
    user = User.objects.create_user(username=f'{org_slug}-user', password='testpass123', email=f'{org_slug}@example.com')
    OrganizationMembership.objects.create(organization=organization, user=user, role=OrganizationMembership.Role.ADMIN, is_active=True)
    contract = Contract.objects.create(
        organization=organization, title='Payrollminds DPA', content=text,
        contract_type=Contract.ContractType.DPA, status='IN_REVIEW', created_by=user,
    )
    return organization, user, contract


class DPAReviewPackModelTests(TestCase):
    def test_review_pack_creation_defaults_to_draft_and_ambiguous(self):
        organization, user, contract = _make_org_and_contract()
        review_pack = DPAReviewPack.objects.create(organization=organization, contract=contract, created_by=user)
        self.assertEqual(review_pack.approval_status, DPAReviewPack.ApprovalStatus.DRAFT)
        self.assertEqual(review_pack.role_qualification, DPAReviewPack.RoleQualification.AMBIGUOUS)


class DPAAnalyzerDetectionTests(TestCase):
    """The heuristic scanner must actually detect what's in the text —
    not just render fields, but populate them correctly."""

    def setUp(self):
        self.organization, self.user, self.contract = _make_org_and_contract()
        self.review_pack = DPAReviewPack.objects.create(organization=self.organization, contract=self.contract, created_by=self.user)

    def test_detects_controller_processor_roles(self):
        run_dpa_analysis(self.review_pack)
        self.assertEqual(self.review_pack.role_qualification, DPAReviewPack.RoleQualification.CONTROLLER_PROCESSOR)

    def test_detects_all_planted_payroll_data_categories(self):
        run_dpa_analysis(self.review_pack)
        for field_name in (
            'has_salary_wage_data', 'has_tax_data', 'has_social_security_data', 'has_bank_account_data',
            'has_pension_benefits_data', 'has_absence_leave_data', 'has_employment_contract_data',
            'has_national_identifiers', 'has_payroll_corrections', 'has_payslip_data',
        ):
            self.assertTrue(getattr(self.review_pack, field_name), f'{field_name} should be detected')

    def test_detects_contradictory_subprocessor_authorization_model(self):
        run_dpa_analysis(self.review_pack)
        self.assertTrue(self.review_pack.subprocessor_prior_approval_required)
        self.assertTrue(self.review_pack.subprocessor_general_authorization_allowed)

    def test_detects_transfer_without_mechanism_as_critical(self):
        suggestions = run_dpa_analysis(self.review_pack)
        self.assertTrue(self.review_pack.transfers_outside_eea)
        self.assertFalse(self.review_pack.transfer_mechanism_present)
        critical_transfer = [s for s in suggestions if s.category == DPARiskItem.Category.TRANSFER and s.severity == DPARiskItem.Severity.CRITICAL]
        self.assertEqual(len(critical_transfer), 1)

    def test_detects_vague_security_measures(self):
        run_dpa_analysis(self.review_pack)
        self.assertFalse(self.review_pack.security_measures_specific)

    def test_specific_security_measures_do_not_flag_as_vague(self):
        organization, user, contract = _make_org_and_contract(text=CLEAN_DPA_TEXT, org_slug='dpa-clean-firm')
        review_pack = DPAReviewPack.objects.create(organization=organization, contract=contract, created_by=user)
        run_dpa_analysis(review_pack)
        self.assertTrue(review_pack.security_measures_specific)

    def test_detects_unrealistic_breach_notification_deadline(self):
        run_dpa_analysis(self.review_pack)
        self.assertEqual(self.review_pack.breach_notification_deadline_hours, 4)
        self.assertFalse(self.review_pack.breach_notification_realistic)

    def test_realistic_breach_deadline_not_flagged(self):
        organization, user, contract = _make_org_and_contract(text=CLEAN_DPA_TEXT, org_slug='dpa-clean-firm2')
        review_pack = DPAReviewPack.objects.create(organization=organization, contract=contract, created_by=user)
        run_dpa_analysis(review_pack)
        self.assertEqual(review_pack.breach_notification_deadline_hours, 72)
        self.assertTrue(review_pack.breach_notification_realistic)

    def test_detects_chargeable_dsar_assistance(self):
        run_dpa_analysis(self.review_pack)
        self.assertTrue(self.review_pack.dsar_assistance_chargeable)

    def test_detects_onsite_audit_and_unbounded_frequency(self):
        run_dpa_analysis(self.review_pack)
        self.assertTrue(self.review_pack.audit_rights_onsite_allowed)
        self.assertFalse(self.review_pack.audit_rights_frequency_limited)

    def test_detects_deletion_deadline_conflict_with_statutory_retention(self):
        run_dpa_analysis(self.review_pack)
        self.assertEqual(self.review_pack.deletion_return_deadline_days, 30)
        self.assertTrue(self.review_pack.deletion_legal_retention_conflict)

    def test_detects_uncapped_liability_and_msa_override(self):
        run_dpa_analysis(self.review_pack)
        self.assertTrue(self.review_pack.liability_uncapped)
        self.assertTrue(self.review_pack.liability_overrides_msa_cap)

    def test_analysis_never_touches_approval_status(self):
        """The analyzer must never approve a DPA — that is exclusively a
        human action via the approval-status endpoint."""
        self.review_pack.approval_status = DPAReviewPack.ApprovalStatus.UNDER_REVIEW
        self.review_pack.save()
        run_dpa_analysis(self.review_pack)
        self.assertEqual(self.review_pack.approval_status, DPAReviewPack.ApprovalStatus.UNDER_REVIEW)

    def test_clean_dpa_produces_far_fewer_suggestions_than_risky_one(self):
        organization, user, contract = _make_org_and_contract(text=CLEAN_DPA_TEXT, org_slug='dpa-clean-firm3')
        clean_pack = DPAReviewPack.objects.create(organization=organization, contract=contract, created_by=user)
        clean_suggestions = run_dpa_analysis(clean_pack)
        risky_suggestions = run_dpa_analysis(self.review_pack)
        self.assertLess(len(clean_suggestions), len(risky_suggestions))


class DPAReviewPackViewTests(TestCase):
    def setUp(self):
        self.organization, self.admin, self.contract = _make_org_and_contract()
        self.review_pack = DPAReviewPack.objects.create(organization=self.organization, contract=self.contract, created_by=self.admin)
        self.member = User.objects.create_user(username='dpa_member', password='testpass123', email='member@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.member, role=OrganizationMembership.Role.MEMBER, is_active=True)

    def test_list_view_renders_for_member(self):
        client = TestClient()
        client.login(username='dpa_member', password='testpass123')
        response = client.get(reverse('contracts:dpa_review_pack_list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_view_renders_for_member(self):
        client = TestClient()
        client.login(username='dpa_member', password='testpass123')
        response = client.get(reverse('contracts:dpa_review_pack_detail', kwargs={'pk': self.review_pack.pk}))
        self.assertEqual(response.status_code, 200)

    def test_run_analysis_persists_risk_items(self):
        client = TestClient()
        client.login(username=self.admin.username, password='testpass123')
        response = client.post(
            reverse('contracts:dpa_review_run_analysis', kwargs={'pk': self.review_pack.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(self.review_pack.risk_items.count(), 0)

    def test_rerunning_analysis_does_not_duplicate_open_auto_detected_items(self):
        client = TestClient()
        client.login(username=self.admin.username, password='testpass123')
        client.post(reverse('contracts:dpa_review_run_analysis', kwargs={'pk': self.review_pack.pk}), data=json.dumps({}), content_type='application/json')
        first_count = self.review_pack.risk_items.count()
        client.post(reverse('contracts:dpa_review_run_analysis', kwargs={'pk': self.review_pack.pk}), data=json.dumps({}), content_type='application/json')
        second_count = self.review_pack.risk_items.count()
        self.assertEqual(first_count, second_count)

    def test_rerunning_analysis_preserves_resolved_items(self):
        client = TestClient()
        client.login(username=self.admin.username, password='testpass123')
        client.post(reverse('contracts:dpa_review_run_analysis', kwargs={'pk': self.review_pack.pk}), data=json.dumps({}), content_type='application/json')
        risk = self.review_pack.risk_items.first()
        risk.status = DPARiskItem.Status.RESOLVED
        risk.save()
        client.post(reverse('contracts:dpa_review_run_analysis', kwargs={'pk': self.review_pack.pk}), data=json.dumps({}), content_type='application/json')
        risk.refresh_from_db()
        self.assertEqual(risk.status, DPARiskItem.Status.RESOLVED)

    def test_only_admin_can_set_approval_status(self):
        client = TestClient()
        client.login(username='dpa_member', password='testpass123')
        response = client.post(
            reverse('contracts:dpa_review_set_approval_status', kwargs={'pk': self.review_pack.pk}),
            data=json.dumps({'status': 'APPROVED'}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
        self.review_pack.refresh_from_db()
        self.assertEqual(self.review_pack.approval_status, DPAReviewPack.ApprovalStatus.DRAFT)

    def test_admin_can_set_approval_status_and_it_is_audit_logged(self):
        client = TestClient()
        client.login(username=self.admin.username, password='testpass123')
        response = client.post(
            reverse('contracts:dpa_review_set_approval_status', kwargs={'pk': self.review_pack.pk}),
            data=json.dumps({'status': 'APPROVED'}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.review_pack.refresh_from_db()
        self.assertEqual(self.review_pack.approval_status, DPAReviewPack.ApprovalStatus.APPROVED)
        self.assertEqual(self.review_pack.approved_by_id, self.admin.id)
        entry = AuditLog.objects.filter(model_name='DPAReviewPack', object_id=self.review_pack.pk).order_by('-timestamp').first()
        self.assertIsNotNone(entry)
        self.assertEqual((entry.changes or {}).get('event'), 'dpa_approval_status_changed')

    def test_invalid_approval_status_rejected(self):
        client = TestClient()
        client.login(username=self.admin.username, password='testpass123')
        response = client.post(
            reverse('contracts:dpa_review_set_approval_status', kwargs={'pk': self.review_pack.pk}),
            data=json.dumps({'status': 'NOT_A_REAL_STATUS'}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)


class DPACrossTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a, self.user_a, self.contract_a = _make_org_and_contract(org_slug='dpa-iso-a')
        self.org_b, self.user_b, _ = _make_org_and_contract(org_slug='dpa-iso-b')
        self.review_pack_a = DPAReviewPack.objects.create(organization=self.org_a, contract=self.contract_a, created_by=self.user_a)

    def test_other_org_member_does_not_see_review_pack(self):
        client = TestClient()
        client.login(username=self.user_b.username, password='testpass123')
        response = client.get(reverse('contracts:dpa_review_pack_list'))
        ids = [p.id for p in response.context['review_packs']]
        self.assertNotIn(self.review_pack_a.id, ids)

    def test_other_org_member_gets_404_on_detail(self):
        client = TestClient()
        client.login(username=self.user_b.username, password='testpass123')
        response = client.get(reverse('contracts:dpa_review_pack_detail', kwargs={'pk': self.review_pack_a.pk}))
        self.assertEqual(response.status_code, 404)

    def test_other_org_member_cannot_run_analysis(self):
        client = TestClient()
        client.login(username=self.user_b.username, password='testpass123')
        response = client.post(
            reverse('contracts:dpa_review_run_analysis', kwargs={'pk': self.review_pack_a.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_other_org_member_cannot_set_approval_status(self):
        client = TestClient()
        client.login(username=self.user_b.username, password='testpass123')
        response = client.post(
            reverse('contracts:dpa_review_set_approval_status', kwargs={'pk': self.review_pack_a.pk}),
            data=json.dumps({'status': 'APPROVED'}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)


class DPAPlaybookListViewTests(TestCase):
    def setUp(self):
        self.organization, self.user, _ = _make_org_and_contract(org_slug='dpa-playbook-firm')
        DPAPlaybookPosition.objects.get_or_create(
            organization=None, topic=DPAPlaybookPosition.Topic.LIABILITY,
            defaults={'our_position': 'Stay within the MSA cap.', 'owner': 'LEGAL'},
        )

    def test_playbook_list_renders_global_positions(self):
        client = TestClient()
        client.login(username=self.user.username, password='testpass123')
        response = client.get(reverse('contracts:dpa_playbook_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Stay within the MSA cap.', response.content.decode())

    def test_org_specific_position_overrides_global_default(self):
        DPAPlaybookPosition.objects.create(
            organization=self.organization, topic=DPAPlaybookPosition.Topic.LIABILITY,
            our_position='Org-specific override position.', owner='LEGAL',
        )
        client = TestClient()
        client.login(username=self.user.username, password='testpass123')
        response = client.get(reverse('contracts:dpa_playbook_list'))
        body = response.content.decode()
        self.assertIn('Org-specific override position.', body)
        self.assertNotIn('Stay within the MSA cap.', body)


class DPACopyQualityTests(TestCase):
    def setUp(self):
        self.organization, self.user, self.contract = _make_org_and_contract(org_slug='dpa-copy-firm')
        self.review_pack = DPAReviewPack.objects.create(organization=self.organization, contract=self.contract, created_by=self.user)
        run_dpa_analysis(self.review_pack)
        self.review_pack.save()

    def test_no_raw_internals_on_detail_page(self):
        client = TestClient()
        client.login(username=self.user.username, password='testpass123')
        response = client.get(reverse('contracts:dpa_review_pack_detail', kwargs={'pk': self.review_pack.pk}))
        body = response.content.decode()
        self.assertNotIn('DPAReviewPack', body)
        self.assertNotIn('DPO_SECURITY', body)
        self.assertIn('DPO/Security', body)
        self.assertIsNone(ISO_TIMESTAMP_RE.search(body), 'Found a raw ISO timestamp in the DPA review detail response')

    def test_approval_status_shows_human_label_not_raw_enum(self):
        client = TestClient()
        client.login(username=self.user.username, password='testpass123')
        response = client.get(reverse('contracts:dpa_review_pack_list'))
        body = response.content.decode()
        self.assertIn('Draft', body)
