from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0006_portalconfig_payment_providers"),
    ]

    operations = [
        migrations.AddField(
            model_name="portalconfig",
            name="admin_active_template",
            field=models.CharField(default="admin-classic", max_length=64),
        ),
        migrations.AddField(
            model_name="portalconfig",
            name="admin_available_templates",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
