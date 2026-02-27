from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import Role, UserProfile
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


class UserAdminSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True, allow_blank=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
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

    def validate_password(self, value: str) -> str:
        password = value or ""
        if len(password) < 8:
            raise serializers.ValidationError("Senha deve ter ao menos 8 caracteres.")

        has_lower = any(char.islower() for char in password)
        has_upper = any(char.isupper() for char in password)
        has_digit = any(char.isdigit() for char in password)

        if not (has_lower and has_upper and has_digit):
            raise serializers.ValidationError(
                "Senha deve conter letra maiuscula, minuscula e numero."
            )

        return password

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


def _normalize_digits(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


class UserProfileSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()
    document_front_image_url = serializers.SerializerMethodField()
    document_back_image_url = serializers.SerializerMethodField()
    document_selfie_image_url = serializers.SerializerMethodField()
    biometric_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "full_name",
            "preferred_name",
            "phone",
            "secondary_phone",
            "birth_date",
            "cpf",
            "cnpj",
            "rg",
            "occupation",
            "postal_code",
            "street",
            "street_number",
            "address_complement",
            "neighborhood",
            "city",
            "state",
            "country",
            "document_type",
            "document_number",
            "document_issuer",
            "profile_photo",
            "profile_photo_url",
            "document_front_image",
            "document_front_image_url",
            "document_back_image",
            "document_back_image_url",
            "document_selfie_image",
            "document_selfie_image_url",
            "biometric_photo",
            "biometric_photo_url",
            "biometric_status",
            "biometric_captured_at",
            "biometric_verified_at",
            "notes",
            "extra_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "profile_photo_url",
            "document_front_image_url",
            "document_back_image_url",
            "document_selfie_image_url",
            "biometric_photo_url",
            "biometric_status",
            "biometric_captured_at",
            "biometric_verified_at",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "profile_photo": {"required": False, "allow_null": True},
            "document_front_image": {"required": False, "allow_null": True},
            "document_back_image": {"required": False, "allow_null": True},
            "document_selfie_image": {"required": False, "allow_null": True},
            "biometric_photo": {"required": False, "allow_null": True},
            "document_type": {"required": False, "allow_blank": True},
        }

    def _build_file_url(self, value) -> str | None:
        if not value:
            return None

        request = self.context.get("request")
        url = value.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_profile_photo_url(self, obj):
        return self._build_file_url(obj.profile_photo)

    def get_document_front_image_url(self, obj):
        return self._build_file_url(obj.document_front_image)

    def get_document_back_image_url(self, obj):
        return self._build_file_url(obj.document_back_image)

    def get_document_selfie_image_url(self, obj):
        return self._build_file_url(obj.document_selfie_image)

    def get_biometric_photo_url(self, obj):
        return self._build_file_url(obj.biometric_photo)

    def validate_cpf(self, value: str) -> str:
        normalized = _normalize_digits(value)
        if normalized and len(normalized) != 11:
            raise serializers.ValidationError("CPF invalido. Informe 11 digitos.")
        return normalized

    def validate_cnpj(self, value: str) -> str:
        normalized = _normalize_digits(value)
        if normalized and len(normalized) != 14:
            raise serializers.ValidationError("CNPJ invalido. Informe 14 digitos.")
        return normalized

    def validate_postal_code(self, value: str) -> str:
        normalized = _normalize_digits(value)
        if normalized and len(normalized) not in {8}:
            raise serializers.ValidationError("CEP invalido. Informe 8 digitos.")
        return normalized

    def update(self, instance: UserProfile, validated_data):
        biometric_photo = validated_data.get("biometric_photo", serializers.empty)
        if biometric_photo is not serializers.empty:
            if biometric_photo:
                instance.biometric_status = UserProfile.BiometricStatus.PENDING_REVIEW
                instance.biometric_captured_at = timezone.now()
                instance.biometric_verified_at = None
            else:
                instance.biometric_status = UserProfile.BiometricStatus.NOT_CONFIGURED
                instance.biometric_captured_at = None
                instance.biometric_verified_at = None

        return super().update(instance, validated_data)
