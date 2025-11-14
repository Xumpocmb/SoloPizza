from django.contrib import admin
from .models import TrackedUTM


@admin.register(TrackedUTM)
class TrackedUTMAdmin(admin.ModelAdmin):
    list_display = ('utm_source', 'utm_medium', 'utm_campaign', 'timestamp', 'ip_address')
    readonly_fields = ('utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'timestamp', 'ip_address', 'user_agent')
    search_fields = ('utm_source', 'utm_medium', 'utm_campaign', 'ip_address')
    list_filter = ('utm_source', 'utm_medium', 'utm_campaign')
