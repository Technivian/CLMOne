"""Seed a fresh SignatureRequest in PENDING state for SPR3-005 e-sign rehearsal evidence."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from contracts.models import Contract, Organization, OrganizationMembership, SignatureRequest


User = get_user_model()


class Command(BaseCommand):
    help = 'Seed a fresh SignatureRequest in PENDING state for SPR3-005 e-sign reconciliation rehearsal.'

    def add_arguments(self, parser):
        parser.add_argument('--organization-slug', default='demo-firm')
        parser.add_argument('--organization-name', default='Demo Firm')
        parser.add_argument('--external-id', default='rehearsal-esign-001')

    def handle(self, *args, **options):
        now = timezone.now()
        organization_slug = str(options.get('organization_slug') or 'demo-firm').strip() or 'demo-firm'
        organization_name = str(options.get('organization_name') or 'Demo Firm').strip() or 'Demo Firm'
        external_id = str(options.get('external_id') or 'rehearsal-esign-001').strip()

        admin = User.objects.filter(username='admin').first()
        if admin is None:
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
            )

        organization, _ = Organization.objects.get_or_create(
            slug=organization_slug,
            defaults={'name': organization_name},
        )

        OrganizationMembership.objects.get_or_create(
            organization=organization,
            user=admin,
            defaults={'role': OrganizationMembership.Role.OWNER, 'is_active': True},
        )

        contract, _ = Contract.objects.get_or_create(
            organization=organization,
            title='SPR3-005 E-Sign Rehearsal Contract',
            defaults={
                'contract_type': Contract.ContractType.MSA,
                'content': 'Synthetic e-sign rehearsal contract for SPR3-005 evidence.',
                'status': Contract.Status.ACTIVE,
                'counterparty': 'Rehearsal Provider LLC',
                'value': 10000,
                'currency': Contract.Currency.USD,
                'governing_law': 'State of Delaware',
                'jurisdiction': 'New York',
                'start_date': now.date() - timedelta(days=7),
                'end_date': now.date() + timedelta(days=358),
                'lifecycle_stage': 'EXECUTED',
                'created_by': admin,
            },
        )

        existing = SignatureRequest.objects.filter(
            organization=organization,
            external_id=external_id,
        ).first()
        if existing is not None:
            existing.status = SignatureRequest.Status.PENDING
            existing.signed_at = None
            existing.viewed_at = None
            existing.sent_at = None
            existing.save(update_fields=['status', 'signed_at', 'viewed_at', 'sent_at'])
            signature_request = existing
        else:
            signature_request = SignatureRequest.objects.create(
                organization=organization,
                contract=contract,
                signer_name='Rehearsal Signer',
                signer_email='rehearsal-signer@example.com',
                signer_role='Authorized Signatory',
                status=SignatureRequest.Status.PENDING,
                external_id=external_id,
                created_by=admin,
            )

        self.stdout.write(self.style.SUCCESS('SPR3-005 e-sign rehearsal seed complete.'))
        self.stdout.write(f'  Organization: {organization.slug}')
        self.stdout.write(f'  Contract: {contract.id}')
        self.stdout.write(f'  SignatureRequest id={signature_request.id} external_id={external_id} status={signature_request.status}')
