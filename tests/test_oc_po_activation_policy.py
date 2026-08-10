"""Default-off technical activation coverage for Order Confirmation and PO."""

from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from contracts.models import (
    AuditLog,
    Contract,
    ContractTemplate,
    Counterparty,
    Document,
    LegalTask,
    Organization,
    OrganizationMembership,
    Workflow,
)
from contracts.permissions import ContractAction, can_access_contract_action
from contracts.services.document_version_service import create_document_version
from contracts.services.object_read_policy import (
    filter_document_queryset,
    filter_document_version_queryset,
    filter_legal_task_queryset,
    filter_workflow_queryset,
)
from contracts.services.repository_csv_import import get_repository_csv_import_service
from contracts.services.search_api import ContractSearchAPIService
from contracts.services.contract_type_activation import active_contract_type_codes


User = get_user_model()

PILOT_DEFAULTS = {
    'CONTROLLED_PILOT_ENABLED': True,
    'PAYROLLMINDS_ENABLED_CONTRACT_TYPES': ('MSA', 'NDA', 'DPA'),
    'GEMINI_AI_ENABLED': False,
    'REPOSITORY_CSV_IMPORT_ENABLED': False,
}
PILOT_OC_PO_ENABLED = {
    **PILOT_DEFAULTS,
    'PAYROLLMINDS_ENABLED_CONTRACT_TYPES': ('MSA', 'NDA', 'DPA', 'ORDER_CONFIRMATION', 'PURCHASE_ORDER'),
}


class OrderConfirmationPurchaseOrderActivationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='OC PO activation', slug='oc-po-activation')
        self.other_organization = Organization.objects.create(name='Other OC PO', slug='other-oc-po')
        self.owner = User.objects.create_user(username='ocpo-owner', password='testpass123')
        self.member = User.objects.create_user(username='ocpo-member', password='testpass123')
        self.outsider = User.objects.create_user(username='ocpo-outsider', password='testpass123')
        for organization, user, role in (
            (self.organization, self.owner, OrganizationMembership.Role.OWNER),
            (self.organization, self.member, OrganizationMembership.Role.MEMBER),
            (self.other_organization, self.outsider, OrganizationMembership.Role.OWNER),
        ):
            OrganizationMembership.objects.create(
                organization=organization,
                user=user,
                role=role,
                is_active=True,
            )
        self.client.force_login(self.owner)

    @override_settings(**PILOT_DEFAULTS)
    def test_default_policy_hides_and_blocks_oc_po_and_other_inactive_types(self):
        self.assertEqual(active_contract_type_codes(), frozenset({'MSA', 'NDA', 'DPA'}))
        picker = self.client.get(reverse('contracts:contract_template_picker'))
        self.assertEqual(picker.status_code, 200)
        for label in ('Order Confirmation', 'Purchase Order', 'Supplier Agreement', 'Other'):
            self.assertNotContains(picker, label)

        for code in ('ORDER_CONFIRMATION', 'PURCHASE_ORDER', 'SOW', 'VENDOR', 'EMPLOYMENT', 'SAAS', 'LEASE', 'OTHER'):
            with self.subTest(code=code):
                response = self.client.get(
                    reverse('contracts:contract_type_create', kwargs={'contract_type': code}),
                    follow=False,
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, reverse('dashboard'))

        # Generic form, upload, and CSV import remain separate fail-closed
        # routes; no type can use them to bypass the policy.
        self.assertEqual(self.client.get(reverse('contracts:contract_create')).status_code, 302)
        self.assertEqual(self.client.get(reverse('contracts:upload_signed_contract')).status_code, 302)
        self.assertEqual(self.client.get(reverse('contracts:repository_csv_import')).status_code, 404)

        Counterparty.objects.create(
            organization=self.organization,
            name='CSV Counterparty',
        )
        preview = get_repository_csv_import_service().preview(
            organization=self.organization,
            actor=self.owner,
            csv_bytes=(
                b'title,contract_type,counterparty\n'
                b'Blocked CSV OC,ORDER_CONFIRMATION,CSV Counterparty\n'
            ),
        )
        self.assertFalse(preview.preview_token)
        self.assertIn('not_activated', {issue.code for issue in preview.issues})

        # The direct document API also uses the same central boundary before
        # it can create a Contract from an upload.
        upload = self.client.post(
            reverse('contracts:document_upload_api'),
            {
                'create_contract': 'true',
                'contract_type': Contract.ContractType.PURCHASE_ORDER,
                'file': SimpleUploadedFile('blocked.txt', b'synthetic', content_type='text/plain'),
            },
        )
        self.assertEqual(upload.status_code, 404)
        self.assertFalse(Contract.objects.filter(contract_type=Contract.ContractType.PURCHASE_ORDER).exists())

    @override_settings(**PILOT_OC_PO_ENABLED)
    def test_test_only_enabled_types_create_canonical_private_contract_records(self):
        created = {}
        for code in ('ORDER_CONFIRMATION', 'PURCHASE_ORDER'):
            with self.subTest(code=code):
                response = self.client.post(
                    reverse('contracts:contract_type_create', kwargs={'contract_type': code}),
                    {
                        'title': f'Synthetic {code}',
                        'contract_type': code,
                        'counterparty': 'Synthetic Counterparty',
                        'governing_law': 'Netherlands',
                        'jurisdiction': 'Amsterdam',
                        'owner': self.owner.pk,
                        'currency': Contract.Currency.EUR,
                        'start_date': date(2026, 1, 1).isoformat(),
                        'end_date': date(2027, 1, 1).isoformat(),
                    },
                    follow=False,
                )
                self.assertEqual(response.status_code, 302)
                contract = Contract.objects.get(title=f'Synthetic {code}')
                created[code] = contract
                self.assertEqual(contract.organization, self.organization)
                self.assertEqual(contract.contract_type, code)
                self.assertEqual(contract.owner, self.owner)
                self.assertEqual(contract.created_by, self.owner)
                self.assertIsNotNone(contract.contract_type_catalogue_id)
                self.assertTrue(contract.provenance_locked_at)
                self.assertEqual(contract.origin_channel, 'contract_create_ui')
                self.assertEqual(
                    self.client.get(reverse('contracts:contract_detail', args=[contract.pk])).status_code,
                    200,
                )
                self.assertTrue(
                    AuditLog.objects.filter(
                        organization=self.organization,
                        object_id=contract.pk,
                        changes__event='contract_created',
                    ).exists()
                )

                document, version = create_document_version(
                    organization=self.organization,
                    contract=contract,
                    title=f'{code} source document',
                    document_type=Document.DocType.CONTRACT,
                    status=Document.Status.DRAFT,
                    file=SimpleUploadedFile(f'{code}.txt', b'synthetic evidence', content_type='text/plain'),
                    uploaded_by=self.owner,
                    actor=self.owner,
                    source='manual_upload',
                )
                self.assertEqual(document.contract_id, contract.pk)
                self.assertEqual(version.document_row_id, document.pk)
                self.assertEqual(version.logical_document_id, document.logical_document_id)
                self.assertTrue(version.version_locked_at)

        member_client = Client()
        member_client.force_login(self.member)
        outsider_client = Client()
        outsider_client.force_login(self.outsider)
        for contract in created.values():
            with self.subTest(contract=contract.contract_type, boundary='same_workspace'):
                self.assertEqual(
                    member_client.get(reverse('contracts:contract_detail', args=[contract.pk])).status_code,
                    404,
                )
                self.assertNotContains(member_client.get(reverse('contracts:repository')), contract.title)
            with self.subTest(contract=contract.contract_type, boundary='cross_workspace'):
                self.assertEqual(
                    outsider_client.get(reverse('contracts:contract_detail', args=[contract.pk])).status_code,
                    404,
                )

                document = contract.documents.get()
                version = document.canonical_version
                self.assertTrue(filter_document_queryset(
                    Document.objects.filter(pk=document.pk),
                    organization=self.organization,
                    user=self.owner,
                ).exists())
                self.assertFalse(filter_document_queryset(
                    Document.objects.filter(pk=document.pk),
                    organization=self.organization,
                    user=self.member,
                ).exists())
                self.assertFalse(filter_document_version_queryset(
                    type(version).objects.filter(pk=version.pk),
                    organization=self.organization,
                    user=self.member,
                ).exists())
                self.assertEqual(
                    member_client.get(reverse('contracts:document_detail', args=[document.pk])).status_code,
                    404,
                )

                self.assertTrue(can_access_contract_action(self.owner, contract, ContractAction.AI))
                self.assertFalse(can_access_contract_action(self.member, contract, ContractAction.AI))

                search = ContractSearchAPIService().search_contracts(
                    self.organization,
                    q=contract.title,
                    user=self.member,
                )
                facets = ContractSearchAPIService().get_contract_facets(
                    self.organization,
                    user=self.member,
                )
                self.assertEqual(search.total, 0)
                self.assertEqual(sum(
                    item['count'] for values in facets.values() for item in values
                ), 0)

                workflow = Workflow.objects.create(
                    organization=self.organization,
                    contract=contract,
                    title=f'{code} inherited workflow',
                    created_by=self.owner,
                )
                work_item = LegalTask.objects.create(
                    contract=contract,
                    title=f'{code} inherited work item',
                    description='Synthetic private work item',
                    assigned_to=self.owner,
                    due_date=date(2026, 2, 1),
                )
                self.assertFalse(filter_workflow_queryset(
                    Workflow.objects.filter(pk=workflow.pk),
                    organization=self.organization,
                    user=self.member,
                ).exists())
                self.assertFalse(filter_legal_task_queryset(
                    LegalTask.objects.filter(pk=work_item.pk),
                    organization=self.organization,
                    user=self.member,
                ).exists())

                # Deactivating the only membership revokes every object read
                # immediately; this is intentionally in an isolated test DB.
                owner_membership = OrganizationMembership.objects.get(
                    organization=self.organization,
                    user=self.owner,
                )
                owner_membership.is_active = False
                owner_membership.save(update_fields=['is_active'])
                self.assertFalse(can_access_contract_action(self.owner, contract, ContractAction.VIEW))
                owner_membership.is_active = True
                owner_membership.save(update_fields=['is_active'])

    @override_settings(**PILOT_OC_PO_ENABLED)
    def test_enabled_type_template_uses_the_governed_standard_intake_route(self):
        template = ContractTemplate.objects.create(
            name='Synthetic OC template',
            contract_type=Contract.ContractType.ORDER_CONFIRMATION,
            body='Synthetic template body',
        )
        picker = self.client.get(
            reverse('contracts:contract_template_picker'),
            {'type': Contract.ContractType.ORDER_CONFIRMATION},
        )
        self.assertContains(
            picker,
            reverse(
                'contracts:contract_type_create',
                kwargs={'contract_type': Contract.ContractType.ORDER_CONFIRMATION},
            ) + f'?template={template.pk}',
        )
