from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contracts', '0116_documentingestionattempt'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='mfa_totp_secret_encrypted',
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='mfa_totp_confirmed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='mfa_totp_last_counter',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
