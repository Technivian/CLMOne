from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0047_orgbillingsubscription_stripe_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationapitoken',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True, help_text='Token is rejected after this datetime. Leave blank for no expiry.'),
        ),
    ]
