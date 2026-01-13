from django.contrib import admin
from .models import TrackedUTM, TrackedURL


@admin.register(TrackedUTM)
class TrackedUTMAdmin(admin.ModelAdmin):
    list_display = ("utm_source", "utm_medium", "utm_campaign", "counter", "created_at", "updated_at")
    list_filter = ("utm_source", "utm_medium", "utm_campaign", "created_at")
    search_fields = ("utm_source", "utm_medium", "utm_campaign")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TrackedURL)
class TrackedURLAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "original_url", "clicks", "created_at")
    list_filter = ("created_at",)
    search_fields = ("tracking_code", "original_url")
