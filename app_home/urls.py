from django.urls import path
from app_home.views import home_page, select_branch, discounts_view, vacancy_list, vacancy_detail, vacancy_apply

app_name = 'app_home'

urlpatterns = [
    path('', home_page, name='home'),
    path('select_branch/', select_branch, name='select_branch'),
    path('discounts/', discounts_view, name='discounts'),
    path('vacancies/', vacancy_list, name='vacancy_list'),
    path('vacancies/<int:vacancy_id>/', vacancy_detail, name='vacancy_detail'),
    path('vacancies/<int:vacancy_id>/apply/', vacancy_apply, name='vacancy_apply'),
]
