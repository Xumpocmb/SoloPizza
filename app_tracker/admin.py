from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.conf import settings
from .models import TrackedURL

@admin.register(TrackedURL)
class TrackedURLAdmin(admin.ModelAdmin):
    list_display = ('original_url', 'tracking_code', 'clicks', 'created_at', 'trackable_link')
    readonly_fields = ('clicks', 'created_at', 'trackable_link')
    search_fields = ('original_url', 'tracking_code')

    def trackable_link(self, obj):
        if settings.DEBUG:
            domain = "http://localhost:8000"
        else:
            domain = settings.DOMAIN_NAME

        link = f"{domain}{reverse('track_url')}?code={obj.tracking_code}"
        return format_html("<a href='{}'>{}</a>", link, link)

    trackable_link.short_description = "Trackable Link"
