from django.db import migrations, models


CONTRACT_TYPE_CHOICES = [
    ('NDA', 'Non-Disclosure Agreement'),
    ('NON_COMPETE', 'Non-Compete / Non-Solicitation Agreement'),
    ('MSA', 'Master Service Agreement'),
    ('SOW', 'Statement of Work'),
    ('SUBCONTRACTOR_SOW', 'Subcontractor SOW Agreement'),
    ('CONSULTING', 'Consulting / Independent Contractor Agreement'),
    ('EMPLOYMENT', 'Employment Agreement'),
    ('LEASE', 'Lease Agreement'),
    ('LICENSE', 'License Agreement'),
    ('SAAS', 'SaaS Agreement'),
    ('TERMS_OF_SERVICE', 'Terms of Service / Terms & Conditions'),
    ('VENDOR', 'Vendor Agreement'),
    ('PURCHASE_ORDER', 'Purchase Order'),
    ('ORDER_CONFIRMATION', 'Order Confirmation'),
    ('PARTNERSHIP', 'Partnership Agreement'),
    ('RESELLER', 'Referral / Reseller / Channel Partner Agreement'),
    ('SETTLEMENT', 'Settlement Agreement'),
    ('AMENDMENT', 'Amendment'),
    ('DPA', 'Data Processing Agreement'),
    ('BAA', 'Business Associate Agreement (BAA)'),
    ('OTHER', 'Other'),
]


def migrate_payrollminds_order_confirmations(apps, schema_editor):
    Contract = apps.get_model('contracts', 'Contract')
    Contract.objects.filter(
        title='Atlas Workforce Order Confirmation 2026',
        contract_type='PURCHASE_ORDER',
    ).update(contract_type='ORDER_CONFIRMATION')


def restore_payrollminds_purchase_order(apps, schema_editor):
    Contract = apps.get_model('contracts', 'Contract')
    Contract.objects.filter(
        title='Atlas Workforce Order Confirmation 2026',
        contract_type='ORDER_CONFIRMATION',
    ).update(contract_type='PURCHASE_ORDER')


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0084_payrollminds_order_confirmation_wording'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='contract_type',
            field=models.CharField(
                choices=CONTRACT_TYPE_CHOICES,
                default='OTHER',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='contracttemplate',
            name='contract_type',
            field=models.CharField(choices=CONTRACT_TYPE_CHOICES, max_length=20),
        ),
        migrations.RunPython(
            migrate_payrollminds_order_confirmations,
            restore_payrollminds_purchase_order,
        ),
    ]
