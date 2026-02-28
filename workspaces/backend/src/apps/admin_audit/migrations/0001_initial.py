from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminActivityLog",
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
                (
                    "request_id",
                    models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
                ),
                (
                    "actor_username",
                    models.CharField(
                        blank=True, db_index=True, default="", max_length=150
                    ),
                ),
                ("actor_is_staff", models.BooleanField(default=False)),
                ("actor_is_superuser", models.BooleanField(default=False)),
                (
                    "channel",
                    models.CharField(db_index=True, default="unknown", max_length=32),
                ),
                ("method", models.CharField(db_index=True, max_length=8)),
                ("path", models.CharField(db_index=True, max_length=255)),
                ("query_string", models.TextField(blank=True, default="")),
                (
                    "action_group",
                    models.CharField(
                        blank=True, db_index=True, default="", max_length=64
                    ),
                ),
                (
                    "resource",
                    models.CharField(
                        blank=True, db_index=True, default="", max_length=128
                    ),
                ),
                (
                    "http_status",
                    models.PositiveSmallIntegerField(db_index=True, default=0),
                ),
                ("is_success", models.BooleanField(db_index=True, default=True)),
                ("duration_ms", models.PositiveIntegerField(default=0)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("origin", models.CharField(blank=True, default="", max_length=255)),
                ("referer", models.TextField(blank=True, default="")),
                (
                    "user_agent",
                    models.CharField(blank=True, default="", max_length=512),
                ),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="admin_activity_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="adminactivitylog",
            index=models.Index(
                fields=["-created_at", "id"], name="admin_audit_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="adminactivitylog",
            index=models.Index(
                fields=["actor", "-created_at"], name="admin_audit_actor_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="adminactivitylog",
            index=models.Index(
                fields=["channel", "-created_at"], name="admin_audit_channel_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="adminactivitylog",
            index=models.Index(
                fields=["action_group", "-created_at"], name="admin_audit_action_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="adminactivitylog",
            index=models.Index(
                fields=["http_status", "-created_at"], name="admin_audit_status_idx"
            ),
        ),
    ]
