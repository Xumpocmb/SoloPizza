from django.urls import path
from app_user.views import register, user_login, logout_view

app_name = 'app_user'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', logout_view, name='logout'),
]
