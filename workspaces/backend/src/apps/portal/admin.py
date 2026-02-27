from django.contrib import admin

from .models import PortalConfig, PortalSection


@admin.register(PortalConfig)
class PortalConfigAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "active_template",
        "admin_active_template",
        "site_name",
        "is_published",
        "updated_at",
    )
    search_fields = (
        "site_name",
        "site_title",
        "active_template",
        "admin_active_template",
    )


@admin.register(PortalSection)
class PortalSectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "template_id",
        "page",
        "key",
        "is_enabled",
        "sort_order",
        "updated_at",
    )
    list_filter = ("template_id", "page", "is_enabled")
    search_fields = ("key", "title")
