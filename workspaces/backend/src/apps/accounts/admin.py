from django.contrib import admin

from .models import (
    CustomerGovernanceProfile,
    CustomerLgpdRequest,
    Role,
    UserProfile,
    UserRole,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "role__code")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
        "phone",
        "city",
        "state",
        "biometric_status",
        "updated_at",
    )
    list_filter = ("biometric_status", "state", "city")
    search_fields = (
        "user__username",
        "user__email",
        "full_name",
        "phone",
        "cpf",
        "cnpj",
    )


@admin.register(CustomerGovernanceProfile)
class CustomerGovernanceProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "account_status",
        "checkout_blocked",
        "kyc_review_status",
        "updated_at",
    )
    list_filter = ("account_status", "checkout_blocked", "kyc_review_status")
    search_fields = ("user__username", "user__email", "account_status_reason")


@admin.register(CustomerLgpdRequest)
class CustomerLgpdRequestAdmin(admin.ModelAdmin):
    list_display = (
        "protocol_code",
        "customer",
        "request_type",
        "status",
        "channel",
        "requested_at",
        "due_at",
    )
    list_filter = ("request_type", "status", "channel")
    search_fields = (
        "protocol_code",
        "customer__username",
        "customer__email",
        "requested_by_name",
    )
