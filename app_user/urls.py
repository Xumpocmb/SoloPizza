from django.urls import path
from app_user.views import register_view, login_view, logout_view

app_name = 'app_user'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
