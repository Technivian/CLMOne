"""Map Contract.status, lifecycle_stage, and Document.status to three-dimension vocabulary.

Historical AuditLog payloads are left unchanged (strings remain as logged).
"""

from django.db import migrations, models


def forwards_map_dimensions(apps, schema_editor):
    Contract = apps.get_model('contracts', 'Contract')
    Document = apps.get_model('contracts', 'Document')

    # Record status mapping (historical → new).
    status_map = {
        'NEEDS_INPUT': 'IN_PROGRESS',
        'UPLOADED': 'IN_PROGRESS',
        'PROCESSING': 'IN_PROGRESS',
        'CLASSIFICATION_REQUIRED': 'IN_PROGRESS',
        'AI_REVIEW_IN_PROGRESS': 'IN_PROGRESS',
        'AI_REVIEW_READY': 'IN_PROGRESS',
        'HUMAN_REVIEW_IN_PROGRESS': 'IN_PROGRESS',
        'INFORMATION_REQUIRED': 'IN_PROGRESS',
        'INTERNAL_APPROVAL_REQUIRED': 'IN_PROGRESS',
        'NEGOTIATION_IN_PROGRESS': 'IN_PROGRESS',
        'READY_FOR_SIGNATURE': 'IN_PROGRESS',
        'SIGNATURE_IN_PROGRESS': 'IN_PROGRESS',
        'EXECUTED': 'IN_PROGRESS',
        'OBLIGATIONS_ACTIVE': 'ACTIVE',
        'DRAFT': 'IN_PROGRESS',
        'PENDING': 'IN_PROGRESS',
        'IN_REVIEW': 'IN_PROGRESS',
        'APPROVED': 'IN_PROGRESS',
        'ACTIVE': 'ACTIVE',
        'EXPIRED': 'EXPIRED',
        'TERMINATED': 'TERMINATED',
        'COMPLETED': 'ACTIVE',
        'CANCELLED': 'CANCELLED',
        'ARCHIVED': 'ARCHIVED',
        'IN_PROGRESS': 'IN_PROGRESS',
    }

    doc_status_map = {
        'DRAFT': 'DRAFT',
        'REVIEW': 'DRAFT',
        'APPROVED': 'FINAL',
        'FINAL': 'FINAL',
        'ARCHIVED': 'SUPERSEDED',
        'EXECUTED': 'EXECUTED',
        'SUPERSEDED': 'SUPERSEDED',
    }

    post_activation_stages = {'EXECUTED', 'OBLIGATION_TRACKING', 'RENEWAL'}

    for contract in Contract.objects.all().iterator(chunk_size=500):
        old_status = contract.status
        old_stage = contract.lifecycle_stage

        if old_stage == 'ARCHIVED':
            new_status = 'ARCHIVED'
            new_stage = 'OBLIGATION_TRACKING'
        else:
            new_status = status_map.get(old_status, 'IN_PROGRESS')
            new_stage = old_stage if old_stage in {
                'INTAKE', 'DRAFTING', 'INTERNAL_REVIEW', 'NEGOTIATION', 'APPROVAL',
                'SIGNATURE', 'EXECUTED', 'OBLIGATION_TRACKING', 'RENEWAL',
            } else 'DRAFTING'
            # Live operational contracts: keep ACTIVE with post-activation stage.
            if old_status in {'ACTIVE', 'OBLIGATIONS_ACTIVE', 'COMPLETED'}:
                new_status = 'ACTIVE'
                if new_stage not in post_activation_stages:
                    new_stage = 'OBLIGATION_TRACKING'
            # IN_PROGRESS cannot rest on obligation/renewal stages.
            if new_status == 'IN_PROGRESS' and new_stage in {'OBLIGATION_TRACKING', 'RENEWAL'}:
                new_status = 'ACTIVE'
            # ACTIVE cannot rest on pre-execution stages (except EXECUTED resting).
            if new_status == 'ACTIVE' and new_stage not in post_activation_stages:
                new_stage = 'OBLIGATION_TRACKING'

        if new_status != old_status or new_stage != old_stage:
            Contract.objects.filter(pk=contract.pk).update(
                status=new_status,
                lifecycle_stage=new_stage,
            )

    for document in Document.objects.all().iterator(chunk_size=500):
        old_doc_status = document.status
        new_doc_status = doc_status_map.get(old_doc_status, 'DRAFT')

        if document.contract_id:
            contract = Contract.objects.filter(pk=document.contract_id).first()
            if contract and new_doc_status == 'FINAL':
                if (
                    contract.status in {'ACTIVE', 'EXPIRED', 'TERMINATED', 'ARCHIVED'}
                    or contract.lifecycle_stage in post_activation_stages
                ):
                    # Upgrade primary final docs on active/executed contracts.
                    siblings = Document.objects.filter(
                        contract_id=document.contract_id,
                        is_deleted=False,
                    ).exclude(status='SUPERSEDED').order_by('-version', '-id')
                    primary = siblings.first()
                    if primary and primary.pk == document.pk:
                        new_doc_status = 'EXECUTED'

        if new_doc_status != old_doc_status:
            Document.objects.filter(pk=document.pk).update(status=new_doc_status)


