#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PY="$ROOT_DIR/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY=python
fi

export DJANGO_E2E=1
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings_development}"
export DATABASE_URL="${E2E_DATABASE_URL:-sqlite:///$ROOT_DIR/e2e.sqlite3}"
# Isolate e2e from developer .env Redis (often remote Upstash). Use local Redis only when explicitly requested.
# Empty REDIS_URL must remain set so settings_base._load_dotenv setdefault cannot reinstate .env.
if [ -n "${E2E_REDIS_URL:-}" ]; then
  export REDIS_URL="$E2E_REDIS_URL"
else
  export REDIS_URL=
fi
# Deterministic auth throttle for browser gate tests (forced; do not inherit ambient overrides).
export LOGIN_RATE_LIMIT_REQUESTS=3
export LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
export RATELIMIT_ENABLED=true
export RATELIMIT_TRUSTED_IPS=
# Disable live AI provider in e2e so search/draft paths use deterministic fallbacks.
export GEMINI_API_KEY=
export GEMINI_AI_ENABLED=false

if [ -z "${E2E_DATABASE_URL:-}" ]; then
  rm -f "$ROOT_DIR/e2e.sqlite3"
fi
"$PY" "$ROOT_DIR/manage.py" migrate --noinput
"$PY" "$ROOT_DIR/manage.py" shell -c "
from django.contrib.auth import get_user_model
from contracts.models import ApprovalRule, Client, Matter, Organization, OrganizationMembership, UserProfile

User = get_user_model()
user, _ = User.objects.get_or_create(
    username='e2e_owner',
    defaults={'email': 'e2e_owner@example.com'},
)
user.is_staff = True
user.is_superuser = True
user.set_password('e2e_pass_123')
user.save()

org, _ = Organization.objects.get_or_create(
    slug='e2e-command-center',
    defaults={'name': 'E2E Command Center', 'workspace_mode': Organization.WorkspaceMode.IN_HOUSE_CLM},
)
if org.workspace_mode != Organization.WorkspaceMode.IN_HOUSE_CLM:
    org.workspace_mode = Organization.WorkspaceMode.IN_HOUSE_CLM
    org.save(update_fields=['workspace_mode', 'updated_at'])

membership, _ = OrganizationMembership.objects.get_or_create(
    organization=org,
    user=user,
    defaults={'role': OrganizationMembership.Role.OWNER, 'is_active': True},
)
if not membership.is_active or membership.role != OrganizationMembership.Role.OWNER:
    membership.is_active = True
    membership.role = OrganizationMembership.Role.OWNER
    membership.save(update_fields=['is_active', 'role', 'updated_at'])

for username, password, first_name, department, profile_role in [
    ('e2e_legal', 'e2e_legal_pass_123', 'Legal', 'Legal', UserProfile.Role.ASSOCIATE),
    ('e2e_finance', 'e2e_finance_pass_123', 'Finance', 'Finance', UserProfile.Role.ADMIN),
]:
    reviewer, _ = User.objects.get_or_create(username=username, defaults={'email': f'{username}@example.com'})
    reviewer.first_name = first_name
    reviewer.set_password(password)
    reviewer.save()
    OrganizationMembership.objects.update_or_create(
        organization=org,
        user=reviewer,
        defaults={'role': OrganizationMembership.Role.MEMBER, 'is_active': True},
    )
    UserProfile.objects.update_or_create(
        user=reviewer,
        defaults={'role': profile_role, 'department': department, 'is_active': True},
    )

legal_reviewer = User.objects.get(username='e2e_legal')
finance_reviewer = User.objects.get(username='e2e_finance')
for step, reviewer, hours in [
    ('LEGAL', legal_reviewer, 48),
    ('FINANCE', finance_reviewer, 24),
]:
    ApprovalRule.objects.update_or_create(
        organization=org,
        name=f'E2E MSA {step.title()} approval',
        defaults={
            'description': f'Demo authority for MSA {step.title()} review.',
            'trigger_type': ApprovalRule.TriggerType.CONTRACT_TYPE,
            'trigger_value': 'MSA',
            'approval_step': step,
            'approver_role': reviewer.profile.role,
            'specific_approver': reviewer,
            'sla_hours': hours,
            'escalation_after_hours': hours + 24,
            'is_active': True,
            'order': 10 if step == 'LEGAL' else 20,
        },
    )

# Fixture data for the invoice/time-entry e2e flow, which needs an existing
# Client and Matter to select from — nothing else in this setup creates one.
client, _ = Client.objects.get_or_create(
    organization=org,
    name='E2E Fixture Client',
    defaults={'created_by': user},
)
Matter.objects.get_or_create(
    organization=org,
    matter_number='E2E-0001',
    defaults={'title': 'E2E Fixture Matter', 'client': client, 'created_by': user},
)

# Cross-tenant search exclusion fixture: clause visible only in a foreign org.
from contracts.models import ClauseTemplate
foreign_org, _ = Organization.objects.get_or_create(
    slug='e2e-foreign-tenant',
    defaults={'name': 'E2E Foreign Tenant', 'workspace_mode': Organization.WorkspaceMode.IN_HOUSE_CLM},
)
ClauseTemplate.objects.get_or_create(
    organization=foreign_org,
    title='FOREIGN_TENANT_SECRET_CLAUSE_E2E',
    defaults={
        'content': 'This clause must never appear in e2e-command-center search results.',
        'created_by': user,
    },
)
ClauseTemplate.objects.get_or_create(
    organization=org,
    title='E2E Local Indemnity Clause',
    defaults={
        'content': 'Indemnity and confidentiality obligations for pilot verification search.',
        'created_by': user,
    },
)
"

"$PY" "$ROOT_DIR/manage.py" seed_demo_command_center \
  --organization-slug e2e-command-center \
  --username e2e_owner
"$PY" "$ROOT_DIR/manage.py" seed_payrollminds_demo

exec "$PY" "$ROOT_DIR/manage.py" runserver 127.0.0.1:8010 --noreload
