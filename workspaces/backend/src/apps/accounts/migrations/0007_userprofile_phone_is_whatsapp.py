from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_usertaskcategory_usertask_usertaskassignment"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="phone_is_whatsapp",
            field=models.BooleanField(default=False),
        ),
    ]
