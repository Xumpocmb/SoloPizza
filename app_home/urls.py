from django.urls import path
from app_home.views import home_page, select_branch

app_name = 'app_home'

urlpatterns = [
    path('', home_page, name='home'),
    path('select_branch/', select_branch, name='select_branch'),
]