from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from .models import MobileRelease, PortalConfig, PortalPage, PortalSection


class PortalConfigAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalConfig
        fields = [
            "id",
            "active_template",
            "available_templates",
            "client_active_template",
            "client_available_templates",
            "admin_active_template",
            "admin_available_templates",
            "site_name",
            "site_title",
            "meta_description",
            "primary_color",
            "secondary_color",
            "dark_bg_color",
            "android_download_url",
            "ios_download_url",
            "qr_target_url",
            "api_base_url",
            "local_hostname",
            "local_network_ip",
            "root_domain",
            "portal_domain",
            "client_domain",
            "admin_domain",
            "api_domain",
            "portal_base_url",
            "client_base_url",
            "admin_base_url",
            "backend_base_url",
            "proxy_base_url",
            "cors_allowed_origins",
            "cloudflare_settings",
            "auth_providers",
            "payment_providers",
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
        admin_available_templates = attrs.get(
            "admin_available_templates",
            getattr(instance, "admin_available_templates", []),
        )
        admin_active_template = attrs.get(
            "admin_active_template",
            getattr(instance, "admin_active_template", ""),
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

        admin_template_ids: set[str] = set()
        for item in admin_available_templates:
            if isinstance(item, dict):
                template_id = str(item.get("id", "")).strip()
            else:
                template_id = str(item).strip()
            if template_id:
                admin_template_ids.add(template_id)

        if admin_template_ids and admin_active_template not in admin_template_ids:
            raise serializers.ValidationError(
                "admin_active_template precisa existir em admin_available_templates."
            )

        payment_providers = attrs.get(
            "payment_providers",
            getattr(instance, "payment_providers", {}),
        )
        if isinstance(payment_providers, dict):
            receiver = payment_providers.get("receiver", {})
            if isinstance(receiver, dict):
                person_type = (
                    str(receiver.get("person_type", "CNPJ")).strip().upper() or "CNPJ"
                )
                document = "".join(
                    char
                    for char in str(receiver.get("document", "")).strip()
                    if char.isdigit()
                )
                email = str(receiver.get("email", "")).strip()

                if person_type == "CPF" and document and len(document) != 11:
                    raise serializers.ValidationError(
                        "Documento do recebedor invalido para CPF (11 digitos)."
                    )

                if person_type == "CNPJ" and document and len(document) != 14:
                    raise serializers.ValidationError(
                        "Documento do recebedor invalido para CNPJ (14 digitos)."
                    )

                if email:
                    try:
                        validate_email(email)
                    except DjangoValidationError as exc:
                        raise serializers.ValidationError(
                            "Email do recebedor invalido."
                        ) from exc

                receiver["person_type"] = person_type
                receiver["document"] = document
                receiver["email"] = email
                payment_providers["receiver"] = receiver
                attrs["payment_providers"] = payment_providers

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
    admin_active_template = serializers.CharField()
    admin_available_templates = serializers.JSONField()
    site_name = serializers.CharField()
    site_title = serializers.CharField()
    meta_description = serializers.CharField()
    primary_color = serializers.CharField()
    secondary_color = serializers.CharField()
    dark_bg_color = serializers.CharField()
    android_download_url = serializers.CharField()
    ios_download_url = serializers.CharField()
    qr_target_url = serializers.CharField()
    api_base_url = serializers.CharField()
    local_hostname = serializers.CharField()
    local_network_ip = serializers.CharField()
    root_domain = serializers.CharField()
    portal_domain = serializers.CharField()
    client_domain = serializers.CharField()
    admin_domain = serializers.CharField()
    api_domain = serializers.CharField()
    portal_base_url = serializers.CharField()
    client_base_url = serializers.CharField()
    admin_base_url = serializers.CharField()
    backend_base_url = serializers.CharField()
    proxy_base_url = serializers.CharField()
    cors_allowed_origins = serializers.JSONField()
    cloudflare = serializers.JSONField()
    auth_providers = serializers.JSONField()
    payment_providers = serializers.JSONField()
    host_publico = serializers.CharField()
    app_download_android_url = serializers.CharField()
    app_download_ios_url = serializers.CharField()
    is_published = serializers.BooleanField()
    updated_at = serializers.DateTimeField()
    page = serializers.CharField()
    sections = PortalPublicSectionSerializer(many=True)


class PortalVersionSerializer(serializers.Serializer):
    updated_at = serializers.DateTimeField(allow_null=True)
    hash = serializers.CharField()
    etag = serializers.CharField()


class MobileReleaseAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileRelease
        fields = [
            "id",
            "config",
            "release_version",
            "build_number",
            "status",
            "update_policy",
            "is_critical_update",
            "min_supported_version",
            "recommended_version",
            "api_base_url_snapshot",
            "host_publico_snapshot",
            "android_relative_path",
            "ios_relative_path",
            "android_download_url",
            "ios_download_url",
            "android_checksum_sha256",
            "ios_checksum_sha256",
            "release_notes",
            "build_log",
            "metadata",
            "published_at",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "api_base_url_snapshot",
            "host_publico_snapshot",
            "android_download_url",
            "ios_download_url",
            "android_checksum_sha256",
            "ios_checksum_sha256",
            "build_log",
            "published_at",
            "created_by",
            "created_at",
            "updated_at",
        ]


class MobileReleaseLatestSerializer(serializers.Serializer):
    release_version = serializers.CharField()
    build_number = serializers.IntegerField()
    status = serializers.CharField()
    update_policy = serializers.CharField()
    is_critical_update = serializers.BooleanField()
    min_supported_version = serializers.CharField()
    recommended_version = serializers.CharField()
    api_base_url = serializers.CharField()
    host_publico = serializers.CharField()
    android_download_url = serializers.CharField()
    ios_download_url = serializers.CharField()
    published_at = serializers.DateTimeField(allow_null=True)
    release_notes = serializers.CharField()
