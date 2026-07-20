"""Deterministic seed for the approved single-organisation controlled pilot."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from contracts.models import (
    ApprovalRule,
    Contract,
    Organization,
    OrganizationMembership,
    OrgPolicy,
    UserProfile,
)
from contracts.services.finance_approval_policy import get_finance_approval_threshold


PILOT_ORG_SLUG = 'controlled-pilot-org'
PILOT_ORG_NAME = 'CLM One Controlled Pilot'
PILOT_PASSWORD = 'PilotPass123!'


USERS = (
    # username, email, membership_role, profile_role, department
    ('pilot_owner', 'pilot_owner@example.com', OrganizationMembership.Role.OWNER, UserProfile.Role.ADMIN, 'Executive'),
    ('pilot_admin', 'pilot_admin@example.com', OrganizationMembership.Role.ADMIN, UserProfile.Role.ADMIN, 'Operations'),
    ('pilot_requester', 'pilot_requester@example.com', OrganizationMembership.Role.MEMBER, UserProfile.Role.PARALEGAL, 'Revenue Operations'),
    ('pilot_legal', 'pilot_legal@example.com', OrganizationMembership.Role.MEMBER, UserProfile.Role.ASSOCIATE, 'Legal'),
    ('pilot_finance', 'pilot_finance@example.com', OrganizationMembership.Role.MEMBER, UserProfile.Role.ADMIN, 'Finance'),
)


class Command(BaseCommand):
    help = 'Seed one-org controlled pilot users, rules, and sample contracts.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-samples',
            action='store_true',
            help='Delete and recreate sample pilot contracts for this org.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        org, _ = Organization.objects.get_or_create(
            slug=PILOT_ORG_SLUG,
            defaults={
                'name': PILOT_ORG_NAME,
                'workspace_mode': Organization.WorkspaceMode.IN_HOUSE_CLM,
            },
        )
        org.name = PILOT_ORG_NAME
        org.workspace_mode = Organization.WorkspaceMode.IN_HOUSE_CLM
        org.save()

        OrgPolicy.objects.update_or_create(
            organization=org,
            defaults={'ai_features_enabled': False},
        )

        users = {}
        for username, email, membership_role, profile_role, department in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email},
            )
            user.email = email
            user.set_password(PILOT_PASSWORD)
            user.is_staff = membership_role in {
                OrganizationMembership.Role.OWNER,
                OrganizationMembership.Role.ADMIN,
            }
            user.save()
            OrganizationMembership.objects.update_or_create(
                organization=org,
                user=user,
                defaults={'role': membership_role, 'is_active': True},
            )
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': profile_role,
                    'department': department,
                    'is_active': True,
                },
            )
            users[username] = user
            self.stdout.write(f'user={username} created={created} role={membership_role}')

        legal = users['pilot_legal']
        finance = users['pilot_finance']
        for step, reviewer, hours, order in (
            ('LEGAL', legal, 48, 10),
            ('FINANCE', finance, 24, 20),
        ):
            ApprovalRule.objects.update_or_create(
                organization=org,
                name=f'Pilot MSA {step.title()} approval',
                defaults={
                    'description': f'Controlled pilot {step} rule',
                    'trigger_type': ApprovalRule.TriggerType.CONTRACT_TYPE,
                    'trigger_value': 'MSA',
                    'approval_step': step,
                    'approver_role': reviewer.profile.role,
                    'specific_approver': reviewer,
                    'sla_hours': hours,
                    'escalation_after_hours': hours + 24,
                    'is_active': True,
                    'order': order,
                },
            )

        threshold = get_finance_approval_threshold(org)
        owner = users['pilot_owner']
        requester = users['pilot_requester']

        if options['reset_samples']:
            Contract.objects.filter(organization=org, title__startswith='Pilot Sample').delete()

        samples = (
            ('Pilot Sample MSA Below Threshold', Contract.ContractType.MSA, Decimal('99999'), 'Acme Below Co'),
            ('Pilot Sample MSA At Threshold', Contract.ContractType.MSA, Decimal('100000'), 'Acme Exact Co'),
            ('Pilot Sample MSA Above Threshold', Contract.ContractType.MSA, Decimal('100001'), 'Acme Above Co'),
            ('Pilot Sample NDA Mutual', Contract.ContractType.NDA, None, 'NDA Counterparty BV'),
            ('Pilot Sample DPA Processor', Contract.ContractType.DPA, None, 'DPA Processor Ltd'),
        )
        for title, ctype, value, counterparty in samples:
            defaults = {
                'contract_type': ctype,
                'status': Contract.Status.IN_PROGRESS,
                'lifecycle_stage': 'DRAFTING',
                'counterparty': counterparty,
                'owner': requester,
                'created_by': owner,
                'organization': org,
                'currency': 'USD',
                'content': f'{title} — controlled pilot sample. No live confidential client data.',
            }
            if value is not None:
                defaults['value'] = value
            contract, created = Contract.objects.get_or_create(
                organization=org,
                title=title,
                defaults=defaults,
            )
            if not created and options['reset_samples']:
                for key, val in defaults.items():
                    setattr(contract, key, val)
                contract.save()
            self.stdout.write(f'contract={title} created={created} value={value}')

        self.stdout.write(self.style.SUCCESS(
            f'controlled_pilot_seed_ok org={org.slug} finance_threshold={threshold} '
            f'ai_org_policy=disabled password_shared=PilotPass123!'
        ))
        self.stdout.write(
            'roles: pilot_owner(OWNER), pilot_admin(ADMIN), pilot_requester(MEMBER), '
            'pilot_legal(Legal), pilot_finance(Finance)'
        )
