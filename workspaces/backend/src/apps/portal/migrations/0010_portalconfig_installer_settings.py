from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0009_portalconfig_email_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="portalconfig",
            name="installer_settings",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
