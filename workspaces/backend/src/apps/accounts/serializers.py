from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .customer_services import (
    apply_customer_consents,
    ensure_customer_governance_profile,
)
from .models import Role, UserProfile, UserTask, UserTaskCategory
from .services import (
    SystemRole,
    assign_admin_modules_to_user,
    assign_roles_to_user,
    assign_tasks_to_user,
    build_user_account_compliance,
    get_allowed_admin_module_slugs,
    get_user_admin_module_permissions,
    get_user_role_codes,
    get_user_task_category_codes,
    get_user_task_codes,
    register_user_with_default_role,
    user_can_access_technical_admin,
)
from .validators import (
    is_valid_cnpj_document,
    is_valid_cpf_document,
    is_valid_phone_document,
    normalize_digits,
    normalize_phone_digits,
    normalize_postal_code,
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
    email_verified = serializers.SerializerMethodField()
    email_verified_at = serializers.SerializerMethodField()
    essential_profile_complete = serializers.SerializerMethodField()
    missing_essential_profile_fields = serializers.SerializerMethodField()
    allowed_admin_module_slugs = serializers.SerializerMethodField()
    module_permissions = serializers.SerializerMethodField()
    can_access_technical_admin = serializers.SerializerMethodField()

    def get_roles(self, obj):
        return sorted(get_user_role_codes(obj))

    def _compliance_payload(self, obj) -> dict:
        cached = getattr(obj, "_accounts_compliance_payload", None)
        if isinstance(cached, dict):
            return cached
        payload = build_user_account_compliance(obj)
        obj._accounts_compliance_payload = payload
        return payload

    def get_email_verified(self, obj):
        return self._compliance_payload(obj)["email_verified"]

    def get_email_verified_at(self, obj):
        return self._compliance_payload(obj)["email_verified_at"]

    def get_essential_profile_complete(self, obj):
        return self._compliance_payload(obj)["essential_profile_complete"]

    def get_missing_essential_profile_fields(self, obj):
        return self._compliance_payload(obj)["missing_essential_profile_fields"]

    def get_allowed_admin_module_slugs(self, obj):
        return get_allowed_admin_module_slugs(obj)

    def get_module_permissions(self, obj):
        return get_user_admin_module_permissions(obj)

    def get_can_access_technical_admin(self, obj):
        return user_can_access_technical_admin(obj)


class MeAccountUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate_username(self, value: str) -> str:
        username = str(value or "").strip()
        if not username:
            raise serializers.ValidationError("Informe um nome de usuario valido.")

        user = self.context.get("user")
        User = get_user_model()
        qs = User.objects.filter(username=username)
        if user is not None:
            qs = qs.exclude(pk=user.pk)
        if qs.exists():
            raise serializers.ValidationError("Nome de usuario ja cadastrado.")
        return username

    def validate_password(self, value: str) -> str:
        password = str(value or "")
        if not password:
            return ""
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

    def apply(self, *, user):
        updates: list[str] = []
        for field_name in ("username", "email", "first_name", "last_name"):
            if field_name not in self.validated_data:
                continue
            value = self.validated_data[field_name]
            if isinstance(value, str):
                value = value.strip()
            if getattr(user, field_name) == value:
                continue
            setattr(user, field_name, value)
            updates.append(field_name)

        password = self.validated_data.get("password", None)
        if isinstance(password, str) and password:
            user.set_password(password)
            updates.append("password")

        if updates:
            if "password" in updates:
                user.save()
            else:
                user.save(update_fields=updates)
        return user


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
    email_verified = serializers.SerializerMethodField()
    email_verified_at = serializers.SerializerMethodField()
    email_verification_last_sent_at = serializers.SerializerMethodField()
    essential_profile_complete = serializers.SerializerMethodField()
    missing_essential_profile_fields = serializers.SerializerMethodField()
    task_codes = serializers.SerializerMethodField()
    task_category_codes = serializers.SerializerMethodField()
    allowed_admin_module_slugs = serializers.SerializerMethodField()
    module_permissions = serializers.SerializerMethodField()
    can_access_technical_admin = serializers.SerializerMethodField()

    def get_roles(self, obj):
        return sorted(get_user_role_codes(obj))

    def _compliance_payload(self, obj) -> dict:
        cached = getattr(obj, "_accounts_compliance_payload", None)
        if isinstance(cached, dict):
            return cached
        payload = build_user_account_compliance(obj)
        obj._accounts_compliance_payload = payload
        return payload

    def get_email_verified(self, obj):
        return self._compliance_payload(obj)["email_verified"]

    def get_email_verified_at(self, obj):
        return self._compliance_payload(obj)["email_verified_at"]

    def get_email_verification_last_sent_at(self, obj):
        return self._compliance_payload(obj)["email_verification_last_sent_at"]

    def get_essential_profile_complete(self, obj):
        return self._compliance_payload(obj)["essential_profile_complete"]

    def get_missing_essential_profile_fields(self, obj):
        return self._compliance_payload(obj)["missing_essential_profile_fields"]

    def get_task_codes(self, obj):
        return sorted(get_user_task_codes(obj))

    def get_task_category_codes(self, obj):
        return sorted(get_user_task_category_codes(obj))

    def get_allowed_admin_module_slugs(self, obj):
        return get_allowed_admin_module_slugs(obj)

    def get_module_permissions(self, obj):
        return get_user_admin_module_permissions(obj)

    def get_can_access_technical_admin(self, obj):
        return user_can_access_technical_admin(obj)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=8, write_only=True)
    email = serializers.EmailField(required=True, allow_blank=False)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    accepted_terms = serializers.BooleanField(required=False)
    accepted_privacy_policy = serializers.BooleanField(required=False)
    marketing_opt_in = serializers.BooleanField(required=False)
    notifications_opt_in = serializers.BooleanField(required=False)

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
        accepted_terms = bool(validated_data.pop("accepted_terms", False))
        accepted_privacy_policy = bool(
            validated_data.pop("accepted_privacy_policy", False)
        )
        marketing_opt_in = validated_data.pop("marketing_opt_in", None)
        notifications_opt_in = validated_data.pop("notifications_opt_in", None)
        try:
            user = register_user_with_default_role(**validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

        apply_customer_consents(
            customer=user,
            accepted_terms=accepted_terms,
            accepted_privacy_policy=accepted_privacy_policy,
            marketing_opt_in=marketing_opt_in,
            notifications_opt_in=notifications_opt_in,
        )

        return user


class TokenObtainPairEmailVerifiedSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        if user.is_superuser or user.is_staff:
            return data

        role_codes = get_user_role_codes(user)
        if SystemRole.CLIENTE not in role_codes:
            return data

        management_roles = {
            SystemRole.ADMIN,
            SystemRole.FINANCEIRO,
            SystemRole.COZINHA,
            SystemRole.COMPRAS,
            SystemRole.ESTOQUE,
        }
        if role_codes.intersection(management_roles):
            return data

        if getattr(settings, "DEBUG", False):
            governance = ensure_customer_governance_profile(user=user)
            if not governance.email_login_allowed_dev:
                raise AuthenticationFailed(
                    "Acesso via e-mail bloqueado em modo dev para esta conta.",
                    code="email_blocked_dev",
                )

        profile, _created = UserProfile.objects.get_or_create(user=user)
        if profile.email_verified_at is not None:
            return data

        raise AuthenticationFailed(
            "Conta nao validada. Verifique seu e-mail (incluindo caixa de spam) "
            "ou solicite novo token de validacao.",
            code="email_not_verified",
        )


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


class AssignTasksSerializer(serializers.Serializer):
    task_codes = serializers.ListField(
        child=serializers.CharField(max_length=64),
        allow_empty=True,
    )
    replace = serializers.BooleanField(required=False, default=True)

    def validate_task_codes(self, value: list[str]) -> list[str]:
        normalized_codes: list[str] = []
        for code in value:
            normalized_code = str(code or "").strip().upper()
            if not normalized_code:
                continue
            if normalized_code not in normalized_codes:
                normalized_codes.append(normalized_code)
        return normalized_codes

    def apply(self, *, user, assigned_by=None):
        try:
            return assign_tasks_to_user(
                user=user,
                task_codes=self.validated_data["task_codes"],
                replace=self.validated_data.get("replace", True),
                assigned_by=assigned_by,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc


class AdminModulePermissionInputSerializer(serializers.Serializer):
    module_slug = serializers.CharField(max_length=64)
    access_level = serializers.ChoiceField(choices=("read", "write"))


class AdminUserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=8, write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    is_active = serializers.BooleanField(required=False, default=True)
    is_staff = serializers.BooleanField(required=False, default=False)
    role_codes = serializers.ListField(
        child=serializers.ChoiceField(choices=SystemRole.ALL),
        allow_empty=False,
    )
    task_codes = serializers.ListField(
        child=serializers.CharField(max_length=64),
        allow_empty=True,
        required=False,
        default=list,
    )
    module_permissions = AdminModulePermissionInputSerializer(
        many=True,
        required=False,
        default=list,
    )

    def validate_username(self, value: str) -> str:
        User = get_user_model()
        username = str(value or "").strip()
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

    def validate_role_codes(self, value: list[str]) -> list[str]:
        normalized_codes: list[str] = []
        for code in value:
            normalized_code = str(code or "").strip().upper()
            if normalized_code and normalized_code not in normalized_codes:
                normalized_codes.append(normalized_code)
        if not normalized_codes:
            raise serializers.ValidationError("Informe ao menos um papel.")
        return normalized_codes

    def validate_task_codes(self, value: list[str]) -> list[str]:
        normalized_codes: list[str] = []
        for code in value:
            normalized_code = str(code or "").strip().upper()
            if normalized_code and normalized_code not in normalized_codes:
                normalized_codes.append(normalized_code)
        return normalized_codes

    def create(self, validated_data):
        User = get_user_model()

        role_codes = validated_data.pop("role_codes", [])
        task_codes = validated_data.pop("task_codes", [])
        module_permissions = validated_data.pop("module_permissions", [])
        password = validated_data.pop("password")
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=validated_data["username"],
                    password=password,
                    email=str(validated_data.get("email", "") or "").strip(),
                    first_name=str(validated_data.get("first_name", "") or "").strip(),
                    last_name=str(validated_data.get("last_name", "") or "").strip(),
                    is_active=bool(validated_data.get("is_active", True)),
                    is_staff=bool(validated_data.get("is_staff", False)),
                )
                assign_roles_to_user(user=user, role_codes=role_codes, replace=True)
                assign_tasks_to_user(user=user, task_codes=task_codes, replace=True)
                assign_admin_modules_to_user(
                    user=user,
                    module_permissions=module_permissions,
                    replace=True,
                    assigned_by=self.context.get("request_user"),
                )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return user


class AdminUserUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    module_permissions = AdminModulePermissionInputSerializer(
        many=True,
        required=False,
    )

    def validate_username(self, value: str) -> str:
        username = str(value or "").strip()
        if not username:
            raise serializers.ValidationError("Informe um nome de usuario valido.")

        user = self.context.get("user")
        User = get_user_model()
        qs = User.objects.filter(username=username)
        if user is not None:
            qs = qs.exclude(pk=user.pk)
        if qs.exists():
            raise serializers.ValidationError("Nome de usuario ja cadastrado.")
        return username

    def validate_password(self, value: str) -> str:
        password = str(value or "")
        if not password:
            return ""
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

    def apply(self, *, user):
        updates: list[str] = []
        for field_name in (
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
        ):
            if field_name not in self.validated_data:
                continue
            value = self.validated_data[field_name]
            if isinstance(value, str):
                value = value.strip()
            if getattr(user, field_name) == value:
                continue
            setattr(user, field_name, value)
            updates.append(field_name)

        password = self.validated_data.get("password", None)
        if isinstance(password, str) and password:
            user.set_password(password)
            updates.append("password")

        if "module_permissions" in self.validated_data:
            try:
                assign_admin_modules_to_user(
                    user=user,
                    module_permissions=self.validated_data.get("module_permissions", []),
                    replace=True,
                    assigned_by=self.context.get("request_user"),
                )
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages) from exc

        if updates:
            if "password" in updates:
                user.save()
            else:
                user.save(update_fields=updates)

        return user


