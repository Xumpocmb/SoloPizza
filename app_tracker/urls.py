from django.urls import path
from . import views

urlpatterns = [
    path("", views.redirect_to_original_url, name="track_url"),
    path("analytics/", views.utm_analytics_view, name="utm_analytics"),
]
