from __future__ import annotations

from rest_framework import serializers

from .models import AdminActivityLog


class AdminActivityLogSerializer(serializers.ModelSerializer):
    actor_id = serializers.IntegerField(
        source="actor.id", read_only=True, allow_null=True
    )

    class Meta:
        model = AdminActivityLog
        fields = [
            "id",
            "request_id",
            "created_at",
            "actor_id",
            "actor_username",
            "actor_is_staff",
            "actor_is_superuser",
            "channel",
            "method",
            "path",
            "query_string",
            "action_group",
            "resource",
            "http_status",
            "is_success",
            "duration_ms",
            "ip_address",
            "origin",
            "referer",
            "user_agent",
            "metadata",
        ]