class UserTaskSerializer(serializers.ModelSerializer):
    category_code = serializers.CharField(source="category.code", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = UserTask
        fields = [
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "technical_scope",
            "related_module_slug",
            "category_code",
            "category_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UserTaskCategorySerializer(serializers.ModelSerializer):
    tasks = UserTaskSerializer(many=True, read_only=True)

    class Meta:
        model = UserTaskCategory
        fields = [
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "technical_scope",
            "tasks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


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
            "phone_is_whatsapp",
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
            "email_verified_at",
            "email_verification_last_sent_at",
            "email_verification_last_client_base_url",
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
            "email_verified_at",
            "email_verification_last_sent_at",
            "email_verification_last_client_base_url",
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
        normalized = normalize_digits(value)
        if normalized and not is_valid_cpf_document(normalized):
            raise serializers.ValidationError(
                "CPF invalido. Informe um documento valido (11 digitos com DV)."
            )
        return normalized

    def validate_cnpj(self, value: str) -> str:
        normalized = normalize_digits(value)
        if normalized and not is_valid_cnpj_document(normalized):
            raise serializers.ValidationError(
                "CNPJ invalido. Informe um documento valido (14 digitos com DV)."
            )
        return normalized

    def validate_postal_code(self, value: str) -> str:
        normalized = normalize_postal_code(value)
        if normalized and len(normalized) not in {8}:
            raise serializers.ValidationError("CEP invalido. Informe 8 digitos.")
        return normalized

    def validate_phone(self, value: str) -> str:
        normalized = normalize_phone_digits(value)
        if normalized and not is_valid_phone_document(normalized):
            raise serializers.ValidationError(
                "Telefone invalido. Informe DDD + numero com 10 ou 11 digitos."
            )
        return normalized

    def validate_secondary_phone(self, value: str) -> str:
        normalized = normalize_phone_digits(value)
        if normalized and not is_valid_phone_document(normalized):
            raise serializers.ValidationError(
                "Telefone secundario invalido. "
                "Informe DDD + numero com 10 ou 11 digitos."
            )
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


class EmailVerificationConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, allow_blank=False)


class EmailVerificationResendSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=False, allow_blank=True, max_length=150)
    preferred_client_base_url = serializers.URLField(required=False, allow_blank=True)


class CepLookupSerializer(serializers.Serializer):
    cep = serializers.CharField(required=True, allow_blank=False, max_length=16)

    def validate_cep(self, value: str) -> str:
        normalized = normalize_postal_code(value)
        if len(normalized) != 8:
            raise serializers.ValidationError("CEP invalido. Informe 8 digitos.")
        return normalized
