from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0008_portalconfig_cloudflare_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="portalconfig",
            name="email_settings",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
