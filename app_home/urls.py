from django.urls import path
from app_home.views import home_page, select_branch, discounts_view, vacancy_list, vacancy_detail, vacancy_apply, contacts_view, feedback_view, info_view, delivery_view, utm_analytics_view, partners_view

app_name = 'app_home'

urlpatterns = [
    path('', home_page, name='home'),
    path('select_branch/', select_branch, name='select_branch'),
    path('discounts/', discounts_view, name='discounts'),
    path('info/', info_view, name='info'),
    path('contacts/', contacts_view, name='contacts'),
    path('feedback/', feedback_view, name='feedback'),  # URL остается тем же, но функциональность переименована в "Вопросы и предложения"
    path('vacancies/', vacancy_list, name='vacancy_list'),
    path('vacancies/<int:vacancy_id>/', vacancy_detail, name='vacancy_detail'),
    path('vacancies/<int:vacancy_id>/apply/', vacancy_apply, name='vacancy_apply'),
    path('delivery/', delivery_view, name='delivery'),
    path('utm-analytics/', utm_analytics_view, name='utm_analytics'),
    path('partners/', partners_view, name='partners'),
]
