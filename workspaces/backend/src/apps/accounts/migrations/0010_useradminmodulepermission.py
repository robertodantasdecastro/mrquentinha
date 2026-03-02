from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_encrypt_sensitive_profile_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserAdminModulePermission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("module_slug", models.CharField(max_length=64)),
                (
                    "access_level",
                    models.CharField(
                        choices=[("read", "Leitura"), ("write", "Leitura e escrita")],
                        default="read",
                        max_length=8,
                    ),
                ),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="admin_module_permissions_granted",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="admin_module_permissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["user_id", "module_slug"],
            },
        ),
        migrations.AddConstraint(
            model_name="useradminmodulepermission",
            constraint=models.UniqueConstraint(
                fields=("user", "module_slug"),
                name="accounts_useradminmodulepermission_user_module_unique",
            ),
        ),
    ]
