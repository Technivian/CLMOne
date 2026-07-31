"""Private document repository coverage for the PAR-SEC-002 policy boundary."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from contracts.models import (
    Client,
    Contract,
    Document,
    EthicalWall,
    Matter,
    Organization,
    OrganizationMembership,
)
from contracts.services.document_repository_policy import (
    apply_document_repository_policy,
)


User = get_user_model()

REPOSITORY_ENFORCEMENT = {
    'DJANGO_ENV': 'test',
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENABLED': True,
    'PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED': False,
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENVIRONMENTS': 'test',
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ORG_ALLOWLIST': 'private-documents',
}


class PrivateDocumentRepositoryTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Private Documents',
            slug='private-documents',
        )
        self.owner = User.objects.create_user(
            username='document-owner',
            password='testpass123',
        )
        self.member = User.objects.create_user(
            username='document-member',
            password='testpass123',
        )
        for user, role in (
            (self.owner, OrganizationMembership.Role.OWNER),
            (self.member, OrganizationMembership.Role.ADMIN),
        ):
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=user,
                role=role,
                is_active=True,
            )

        self.protected_client = Client.objects.create(
            organization=self.organization,
            name='Protected Client',
        )
        self.protected_matter = Matter.objects.create(
            organization=self.organization,
            client=self.protected_client,
            matter_number='DOC-001',
            title='Protected Matter',
        )
        self.protected_contract = Contract.objects.create(
            organization=self.organization,
            client=self.protected_client,
            title='Protected Agreement',
            created_by=self.owner,
        )
        self.visible_contract = Contract.objects.create(
            organization=self.organization,
            title='Visible Agreement',
            created_by=self.owner,
        )
        self.protected_document = Document.objects.create(
            organization=self.organization,
            contract=self.protected_contract,
            title='Protected document title',
            uploaded_by=self.owner,
        )
        self.direct_client_document = Document.objects.create(
            organization=self.organization,
            client=self.protected_client,
            title='Protected direct client document',
            uploaded_by=self.owner,
        )
        self.direct_matter_document = Document.objects.create(
            organization=self.organization,
            matter=self.protected_matter,
            title='Protected direct matter document',
            uploaded_by=self.owner,
        )
        self.visible_document = Document.objects.create(
            organization=self.organization,
            contract=self.visible_contract,
            title='Visible repository document',
            uploaded_by=self.owner,
        )
        self.wall = EthicalWall.objects.create(
            organization=self.organization,
            name='Document restriction',
            client=self.protected_client,
            created_by=self.owner,
        )
        self.wall.restricted_users.add(self.member)
        self.client.force_login(self.member)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_list_and_search_do_not_disclose_restricted_documents(self):
        response = self.client.get(
            reverse('contracts:document_list'),
            {'q': 'Protected'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['documents']), [])
        body = response.content.decode()
        self.assertNotIn(self.protected_document.title, body)
        self.assertNotIn(self.direct_client_document.title, body)
        self.assertNotIn(self.direct_matter_document.title, body)

        visible = self.client.get(reverse('contracts:document_list'))
        self.assertEqual(
            [document.pk for document in visible.context['documents']],
            [self.visible_document.pk],
        )

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_global_search_does_not_disclose_restricted_objects(self):
        response = self.client.get(
            reverse('contracts:global_search'),
            {'q': 'Protected'},
        )

        self.assertEqual(response.status_code, 200)
        for result_key in ('contracts', 'clients', 'matters', 'documents'):
            self.assertEqual(list(response.context['results'][result_key]), [])
        body = response.content.decode()
        self.assertNotIn(self.protected_contract.title, body)
        self.assertNotIn(self.protected_client.name, body)
        self.assertNotIn(self.protected_matter.title, body)
        self.assertNotIn(self.protected_document.title, body)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_visible_version_does_not_disclose_restricted_parent_metadata(self):
        visible_version = Document.objects.create(
            organization=self.organization,
            contract=self.visible_contract,
            parent_document=self.protected_document,
            title='Visible derived version',
            uploaded_by=self.owner,
        )

        response = self.client.get(
            reverse('contracts:document_detail', args=[visible_version.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['version_chain']), [])
        self.assertNotContains(response, self.protected_document.title)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_soft_deleted_document_is_absent_from_global_search(self):
        self.visible_document.is_deleted = True
        self.visible_document.save(update_fields=['is_deleted'])

        response = self.client.get(
            reverse('contracts:global_search'),
            {'q': 'Visible repository'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['results']['documents']), [])
        self.assertNotContains(response, self.visible_document.title)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_denied_document_routes_return_generic_not_found(self):
        routes = (
            reverse('contracts:document_detail', args=[self.protected_document.pk]),
            reverse('contracts:document_update', args=[self.protected_document.pk]),
            reverse('contracts:document_delete', args=[self.protected_document.pk]),
            reverse('contracts:document_download', args=[self.protected_document.pk]),
            reverse(
                'contracts:document_compare',
                args=[self.visible_document.pk, self.protected_document.pk],
            ),
        )

        for url in routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn(
                    self.protected_document.title,
                    response.content.decode(),
                )

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_create_form_hides_restricted_relation_metadata_and_sharing(self):
        response = self.client.get(reverse('contracts:document_create'))

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertNotIn(
            self.protected_contract.pk,
            set(form.fields['contract'].queryset.values_list('pk', flat=True)),
        )
        self.assertNotIn(
            self.protected_client.pk,
            set(form.fields['client'].queryset.values_list('pk', flat=True)),
        )
        self.assertNotIn(
            self.protected_matter.pk,
            set(form.fields['matter'].queryset.values_list('pk', flat=True)),
        )
        self.assertNotIn('share_with_counterparty', form.fields)
        self.assertNotContains(response, 'Share with counterparty collaborators')

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_internal_upload_is_private_even_with_forged_share_field(self):
        response = self.client.post(
            reverse('contracts:document_create'),
            {
                'title': 'Private upload',
                'document_type': Document.DocType.CONTRACT,
                'status': Document.Status.DRAFT,
                'contract': self.visible_contract.pk,
                'share_with_counterparty': 'on',
                'file': SimpleUploadedFile(
                    'private-upload.txt',
                    b'synthetic contract content',
                    content_type='text/plain',
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        document = Document.objects.get(title='Private upload')
        self.assertFalse(document.share_with_counterparty)
        self.assertEqual(document.organization, self.organization)
        self.assertEqual(document.contract, self.visible_contract)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_restricted_relationship_forgery_is_rejected_without_mutation(self):
        before = Document.objects.count()
        response = self.client.post(
            reverse('contracts:document_create'),
            {
                'title': 'Forged upload',
                'document_type': Document.DocType.CONTRACT,
                'status': Document.Status.DRAFT,
                'contract': self.protected_contract.pk,
                'file': SimpleUploadedFile(
                    'forged.txt',
                    b'synthetic contract content',
                    content_type='text/plain',
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('contract', response.context['form'].errors)
        self.assertEqual(Document.objects.count(), before)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_upload_api_rejects_restricted_relationships_before_mutation(self):
        document_count = Document.objects.count()
        contract_count = Contract.objects.count()

        contract_response = self.client.post(
            reverse('contracts:document_upload_api'),
            {
                'contract_id': self.protected_contract.pk,
                'file': SimpleUploadedFile(
                    'restricted-contract.txt',
                    b'synthetic restricted contract upload',
                    content_type='text/plain',
                ),
            },
        )
        matter_response = self.client.post(
            reverse('contracts:document_upload_api'),
            {
                'create_contract': 'on',
                'matter_id': self.protected_matter.pk,
                'title': 'Restricted matter contract',
                'file': SimpleUploadedFile(
                    'restricted-matter.txt',
                    b'synthetic restricted matter upload',
                    content_type='text/plain',
                ),
            },
        )

        self.assertEqual(contract_response.status_code, 404)
        self.assertEqual(matter_response.status_code, 404)
        self.assertEqual(Document.objects.count(), document_count)
        self.assertEqual(Contract.objects.count(), contract_count)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_internal_form_rejects_unsupported_file_before_storage(self):
        before = Document.objects.count()
        response = self.client.post(
            reverse('contracts:document_create'),
            {
                'title': 'Unsupported upload',
                'document_type': Document.DocType.CONTRACT,
                'status': Document.Status.DRAFT,
                'contract': self.visible_contract.pk,
                'file': SimpleUploadedFile(
                    'payload.exe',
                    b'not an executable; synthetic validation fixture',
                    content_type='application/octet-stream',
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('file', response.context['form'].errors)
        self.assertContains(response, 'is not supported')
        self.assertEqual(Document.objects.count(), before)

    def test_flag_off_preserves_existing_workspace_scoped_document_path(self):
        response = self.client.get(reverse('contracts:document_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(document.pk for document in response.context['documents']),
            {
                self.protected_document.pk,
                self.direct_client_document.pk,
                self.direct_matter_document.pk,
                self.visible_document.pk,
            },
        )

    @patch(
        'contracts.views_domains.client_matter_document.can_access_contract_action',
        return_value=False,
    )
    def test_flag_off_preserves_linked_contract_download_permission_response(
        self,
        _mock_can_access,
    ):
        response = self.client.get(
            reverse('contracts:document_download', args=[self.visible_document.pk])
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    @patch(
        'contracts.views_domains.client_matter_document.can_access_contract_action',
        return_value=False,
    )
    def test_enforced_download_permission_denial_is_non_disclosing(
        self,
        _mock_can_access,
    ):
        response = self.client.get(
            reverse('contracts:document_download', args=[self.visible_document.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, self.visible_document.title, status_code=404)

    @override_settings(EXTERNAL_COLLABORATION_ENABLED=True)
    def test_explicit_sharing_control_requires_separate_external_gate(self):
        form_response = self.client.get(reverse('contracts:document_create'))
        self.assertIn('share_with_counterparty', form_response.context['form'].fields)

        create_response = self.client.post(
            reverse('contracts:document_create'),
            {
                'title': 'Legacy explicit share',
                'document_type': Document.DocType.CONTRACT,
                'status': Document.Status.DRAFT,
                'contract': self.visible_contract.pk,
                'share_with_counterparty': 'on',
                'file': SimpleUploadedFile(
                    'legacy-share.txt',
                    b'synthetic legacy sharing fixture',
                    content_type='text/plain',
                ),
            },
        )

        self.assertEqual(create_response.status_code, 302)
        self.assertTrue(
            Document.objects.get(title='Legacy explicit share').share_with_counterparty
        )

    @override_settings(
        **{
            **REPOSITORY_ENFORCEMENT,
            'PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED': True,
        }
    )
    def test_abort_switch_returns_no_rows_or_object_metadata(self):
        listing = self.client.get(reverse('contracts:document_list'))
        detail = self.client.get(
            reverse('contracts:document_detail', args=[self.visible_document.pk])
        )

        self.assertEqual(list(listing.context['documents']), [])
        self.assertNotContains(listing, self.visible_document.title)
        self.assertEqual(detail.status_code, 404)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_malformed_active_wall_fails_closed(self):
        EthicalWall.objects.create(
            organization=self.organization,
            name='Malformed wall',
            created_by=self.owner,
        )

        listing = self.client.get(reverse('contracts:document_list'))

        self.assertEqual(list(listing.context['documents']), [])
        self.assertNotContains(listing, self.visible_document.title)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_cross_workspace_relationship_is_excluded(self):
        foreign_organization = Organization.objects.create(
            name='Foreign Documents',
            slug='foreign-documents',
        )
        foreign_client = Client.objects.create(
            organization=foreign_organization,
            name='Foreign relationship',
        )
        inconsistent_document = Document.objects.create(
            organization=self.organization,
            client=foreign_client,
            title='Inconsistent relationship document',
            uploaded_by=self.owner,
        )

        listing = self.client.get(reverse('contracts:document_list'))
        detail = self.client.get(
            reverse('contracts:document_detail', args=[inconsistent_document.pk])
        )

        self.assertNotIn(
            inconsistent_document.pk,
            set(listing.context['documents'].values_list('pk', flat=True)),
        )
        self.assertNotContains(listing, inconsistent_document.title)
        self.assertEqual(detail.status_code, 404)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_inactive_membership_fails_closed_at_policy_boundary(self):
        OrganizationMembership.objects.filter(
            organization=self.organization,
            user=self.member,
        ).update(is_active=False)

        eligible = apply_document_repository_policy(
            Document.objects.all(),
            organization=self.organization,
            user=self.member,
            surface='inactive_membership_test',
        )

        self.assertFalse(eligible.exists())
