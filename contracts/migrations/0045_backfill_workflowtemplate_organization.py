"""Backfill WorkflowTemplate.organization from unambiguous workflow usage.

Migration 0044 added a nullable ``organization`` FK to ``WorkflowTemplate``.
A null organization is treated as a *shared* template, visible to every
tenant. To avoid silently sharing templates that were in practice owned by a
single tenant, this data migration assigns each existing template to an
organization **only when its usage is unambiguous** — i.e. every workflow
instantiated from it belongs to exactly one organization.

Templates used by more than one organization, or used by none, are left null
(shared). This is intentionally conservative: it privatizes templates that
clearly belong to a single tenant without over-claiming ownership of genuinely
shared or unused templates.
"""

from django.db import migrations


def backfill_organization(apps, schema_editor):
    WorkflowTemplate = apps.get_model('contracts', 'WorkflowTemplate')
    Workflow = apps.get_model('contracts', 'Workflow')

    for template in WorkflowTemplate.objects.filter(organization__isnull=True):
        org_ids = set(
            Workflow.objects.filter(template=template)
            .exclude(organization__isnull=True)
            .values_list('organization_id', flat=True)
        )
        if len(org_ids) == 1:
            template.organization_id = next(iter(org_ids))
            template.save(update_fields=['organization'])


def noop_reverse(apps, schema_editor):
    # Forward backfill is not safely reversible: we cannot distinguish
    # templates that were null before this migration from those it assigned.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0044_workflowtemplate_organization'),
    ]

    operations = [
        migrations.RunPython(backfill_organization, noop_reverse),
    ]
