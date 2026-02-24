from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Role
from .services import (
    SystemRole,
    assign_roles_to_user,
    get_user_role_codes,
    register_user_with_default_role,
)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    roles = serializers.SerializerMethodField()

    def get_roles(self, obj):
        return sorted(get_user_role_codes(obj))


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=8, write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_username(self, value: str) -> str:
        User = get_user_model()
        username = value.strip()

        if not username:
            raise serializers.ValidationError("Informe um nome de usuario valido.")

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Nome de usuario ja cadastrado.")

        return username

    def create(self, validated_data):
        try:
            user = register_user_with_default_role(**validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

        return user


class AssignRolesSerializer(serializers.Serializer):
    role_codes = serializers.ListField(
        child=serializers.ChoiceField(choices=SystemRole.ALL),
        allow_empty=False,
    )
    replace = serializers.BooleanField(required=False, default=True)

    def validate_role_codes(self, value: list[str]) -> list[str]:
        normalized_codes: list[str] = []
        for code in value:
            normalized_code = code.strip().upper()
            if normalized_code not in normalized_codes:
                normalized_codes.append(normalized_code)

        if not normalized_codes:
            raise serializers.ValidationError("Informe ao menos um papel.")

        return normalized_codes

    def apply(self, *, user):
        try:
            return assign_roles_to_user(
                user=user,
                role_codes=self.validated_data["role_codes"],
                replace=self.validated_data.get("replace", True),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
