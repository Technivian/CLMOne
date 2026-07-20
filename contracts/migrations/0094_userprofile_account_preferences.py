from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0093_contract_intake_privacy_signals'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='date_format',
            field=models.CharField(
                choices=[
                    ('d M Y', '31 Jan 2026'),
                    ('Y-m-d', '2026-01-31'),
                    ('m/d/Y', '01/31/2026'),
                    ('d/m/Y', '31/01/2026'),
                ],
                default='d M Y',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='language',
            field=models.CharField(
                choices=[
                    ('en', 'English'),
                    ('nl', 'Nederlands'),
                    ('de', 'Deutsch'),
                    ('fr', 'Français'),
                ],
                default='en',
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notify_contract_updates',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notify_security_alerts',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notify_workflow_events',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='timezone',
            field=models.CharField(default='UTC', max_length=64),
        ),
    ]
