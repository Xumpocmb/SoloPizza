from django.db import models


class TrackedURL(models.Model):
    tracking_code = models.CharField(max_length=255, unique=True, db_index=True)
    original_url = models.URLField()
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tracking_code}: {self.original_url}"


class TrackedUTM(models.Model):
    utm_source = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    utm_medium = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    utm_campaign = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    utm_term = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    utm_content = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    counter = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content")

    def __str__(self):
        return f"UTM: {self.utm_source or 'N/A'} - {self.utm_campaign or 'N/A'} (Count: {self.counter})"
