from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from .models import CustomerGovernanceProfile, CustomerLgpdRequest, UserProfile
from .services import build_user_account_compliance, get_user_role_codes


class CustomerProfileAdminSerializer(serializers.ModelSerializer):
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
            "email_verification_last_sent_at",
            "email_verification_last_client_base_url",
            "created_at",
            "updated_at",
        ]

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

    def update(self, instance: UserProfile, validated_data):
        biometric_status = validated_data.get("biometric_status")
        if biometric_status == UserProfile.BiometricStatus.VERIFIED:
            validated_data["biometric_verified_at"] = timezone.now()
        elif biometric_status == UserProfile.BiometricStatus.REJECTED:
            validated_data["biometric_verified_at"] = None

        return super().update(instance, validated_data)


class CustomerGovernanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerGovernanceProfile
        fields = [
            "id",
            "user",
            "account_status",
            "account_status_reason",
            "checkout_blocked",
            "checkout_block_reason",
            "terms_accepted_at",
            "privacy_policy_accepted_at",
            "marketing_opt_in_at",
            "marketing_opt_out_at",
            "lgpd_data_export_last_at",
            "lgpd_data_anonymized_at",
            "kyc_review_status",
            "kyc_review_notes",
            "reviewed_by",
            "reviewed_at",
            "extra_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "terms_accepted_at",
            "privacy_policy_accepted_at",
            "marketing_opt_in_at",
            "marketing_opt_out_at",
            "lgpd_data_export_last_at",
            "lgpd_data_anonymized_at",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class CustomerLgpdRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerLgpdRequest
        fields = [
            "id",
            "customer",
            "protocol_code",
            "request_type",
            "status",
            "channel",
            "requested_by_name",
            "requested_by_email",
            "requested_at",
            "due_at",
            "notes",
            "request_payload",
            "resolution_notes",
            "resolved_at",
            "resolved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "protocol_code",
            "status",
            "requested_at",
            "due_at",
            "resolution_notes",
            "resolved_at",
            "resolved_by",
            "created_at",
            "updated_at",
        ]


class CustomerListSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True, allow_blank=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    roles = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    cpf = serializers.SerializerMethodField()
    cnpj = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    email_verified_at = serializers.SerializerMethodField()
    essential_profile_complete = serializers.SerializerMethodField()
    missing_essential_profile_fields = serializers.SerializerMethodField()
    account_status = serializers.SerializerMethodField()
    checkout_blocked = serializers.SerializerMethodField()
    kyc_review_status = serializers.SerializerMethodField()
    orders_count = serializers.IntegerField(read_only=True)
    orders_received_count = serializers.IntegerField(read_only=True)
    orders_total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    last_order_at = serializers.DateTimeField(read_only=True)

    def get_roles(self, obj):
        return sorted(get_user_role_codes(obj))

    def _profile(self, obj):
        return getattr(obj, "profile", None)

    def _governance(self, obj):
        return getattr(obj, "customer_governance", None)

    def _compliance_payload(self, obj) -> dict:
        cached = getattr(obj, "_accounts_compliance_payload", None)
        if isinstance(cached, dict):
            return cached
        payload = build_user_account_compliance(obj)
        obj._accounts_compliance_payload = payload
        return payload

    def get_full_name(self, obj):
        profile = self._profile(obj)
        if profile and profile.full_name:
            return profile.full_name
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name

    def get_phone(self, obj):
        profile = self._profile(obj)
        return profile.phone if profile else ""

    def get_city(self, obj):
        profile = self._profile(obj)
        return profile.city if profile else ""

    def get_state(self, obj):
        profile = self._profile(obj)
        return profile.state if profile else ""

    def get_cpf(self, obj):
        profile = self._profile(obj)
        return profile.cpf if profile else ""

    def get_cnpj(self, obj):
        profile = self._profile(obj)
        return profile.cnpj if profile else ""

    def get_email_verified(self, obj):
        return self._compliance_payload(obj)["email_verified"]

    def get_email_verified_at(self, obj):
        return self._compliance_payload(obj)["email_verified_at"]

    def get_essential_profile_complete(self, obj):
        return self._compliance_payload(obj)["essential_profile_complete"]

    def get_missing_essential_profile_fields(self, obj):
        return self._compliance_payload(obj)["missing_essential_profile_fields"]

    def get_account_status(self, obj):
        governance = self._governance(obj)
        if governance is None:
            return CustomerGovernanceProfile.AccountStatus.ACTIVE
        return governance.account_status

    def get_checkout_blocked(self, obj):
        governance = self._governance(obj)
        if governance is None:
            return False
        return bool(governance.checkout_blocked)

    def get_kyc_review_status(self, obj):
        governance = self._governance(obj)
        if governance is None:
            return CustomerGovernanceProfile.KycReviewStatus.PENDING
        return governance.kyc_review_status


class CustomerDetailSerializer(CustomerListSerializer):
    profile = serializers.SerializerMethodField()
    governance = serializers.SerializerMethodField()

    def get_profile(self, obj):
        profile = getattr(obj, "profile", None)
        if profile is None:
            return None
        return CustomerProfileAdminSerializer(profile, context=self.context).data

    def get_governance(self, obj):
        governance = getattr(obj, "customer_governance", None)
        if governance is None:
            return None
        return CustomerGovernanceSerializer(governance).data


class CustomerAccountStatusSerializer(serializers.Serializer):
    account_status = serializers.ChoiceField(
        choices=CustomerGovernanceProfile.AccountStatus.choices,
    )
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class CustomerConsentsUpdateSerializer(serializers.Serializer):
    accepted_terms = serializers.BooleanField(required=False, allow_null=True)
    accepted_privacy_policy = serializers.BooleanField(required=False, allow_null=True)
    marketing_opt_in = serializers.BooleanField(required=False, allow_null=True)


class CustomerLgpdRequestCreateSerializer(serializers.Serializer):
    request_type = serializers.ChoiceField(
        choices=CustomerLgpdRequest.RequestType.choices
    )
    channel = serializers.ChoiceField(
        choices=CustomerLgpdRequest.RequestChannel.choices,
        default=CustomerLgpdRequest.RequestChannel.WEB,
    )
    requested_by_name = serializers.CharField(
        required=False, allow_blank=True, max_length=180
    )
    requested_by_email = serializers.EmailField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    request_payload = serializers.JSONField(required=False)


class CustomerLgpdRequestStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=CustomerLgpdRequest.RequestStatus.choices)
    resolution_notes = serializers.CharField(required=False, allow_blank=True)
