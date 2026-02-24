from django.contrib import admin

from .models import OCRJob


@admin.register(OCRJob)
class OCRJobAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "status", "created_at", "updated_at")
    list_filter = ("kind", "status")
    search_fields = ("id", "raw_text", "error_message")
    readonly_fields = ("created_at", "updated_at")