def backwards_noop(apps, schema_editor):
    # Historical enum values are not restored; audit payloads retain originals.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0094_userprofile_account_preferences'),
    ]

    operations = [
        # Expand choices additively first so RunPython can write new values.
        migrations.AlterField(
            model_name='contract',
            name='status',
            field=models.CharField(
                choices=[
                    ('IN_PROGRESS', 'In progress'),
                    ('ACTIVE', 'Active'),
                    ('EXPIRED', 'Expired'),
                    ('TERMINATED', 'Terminated'),
                    ('CANCELLED', 'Cancelled'),
                    ('ARCHIVED', 'Archived'),
                    # Temporary legacy values accepted during remap.
                    ('NEEDS_INPUT', 'Needs input'),
                    ('UPLOADED', 'Uploaded'),
                    ('PROCESSING', 'Processing'),
                    ('CLASSIFICATION_REQUIRED', 'Classification Required'),
                    ('AI_REVIEW_IN_PROGRESS', 'AI Review in Progress'),
                    ('AI_REVIEW_READY', 'AI Review Ready'),
                    ('HUMAN_REVIEW_IN_PROGRESS', 'Human Review in Progress'),
                    ('INFORMATION_REQUIRED', 'Information Required'),
                    ('INTERNAL_APPROVAL_REQUIRED', 'Internal Approval Required'),
                    ('NEGOTIATION_IN_PROGRESS', 'Negotiation in Progress'),
                    ('READY_FOR_SIGNATURE', 'Ready for Signature'),
                    ('SIGNATURE_IN_PROGRESS', 'Signature in Progress'),
                    ('EXECUTED', 'Executed'),
                    ('OBLIGATIONS_ACTIVE', 'Obligations Active'),
                    ('DRAFT', 'Draft'),
                    ('PENDING', 'Pending'),
                    ('IN_REVIEW', 'In Review'),
                    ('APPROVED', 'Approved'),
                    ('COMPLETED', 'Completed'),
                ],
                default='IN_PROGRESS',
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='contract',
            name='lifecycle_stage',
            field=models.CharField(
                choices=[
                    ('INTAKE', 'Intake'),
                    ('DRAFTING', 'Drafting'),
                    ('INTERNAL_REVIEW', 'Internal review'),
                    ('NEGOTIATION', 'Negotiation'),
                    ('APPROVAL', 'Approval'),
                    ('SIGNATURE', 'Signature'),
                    ('EXECUTED', 'Executed'),
                    ('OBLIGATION_TRACKING', 'Obligation tracking'),
                    ('RENEWAL', 'Renewal'),
                    ('ARCHIVED', 'Archived'),
                ],
                default='DRAFTING',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='document',
            name='status',
            field=models.CharField(
                choices=[
                    ('DRAFT', 'Draft'),
                    ('FINAL', 'Final'),
                    ('EXECUTED', 'Executed'),
                    ('SUPERSEDED', 'Superseded'),
                    ('REVIEW', 'Under Review'),
                    ('APPROVED', 'Approved'),
                    ('ARCHIVED', 'Archived'),
                ],
                default='DRAFT',
                max_length=20,
            ),
        ),
        migrations.RunPython(forwards_map_dimensions, backwards_noop),
        # Freeze to canonical choices only.
        migrations.AlterField(
            model_name='contract',
            name='status',
            field=models.CharField(
                choices=[
                    ('IN_PROGRESS', 'In progress'),
                    ('ACTIVE', 'Active'),
                    ('EXPIRED', 'Expired'),
                    ('TERMINATED', 'Terminated'),
                    ('CANCELLED', 'Cancelled'),
                    ('ARCHIVED', 'Archived'),
                ],
                default='IN_PROGRESS',
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='contract',
            name='lifecycle_stage',
            field=models.CharField(
                choices=[
                    ('INTAKE', 'Intake'),
                    ('DRAFTING', 'Drafting'),
                    ('INTERNAL_REVIEW', 'Internal review'),
                    ('NEGOTIATION', 'Negotiation'),
                    ('APPROVAL', 'Approval'),
                    ('SIGNATURE', 'Signature'),
                    ('EXECUTED', 'Executed'),
                    ('OBLIGATION_TRACKING', 'Obligation tracking'),
                    ('RENEWAL', 'Renewal'),
                ],
                default='DRAFTING',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='document',
            name='status',
            field=models.CharField(
                choices=[
                    ('DRAFT', 'Draft'),
                    ('FINAL', 'Final'),
                    ('EXECUTED', 'Executed'),
                    ('SUPERSEDED', 'Superseded'),
                ],
                default='DRAFT',
                max_length=20,
            ),
        ),
    ]
