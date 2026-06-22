from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0048_organizationapitoken_expires_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='auditlog',
            name='entry_hash',
            field=models.CharField(
                max_length=64,
                blank=True,
                help_text='SHA-256 of (id:user_id:action:model_name:object_id:timestamp:changes). '
                          'Blank on rows written before this migration.',
            ),
        ),
    ]
