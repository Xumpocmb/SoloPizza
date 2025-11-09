from django.db import models

class TrackedURL(models.Model):
    original_url = models.URLField()
    tracking_code = models.CharField(max_length=20, unique=True)
    clicks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.tracking_code}] {self.original_url}"
