from django.urls import path
from . import views

urlpatterns = [
    path('<str:tracking_code>/', views.redirect_to_original_url, name='track_url'),
]
