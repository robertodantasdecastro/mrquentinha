from rest_framework import serializers

from .models import PortalConfig, PortalPage, PortalSection


class PortalConfigAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalConfig
        fields = [
            "id",
            "active_template",
            "available_templates",
            "client_active_template",
            "client_available_templates",
            "site_name",
            "site_title",
            "meta_description",
            "primary_color",
            "secondary_color",
            "dark_bg_color",
            "android_download_url",
            "ios_download_url",
            "qr_target_url",
            "is_published",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)

        instance = getattr(self, "instance", None)
        available_templates = attrs.get(
            "available_templates",
            getattr(instance, "available_templates", []),
        )
        active_template = attrs.get(
            "active_template",
            getattr(instance, "active_template", ""),
        )
        client_available_templates = attrs.get(
            "client_available_templates",
            getattr(instance, "client_available_templates", []),
        )
        client_active_template = attrs.get(
            "client_active_template",
            getattr(instance, "client_active_template", ""),
        )

        template_ids: set[str] = set()
        for item in available_templates:
            if isinstance(item, dict):
                template_id = str(item.get("id", "")).strip()
            else:
                template_id = str(item).strip()
            if template_id:
                template_ids.add(template_id)

        if template_ids and active_template not in template_ids:
            raise serializers.ValidationError(
                "active_template precisa existir em available_templates."
            )

        client_template_ids: set[str] = set()
        for item in client_available_templates:
            if isinstance(item, dict):
                template_id = str(item.get("id", "")).strip()
            else:
                template_id = str(item).strip()
            if template_id:
                client_template_ids.add(template_id)

        if client_template_ids and client_active_template not in client_template_ids:
            raise serializers.ValidationError(
                "client_active_template precisa existir em client_available_templates."
            )

        return attrs


class PortalSectionAdminSerializer(serializers.ModelSerializer):
    page = serializers.ChoiceField(choices=PortalPage.choices)

    class Meta:
        model = PortalSection
        fields = [
            "id",
            "config",
            "template_id",
            "page",
            "key",
            "title",
            "body_json",
            "is_enabled",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PortalPublicSectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    template_id = serializers.CharField()
    page = serializers.CharField()
    key = serializers.CharField()
    title = serializers.CharField()
    body_json = serializers.JSONField()
    sort_order = serializers.IntegerField()
    updated_at = serializers.DateTimeField()


class PortalPublicConfigSerializer(serializers.Serializer):
    channel = serializers.CharField()
    active_template = serializers.CharField()
    available_templates = serializers.JSONField()
    client_active_template = serializers.CharField()
    client_available_templates = serializers.JSONField()
    site_name = serializers.CharField()
    site_title = serializers.CharField()
    meta_description = serializers.CharField()
    primary_color = serializers.CharField()
    secondary_color = serializers.CharField()
    dark_bg_color = serializers.CharField()
    android_download_url = serializers.CharField()
    ios_download_url = serializers.CharField()
    qr_target_url = serializers.CharField()
    is_published = serializers.BooleanField()
    updated_at = serializers.DateTimeField()
    page = serializers.CharField()
    sections = PortalPublicSectionSerializer(many=True)


class PortalVersionSerializer(serializers.Serializer):
    updated_at = serializers.DateTimeField(allow_null=True)
    hash = serializers.CharField()
    etag = serializers.CharField()
