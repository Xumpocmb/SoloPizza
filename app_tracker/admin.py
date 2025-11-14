from django.contrib import admin
from .models import TrackedUTM, TrackedURL


@admin.register(TrackedUTM)
class TrackedUTMAdmin(admin.ModelAdmin):
    list_display = ('utm_source', 'utm_medium', 'utm_campaign', 'timestamp', 'ip_address')
    readonly_fields = ('utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'timestamp', 'ip_address', 'user_agent')
    search_fields = ('utm_source', 'utm_medium', 'utm_campaign', 'ip_address')
    list_filter = ('utm_source', 'utm_medium', 'utm_campaign')

@admin.register(TrackedURL)
class TrackedURLAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'original_url', 'clicks', 'created_at')
    search_fields = ('tracking_code', 'original_url')
    readonly_fields = ('clicks', 'created_at')
