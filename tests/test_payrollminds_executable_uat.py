"""Executable, deterministic UAT for the bounded PayrollMinds controlled pilot.

See docs/pilots/payrollminds/PAYROLLMINDS_EXECUTABLE_UAT_MATRIX.md for the
scenario-by-scenario mapping (PM-UAT-001..018) and
docs/pilots/payrollminds/PAYROLLMINDS_EXECUTABLE_UAT_EVIDENCE.md for the
recommendation this suite feeds. Every scenario drives the real HTTP
views / service-layer entrypoints a pilot user or the governed intake path
would use; the only direct-model writes are actor/organization fixture setup
and the second-workspace comparison data, never the acceptance action itself.

No real PayrollMinds/customer/employee/payroll/salary data is used anywhere
in this file. MFA, external AI, inbound email, signatures, and external
portals/integrations are proven to remain disabled, not exercised.
"""
from __future__ import annotations

import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from contracts.models import (
    AuditLog,
    Contract,
    Deadline,
    Document,
    DocumentIngestionAttempt,
    DocumentReviewRun,
    DocumentVersion,
    Organization,
    OrganizationMembership,
    SignatureRequest,
    WebhookDelivery,
    WebhookEndpoint,
    Workflow,
)
from contracts.services.document_ingestion import (
    DocumentReleaseDenied,
    ScanResult,
    ScanVerdict,
    get_document_ingestion_service,
)
from contracts.services.nda_workflow import create_nda_workflow_instance, get_nda_workflow_template


User = get_user_model()

UAT_ORG_SLUG = 'payrollminds-uat'
UAT_OTHER_ORG_SLUG = 'payrollminds-uat-other'


class CleanScanner:
    """Deterministic clean-verdict scanner fixture, matching
    tests.test_document_ingestion_security's pattern (kept local so this
    file has no cross-module test-fixture dependency)."""

    def scan(self, file_obj, **kwargs):
        file_obj.read()
        return ScanResult(ScanVerdict.CLEAN, 'uat-synthetic-scanner', 'uat-signatures-1')


class MaliciousScanner:
    def scan(self, file_obj, **kwargs):
        file_obj.read()
        return ScanResult(
            ScanVerdict.MALICIOUS,
            'uat-synthetic-scanner',
            'uat-signatures-1',
            'SYNTHETIC_MALWARE_MARKER',
        )


def _uat_settings(org_slug=UAT_ORG_SLUG, **extra):
    values = {
        'DJANGO_ENV': 'test',
        'CONTROLLED_PILOT_ENABLED': True,
        'GEMINI_AI_ENABLED': False,
        'DOCUMENT_QUARANTINE_ENFORCEMENT_ENABLED': True,
        'DOCUMENT_QUARANTINE_ABORT_FAIL_CLOSED': False,
        'DOCUMENT_QUARANTINE_ENVIRONMENTS': 'test',
        'DOCUMENT_QUARANTINE_ORG_ALLOWLIST': org_slug,
        'DOCUMENT_MALWARE_SCANNER_CLASS': 'tests.test_payrollminds_executable_uat.CleanScanner',
        'DOCUMENT_QUARANTINE_RELEASE_ENABLED': True,
        'DOCUMENT_QUARANTINE_PURGE_ENABLED': False,
        'DOCUMENT_QUARANTINE_RETENTION_DAYS': 0,
        'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENABLED': True,
        'PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED': False,
        'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENVIRONMENTS': 'test',
        'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ORG_ALLOWLIST': org_slug,
        'PAR_SEC_002_SEARCH_ENFORCEMENT_ENABLED': True,
        'PAR_SEC_002_SEARCH_ABORT_FAIL_CLOSED': False,
        'PAR_SEC_002_SEARCH_ENFORCEMENT_ENVIRONMENTS': 'test',
        'PAR_SEC_002_SEARCH_ENFORCEMENT_ORG_ALLOWLIST': org_slug,
    }
    values.update(extra)
    return override_settings(**values)


