from django.contrib import admin

from .models import Role, UserProfile, UserRole


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
