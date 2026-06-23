# Generated for Phase 5L — operator job-failure alert deduplication.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0057_invitation_delivery_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledjobrun',
            name='alert_sent_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Set when an operator failure-alert email was sent for this run. '
                          'Used for deduplication (one alert per job_name per hour).',
            ),
        ),
    ]