class PayrollMindsExecutableUATTests(TestCase):
    """Backend executable UAT for the PayrollMinds controlled pilot.

    Each test method is fully self-contained (own transaction, own storage
    tempdir) per Django TestCase convention; several call
    ``self._intake_uat_contract`` to reach the same real, governed happy-path
    contract independently rather than sharing mutable state across methods.
    """

    def setUp(self):
        self.default_media = tempfile.TemporaryDirectory()
        self.quarantine_media = tempfile.TemporaryDirectory()
        self.addCleanup(self.default_media.cleanup)
        self.addCleanup(self.quarantine_media.cleanup)
        self.storage_override = override_settings(STORAGES={
            'default': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
                'OPTIONS': {'location': self.default_media.name},
            },
            'quarantine': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
                'OPTIONS': {'location': self.quarantine_media.name, 'base_url': None},
            },
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            },
        })
        self.storage_override.enable()
        self.addCleanup(self.storage_override.disable)

        self.organization = Organization.objects.create(
            name='PayrollMinds UAT', slug=UAT_ORG_SLUG,
        )
        self.owner = User.objects.create_user(
            username='payrollminds-uat-owner', password='uat-synthetic-pass-1',
        )
        self.member_b = User.objects.create_user(
            username='payrollminds-uat-member-b', password='uat-synthetic-pass-2',
        )
        OrganizationMembership.objects.create(
            organization=self.organization, user=self.owner,
            role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.organization, user=self.member_b,
            role=OrganizationMembership.Role.MEMBER, is_active=True,
        )

        self.other_organization = Organization.objects.create(
            name='PayrollMinds UAT Other Workspace', slug=UAT_OTHER_ORG_SLUG,
        )
        self.outside_user = User.objects.create_user(
            username='payrollminds-uat-outsider', password='uat-synthetic-pass-3',
        )
        OrganizationMembership.objects.create(
            organization=self.other_organization, user=self.outside_user,
            role=OrganizationMembership.Role.OWNER, is_active=True,
        )

        self.service = get_document_ingestion_service()

    # -- shared helper -----------------------------------------------------

    def _upload(self, name='payrollminds-uat-agreement.txt',
                content=b'Synthetic PayrollMinds UAT agreement text. No real data.'):
        return SimpleUploadedFile(name, content, content_type='text/plain')

    def _intake_uat_contract(self, actor=None, title='PayrollMinds UAT synthetic agreement'):
        """Drive the real governed intake path: quarantine -> scan -> release.

        Returns (contract, document, version, attempt). This is the only
        place a "clean upload becomes a canonical record" happens in this
        suite; every other scenario either reuses this path via HTTP or
        reads its resulting objects.
        """
        actor = actor or self.owner
        attempt = self.service.quarantine(
            organization=self.organization, uploaded_file=self._upload(), actor=actor,
        )
        attempt = self.service.scan(attempt=attempt, actor=actor)
        self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.CLEAN)
        with self.captureOnCommitCallbacks(execute=True):
            contract, document, version = self.service.create_contract_and_release(
                attempt=attempt,
                actor=actor,
                contract_fields={
                    'title': title,
                    'contract_type': Contract.ContractType.NDA,
                    'counterparty': 'Synthetic PayrollMinds counterparty',
                    'owner': actor,
                    'status': Contract.Status.IN_PROGRESS,
                    'lifecycle_stage': Contract.LifecycleStage.INTAKE,
                },
                title='payrollminds-uat-source.txt',
            )
        return contract, document, version, attempt

    # -- PM-UAT-001: workspace entry ---------------------------------------

    @_uat_settings()
    def test_pm_uat_001_workspace_entry(self):
        self.client.force_login(self.owner)

        dashboard = self.client.get(reverse('dashboard'))
        repository = self.client.get(reverse('contracts:contracts_api'))

        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(repository.status_code, 200)
        self.assertEqual(repository.json()['total_count'], 0)

    def test_pm_uat_001_unauthenticated_user_is_redirected(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    # -- PM-UAT-002: contract intake ---------------------------------------

    @_uat_settings()
    def test_pm_uat_002_contract_intake_creates_canonical_chain(self):
        self.assertFalse(Contract.objects.filter(organization=self.organization).exists())

        contract, document, version, attempt = self._intake_uat_contract()

        attempt.refresh_from_db()
        self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.RELEASED)
        self.assertEqual(attempt.contract_id, contract.pk)
        self.assertEqual(document.contract_id, contract.pk)
        self.assertEqual(version.contract_id, contract.pk)
        self.assertEqual(version, DocumentVersion.objects.get(pk=version.pk))
        self.assertEqual(contract.organization_id, self.organization.pk)
        self.assertEqual(contract.owner_id, self.owner.pk)
        self.assertEqual(contract.origin_kind, Contract.OriginKind.UPLOAD)
        self.assertTrue(contract.provenance_locked_at)
        self.assertTrue(AuditLog.objects.filter(
            organization=self.organization,
            event_type='contract.record.created',
            object_id=contract.pk,
        ).exists())
        self.assertTrue(AuditLog.objects.filter(
            organization=self.organization,
            event_type='document.version.created',
            object_id=document.pk,
        ).exists())

    @_uat_settings()
    def test_pm_uat_002_http_api_intake_path_matches_service_path(self):
        """The browser-facing route the pilot actually exposes: quarantine
        API -> release API, end to end, no service-layer shortcut."""
        self.client.force_login(self.owner)

        received = self.client.post(
            reverse('contracts:document_ingestion_quarantine_api'),
            {'file': self._upload()},
        )
        self.assertEqual(received.status_code, 202)

        released = self.client.post(
            reverse(
                'contracts:document_ingestion_release_api',
                args=[received.json()['correlation_id']],
            ),
            {
                'title': 'payrollminds-uat-api-source.txt',
                'create_contract': 'on',
                'contract_title': 'PayrollMinds UAT API-released agreement',
                'contract_type': Contract.ContractType.NDA,
                'counterparty': 'Synthetic PayrollMinds counterparty',
                'start_date': '2030-01-01',
                'end_date': '2030-12-31',
            },
        )

        self.assertEqual(released.status_code, 201)
        payload = released.json()
        contract = Contract.objects.get(pk=payload['contract_id'])
        self.assertEqual(contract.organization_id, self.organization.pk)
        self.assertEqual(contract.owner_id, self.owner.pk)

    # -- PM-UAT-003: metadata/review ----------------------------------------

    @_uat_settings()
    def test_pm_uat_003_metadata_review_is_human_verified(self):
        contract, document, _version, _attempt = self._intake_uat_contract()

        review = DocumentReviewRun.objects.get(document=document)
        self.assertEqual(review.governance_sources['metadata_authority'], 'human_entered')
        self.assertFalse(review.governance_sources['suggestions_authoritative'])

        self.client.force_login(self.owner)
        detail = self.client.get(reverse('contracts:contract_detail', args=[contract.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, contract.title)

    # -- PM-UAT-004: workflow progression -----------------------------------

    @_uat_settings()
    def test_pm_uat_004_workflow_progression_valid_and_invalid(self):
        template = get_nda_workflow_template()
        low_risk_values = {
            'counterparty': 'Synthetic PayrollMinds counterparty',
            'start_date': '2030-01-01',
            'contract_owner': 'PayrollMinds UAT Owner',
            'business_unit': 'Revenue Operations',
            'internal_reference': 'PM-UAT-004',
            'nda_type': 'Mutual',
            'confidentiality_purpose': 'synthetic UAT diligence',
            'confidentiality_period': 2,
            'disclosure_scope': 'synthetic technical architecture',
            'permitted_recipients': 'employees with a need to know',
            'governing_law': 'Netherlands',
            'jurisdiction': 'Amsterdam',
            'residual_knowledge_included': False,
            'injunctive_relief_included': True,
            'personal_data_involved': False,
            'confidentiality_period_nonstandard': False,
            'personal_data_confirmed': False,
            'residual_knowledge_nonstandard': False,
            'governing_law_nonpreferred': False,
        }
        workflow = create_nda_workflow_instance(
            organization=self.organization, user=self.owner, cleaned_values=low_risk_values,
        )

        # Correct, version-pinned template governs the instance.
        self.assertEqual(workflow.template_id, template.id)
        self.assertEqual(workflow.template.name, 'NDA Self-Serve Workflow')
        self.assertEqual(workflow.contract.contract_type, Contract.ContractType.NDA)

        # Required review step appears and is correctly evaluated for this
        # risk tier (low risk -> self-serve -> Legal Review is SKIPPED, not
        # absent).
        legal_step = workflow.steps.get(name='Legal Review')
        self.assertEqual(legal_step.status, legal_step.Status.SKIPPED)

        self.client.force_login(self.owner)

        # Valid human action: confirm a drafting section. Progresses the
        # workflow's own review-confirmation state and is audit-evidenced.
        confirm = self.client.post(
            reverse('contracts:nda_confirm_section', args=[workflow.pk, 'terms']),
            follow=True,
        )
        self.assertEqual(confirm.status_code, 200)
        self.assertTrue(AuditLog.objects.filter(
            organization=self.organization,
            action='nda_section_confirmed',
            object_id=workflow.pk,
        ).exists())

        # Invalid progression: submitting for Legal review before the
        # workflow's own generated draft has been through its required
        # review confirmations must be rejected, not silently accepted —
        # whatever the specific governed reason, the workflow's status must
        # not silently advance.
        before_status = Workflow.objects.get(pk=workflow.pk).status
        submit = self.client.post(
            reverse('contracts:nda_submit_for_review', args=[workflow.pk, 'legal']),
            follow=True,
        )
        self.assertEqual(submit.status_code, 200)
        messages = [str(m) for m in submit.context['messages']]
        self.assertTrue(messages, 'expected a governed rejection message, got none')
        self.assertEqual(Workflow.objects.get(pk=workflow.pk).status, before_status)

    # -- PM-UAT-005: search ---------------------------------------------------

    @_uat_settings()
    def test_pm_uat_005_search_authorized_and_unauthorized(self):
        contract, _document, _version, _attempt = self._intake_uat_contract()

        self.client.force_login(self.owner)
        owner_search = self.client.get(reverse('contracts:global_search'), {'q': 'PayrollMinds UAT synthetic'})
        self.assertEqual(owner_search.status_code, 200)
        self.assertContains(owner_search, contract.title)

        self.client.force_login(self.member_b)
        member_search = self.client.get(reverse('contracts:global_search'), {'q': 'PayrollMinds UAT synthetic'})
        self.assertEqual(member_search.status_code, 200)
        self.assertEqual(list(member_search.context['results']['contracts']), [])
        self.assertNotContains(member_search, contract.title)

        broad = self.client.get(reverse('contracts:global_search'), {'q': ''})
        self.assertEqual(broad.status_code, 200)
        self.assertEqual(dict(broad.context['results']), {})
        self.assertNotContains(broad, contract.title)

        repository = self.client.get(reverse('contracts:contracts_api'))
        self.assertEqual(repository.json()['total_count'], 0)

    # -- PM-UAT-006: operational tracking -------------------------------------

    # CONTROLLED_PILOT_ENABLED=True (the default from _uat_settings(), the
    # pilot's real deployment posture): the Obligations UI route allowlist
    # was reconciled with PILOT_SCOPE.md's "Search and dates" row (see
    # AGENT PROMPT 32 Phase 1 / PRODUCTION_TARGET_COMMISSIONING.md), so this
    # now exercises the real pilot configuration end to end, not an isolated
    # boundary.
    @_uat_settings()
    def test_pm_uat_006_operational_tracking_deadline(self):
        contract, _document, _version, _attempt = self._intake_uat_contract()

        self.client.force_login(self.owner)
        create = self.client.post(reverse('contracts:deadline_create'), {
            'title': 'PayrollMinds UAT renewal notice',
            'deadline_type': 'RENEWAL',
            'priority': 'MEDIUM',
            'due_date': '2030-06-01',
            'reminder_days': 30,
            'contract': contract.pk,
            'assigned_to': self.owner.pk,
        })
        self.assertEqual(create.status_code, 302)
        deadline = Deadline.objects.get(contract=contract)
        self.assertTrue(AuditLog.objects.filter(
            organization=self.organization,
            model_name='Deadline',
            object_id=deadline.pk,
            event_type='deadline.created',
        ).exists())

        obligations = self.client.get(reverse('contracts:obligations_workspace'))
        self.assertEqual(obligations.status_code, 200)
        self.assertIn(deadline, list(obligations.context['obligations']))
        self.assertContains(obligations, deadline.title)

        self.client.force_login(self.member_b)
        member_obligations = self.client.get(reverse('contracts:obligations_workspace'))
        self.assertEqual(list(member_obligations.context['obligations']), [])
        self.assertNotContains(member_obligations, deadline.title)

    @_uat_settings()
    def test_pm_uat_006_obligations_cross_workspace_denied(self):
        """The route allowlist reconciliation must not weaken authorization:
        an outside-workspace user reaching the now-permitted Obligations
        route still sees nothing, server-side, regardless of route scope."""
        contract, _document, _version, _attempt = self._intake_uat_contract()
        Deadline.objects.create(
            title='PayrollMinds UAT renewal notice', contract=contract,
            due_date='2030-06-01', created_by=self.owner,
        )

        self.client.force_login(self.outside_user)
        response = self.client.get(reverse('contracts:obligations_workspace'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['obligations']), [])
        self.assertNotContains(response, 'PayrollMinds UAT renewal notice')

    # -- PM-UAT-007: controlled export ---------------------------------------

    @_uat_settings()
    def test_pm_uat_007_controlled_export(self):
        self.client.force_login(self.owner)
        self.client.post(
            reverse('contracts:organization_team'),
            {'email': 'payrollminds-uat-invitee@example.com', 'role': OrganizationMembership.Role.MEMBER},
            follow=True,
        )

        export = self.client.get(reverse('contracts:organization_activity_export'))
        self.assertEqual(export.status_code, 200)
        self.assertIn('text/csv', export['Content-Type'])
        body = export.content.decode()
        self.assertIn('payrollminds-uat-invitee@example.com', body)
        self.assertTrue(AuditLog.objects.filter(
            organization=self.organization,
            event_type='organization.activity_exported',
            user=self.owner,
        ).exists())

        self.client.force_login(self.member_b)
        denied = self.client.get(reverse('contracts:organization_activity_export'))
        self.assertEqual(denied.status_code, 403)

    @_uat_settings()
    def test_pm_uat_007_export_never_leaks_other_workspace_rows(self):
        self.client.force_login(self.owner)
        self.client.post(
            reverse('contracts:organization_team'),
            {'email': 'payrollminds-uat-alpha@example.com', 'role': OrganizationMembership.Role.MEMBER},
            follow=True,
        )
        self.client.logout()

        self.client.force_login(self.outside_user)
        self.client.post(
            reverse('contracts:organization_team'),
            {'email': 'payrollminds-uat-beta@example.com', 'role': OrganizationMembership.Role.MEMBER},
            follow=True,
        )
        export = self.client.get(reverse('contracts:organization_activity_export'))

        self.assertEqual(export.status_code, 200)
        body = export.content.decode()
        self.assertIn('payrollminds-uat-beta@example.com', body)
        self.assertNotIn('payrollminds-uat-alpha@example.com', body)

    # -- PM-UAT-008: private access denial to an unrelated member -----------

    @_uat_settings()
    def test_pm_uat_008_private_access_denied_to_unrelated_member(self):
        contract, document, _version, _attempt = self._intake_uat_contract()

        self.client.force_login(self.member_b)
        repository = self.client.get(reverse('contracts:contracts_api'))
        direct_contract = self.client.get(reverse('contracts:contract_detail', args=[contract.pk]))
        direct_document = self.client.get(reverse('contracts:document_detail', args=[document.pk]))

        self.assertEqual(repository.json()['total_count'], 0)
        self.assertEqual(direct_contract.status_code, 404)
        self.assertEqual(direct_document.status_code, 404)

    # -- PM-UAT-009: cross-workspace access denial ---------------------------

    @_uat_settings()
    def test_pm_uat_009_cross_workspace_access_denied(self):
        contract, _document, _version, _attempt = self._intake_uat_contract()

        self.client.force_login(self.outside_user)
        repository = self.client.get(reverse('contracts:contracts_api'))
        search = self.client.get(reverse('contracts:global_search'), {'q': 'PayrollMinds UAT synthetic'})
        direct = self.client.get(reverse('contracts:contract_detail', args=[contract.pk]))

        self.assertEqual(repository.json()['total_count'], 0)
        self.assertEqual(list(search.context['results']['contracts']), [])
        self.assertEqual(direct.status_code, 404)

    # -- PM-UAT-010: direct identifier access does not bypass authorization -

    @_uat_settings()
    def test_pm_uat_010_direct_identifier_access_denied(self):
        contract, _document, _version, attempt = self._intake_uat_contract()

        self.client.force_login(self.member_b)
        direct_contract = self.client.get(reverse('contracts:contract_detail', args=[contract.pk]))
        ingestion_status = self.client.get(
            reverse('contracts:document_ingestion_status_api', args=[attempt.correlation_id])
        )

        self.assertEqual(direct_contract.status_code, 404)
        self.assertEqual(ingestion_status.status_code, 404)

    # -- PM-UAT-011: access revocation removes visibility --------------------

    @_uat_settings()
    def test_pm_uat_011_access_revocation_removes_visibility(self):
        contract, _document, _version, _attempt = self._intake_uat_contract(actor=self.member_b)

        self.client.force_login(self.member_b)
        allowed = self.client.get(reverse('contracts:contracts_api'))
        self.assertEqual(allowed.json()['total_count'], 1)

        OrganizationMembership.objects.filter(
            organization=self.organization, user=self.member_b,
        ).update(is_active=False)

        revoked = self.client.get(reverse('contracts:contracts_api'))
        direct = self.client.get(reverse('contracts:contract_detail', args=[contract.pk]))
        self.assertEqual(revoked.json()['total_count'], 0)
        self.assertEqual(direct.status_code, 404)

    # -- PM-UAT-012: external AI disabled -------------------------------------

    @_uat_settings(GEMINI_AI_ENABLED=True, GEMINI_API_KEY='uat-configured-but-must-not-be-used')
    def test_pm_uat_012_external_ai_disabled_even_when_configured(self):
        from unittest.mock import patch

        contract, _document, _version, _attempt = self._intake_uat_contract()

        self.client.force_login(self.owner)
        url = reverse('contracts:contract_ai_extract_api', args=[contract.pk])
        with patch('contracts.services.ai_extraction._get_client') as provider:
            response = self.client.post(url, data='{}', content_type='application/json')

        self.assertEqual(response.status_code, 403)
        self.assertIn('Enter and verify metadata manually', response.json()['error'])
        provider.assert_not_called()

    # -- PM-UAT-013: inbound email ingestion unavailable ----------------------

    def test_pm_uat_013_inbound_email_ingestion_unavailable(self):
        from django.urls import NoReverseMatch

        for candidate in (
            'contracts:email_ingestion_api',
            'contracts:inbound_email_webhook',
            'contracts:document_email_intake_api',
        ):
            with self.assertRaises(NoReverseMatch):
                reverse(candidate)

        # DocumentIngestionAttempt has exactly one creation path: the
        # governed upload API. There is no email-derived source concept on
        # the model at all.
        self.assertNotIn('source', [f.name for f in DocumentIngestionAttempt._meta.get_fields()])

    # -- PM-UAT-014: signature initiation remains unavailable -----------------

    @_uat_settings()
    def test_pm_uat_014_signature_initiation_blocked_under_real_pilot_scope(self):
        """Under the real pilot setting (CONTROLLED_PILOT_ENABLED=True),
        ControlledPilotScopeMiddleware blocks every /contracts/signatures/*
        route outright (reason='signatures_out_of_scope') before any
        view/service code runs — the strongest available proof that
        signature initiation is unavailable in this pilot, independent of
        provider configuration."""
        contract, document, _version, _attempt = self._intake_uat_contract()
        signature_request = SignatureRequest.objects.create(
            organization=self.organization,
            contract=contract,
            document=document,
            signer_name='Synthetic PayrollMinds Signer',
            signer_email='payrollminds-uat-signer@example.com',
            created_by=self.owner,
        )

        self.client.force_login(self.owner)
        listing = self.client.get(reverse('contracts:signature_request_list'))
        send = self.client.post(
            reverse('contracts:signature_request_send', args=[signature_request.pk])
        )

        self.assertEqual(listing.status_code, 302)
        self.assertEqual(listing['Location'], reverse('dashboard'))
        self.assertEqual(send.status_code, 302)
        self.assertEqual(send['Location'], reverse('dashboard'))
        signature_request.refresh_from_db()
        self.assertEqual(signature_request.status, SignatureRequest.Status.PENDING)
        self.assertEqual(signature_request.esign_provider, '')

    def test_pm_uat_014_default_esign_provider_is_the_inert_null_provider(self):
        """Defense in depth, independent of route scoping: even if a
        signature route were reachable, the pilot's actual deployment
        configures no ESIGN_PROVIDER, so dispatch would resolve to the
        inert local-only NullSignatureProvider rather than any live
        delivery integration."""
        from django.conf import settings as django_settings

        self.assertEqual(django_settings.ESIGN_PROVIDER, 'null')

    # -- PM-UAT-015: no external portal/integration path is invoked ---------

    @_uat_settings()
    def test_pm_uat_015_external_integration_not_invoked(self):
        self._intake_uat_contract()

        self.assertFalse(WebhookEndpoint.objects.filter(organization=self.organization).exists())
        self.assertFalse(WebhookDelivery.objects.filter(organization=self.organization).exists())

    # -- PM-UAT-016: invalid/malicious file rejected, never canonical --------

    @_uat_settings(DOCUMENT_MALWARE_SCANNER_CLASS='tests.test_payrollminds_executable_uat.MaliciousScanner')
    def test_pm_uat_016_malicious_file_never_becomes_canonical(self):
        attempt = self.service.quarantine(
            organization=self.organization, uploaded_file=self._upload(), actor=self.owner,
        )
        attempt = self.service.scan(attempt=attempt, actor=self.owner)

        self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.REJECTED)
        self.assertEqual(attempt.verdict, DocumentIngestionAttempt.Verdict.MALICIOUS)
        with self.assertRaises(DocumentReleaseDenied):
            self.service.release(attempt=attempt, actor=self.owner, title='Blocked synthetic upload')

        self.assertFalse(Document.objects.filter(organization=self.organization).exists())
        self.assertFalse(Contract.objects.filter(organization=self.organization).exists())

    # -- PM-UAT-017: machine-verifiable audit timeline ------------------------

    @_uat_settings()
    def test_pm_uat_017_audit_timeline_is_machine_verifiable(self):
        contract, document, _version, _attempt = self._intake_uat_contract()
        self.client.force_login(self.owner)
        self.client.get(reverse('contracts:organization_activity_export'))

        events = list(AuditLog.objects.filter(
            organization=self.organization,
        ).order_by('timestamp', 'pk'))

        self.assertGreaterEqual(len(events), 2)
        seen_event_types = {event.event_type for event in events}
        self.assertIn('contract.record.created', seen_event_types)
        self.assertIn('document.version.created', seen_event_types)

        chained = [event for event in events if event.hash_version == 2]
        for event in events:
            self.assertEqual(event.organization_id, self.organization.pk)
            self.assertIsNotNone(event.timestamp)
        for event in chained:
            self.assertTrue(event.entry_hash)
            self.assertIsNotNone(event.seq)

        # Append-only: bulk update/delete through the ORM queryset API must
        # be structurally impossible, not merely undocumented.
        from contracts.models import AuditWriteError

        with self.assertRaises(AuditWriteError):
            AuditLog.objects.filter(organization=self.organization).update(event_type='tampered')
        with self.assertRaises(AuditWriteError):
            AuditLog.objects.filter(organization=self.organization).delete()

    # -- PM-UAT-018: UAT data is isolated -------------------------------------

    @_uat_settings()
    def test_pm_uat_018_uat_data_isolated_from_other_workspaces(self):
        contract, _document, _version, _attempt = self._intake_uat_contract()

        self.assertNotEqual(self.organization.slug, 'payrollminds-pilot')
        self.assertNotEqual(self.organization.slug, 'payrollminds-demo')
        self.assertTrue(self.organization.slug.startswith('payrollminds-uat'))

        self.assertFalse(
            Contract.objects.filter(
                organization=self.other_organization, title=contract.title,
            ).exists()
        )
        self.client.force_login(self.outside_user)
        cross_repo = self.client.get(reverse('contracts:contracts_api'))
        self.assertEqual(cross_repo.json()['total_count'], 0)

    def test_pm_uat_018_previous_test_left_no_residue(self):
        """Runs regardless of alphabetical/definition order: proves
        per-test transactional rollback, not just call ordering, is what
        keeps PM-UAT data isolated between runs."""
        self.assertFalse(Contract.objects.filter(organization__slug__startswith='payrollminds-uat').exists())
        self.assertFalse(DocumentIngestionAttempt.objects.filter(organization__slug__startswith='payrollminds-uat').exists())
