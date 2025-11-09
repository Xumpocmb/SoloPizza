from django.contrib import admin
from .models import TrackedURL

@admin.register(TrackedURL)
class TrackedURLAdmin(admin.ModelAdmin):
    list_display = ('original_url', 'tracking_code', 'clicks', 'created_at')
    readonly_fields = ('clicks', 'created_at')
    search_fields = ('original_url', 'tracking_code')
