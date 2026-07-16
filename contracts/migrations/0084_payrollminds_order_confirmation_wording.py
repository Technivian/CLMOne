from django.db import migrations


WORKFLOW_TEMPLATE_NAME = 'MSA Commercial Review Workflow'
MSA_TEMPLATE_NAME = 'Standard Master Service Agreement'


def replace_sow_with_order_confirmation(apps, schema_editor):
    ContractTemplate = apps.get_model('contracts', 'ContractTemplate')
    template = ContractTemplate.objects.filter(
        name=MSA_TEMPLATE_NAME,
        contract_type='MSA',
    ).first()
    if template and 'any applicable Statement of Work' in template.body:
        template.body = template.body.replace(
            'any applicable Statement of Work',
            'any applicable Order Confirmation',
        )
        template.save(update_fields=['body'])


def restore_sow_wording(apps, schema_editor):
    ContractTemplate = apps.get_model('contracts', 'ContractTemplate')
    template = ContractTemplate.objects.filter(
        name=MSA_TEMPLATE_NAME,
        contract_type='MSA',
    ).first()
    if template and 'any applicable Order Confirmation' in template.body:
        template.body = template.body.replace(
            'any applicable Order Confirmation',
            'any applicable Statement of Work',
        )
        template.save(update_fields=['body'])


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0083_contract_parent_relationship'),
    ]

    operations = [
        migrations.RunPython(replace_sow_with_order_confirmation, restore_sow_wording),
    ]
