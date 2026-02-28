from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class AdminActivityLog(models.Model):
    request_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_activity_logs",
    )
    actor_username = models.CharField(
        max_length=150, blank=True, default="", db_index=True
    )
    actor_is_staff = models.BooleanField(default=False)
    actor_is_superuser = models.BooleanField(default=False)

    channel = models.CharField(max_length=32, default="unknown", db_index=True)
    method = models.CharField(max_length=8, db_index=True)
    path = models.CharField(max_length=255, db_index=True)
    query_string = models.TextField(blank=True, default="")
    action_group = models.CharField(
        max_length=64, blank=True, default="", db_index=True
    )
    resource = models.CharField(max_length=128, blank=True, default="", db_index=True)

    http_status = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_success = models.BooleanField(default=True, db_index=True)
    duration_ms = models.PositiveIntegerField(default=0)

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    origin = models.CharField(max_length=255, blank=True, default="")
    referer = models.TextField(blank=True, default="")
    user_agent = models.CharField(max_length=512, blank=True, default="")

    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["-created_at", "id"], name="admin_audit_created_idx"),
            models.Index(fields=["actor", "-created_at"], name="admin_audit_actor_idx"),
            models.Index(
                fields=["channel", "-created_at"], name="admin_audit_channel_idx"
            ),
            models.Index(
                fields=["action_group", "-created_at"], name="admin_audit_action_idx"
            ),
            models.Index(
                fields=["http_status", "-created_at"], name="admin_audit_status_idx"
            ),
        ]

    def __str__(self) -> str:
        actor = self.actor_username or "anonimo"
        return (
            f"[{self.created_at.isoformat()}] {actor} "
            f"{self.method} {self.path} ({self.http_status})"
        )
