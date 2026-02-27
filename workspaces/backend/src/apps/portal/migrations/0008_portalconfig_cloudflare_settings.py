from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0007_portalconfig_admin_templates"),
    ]

    operations = [
        migrations.AddField(
            model_name="portalconfig",
            name="cloudflare_settings",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
