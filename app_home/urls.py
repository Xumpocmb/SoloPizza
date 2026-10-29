from django.urls import path
from app_home.views import (
    home_page,
    select_branch,
    discounts_view,
    vacancy_list,
    vacancy_detail,
    vacancy_apply,
    contacts_view,
    feedback_view,
    info_view,
    delivery_view,
    partners_view,
    certificate_sell,
    certificate_check,
    certificate_use,
    certificate_search,
)

app_name = "app_home"

urlpatterns = [
    path("", home_page, name="home"),
    path("select_branch/", select_branch, name="select_branch"),
    path("discounts/", discounts_view, name="discounts"),
    path("info/", info_view, name="info"),
    path("contacts/", contacts_view, name="contacts"),
    path("feedback/", feedback_view, name="feedback"),  # URL остается тем же, но функциональность переименована в "Вопросы и предложения"
    path("vacancies/", vacancy_list, name="vacancy_list"),
    path("vacancies/<int:vacancy_id>/", vacancy_detail, name="vacancy_detail"),
    path("vacancies/<int:vacancy_id>/apply/", vacancy_apply, name="vacancy_apply"),
    path("delivery/", delivery_view, name="delivery"),
    path("partners/", partners_view, name="partners"),
    path("certificates/sell/", certificate_sell, name="certificate_sell"),
    path("certificates/check/", certificate_check, name="certificate_check"),
    path("certificates/<int:certificate_id>/use/", certificate_use, name="certificate_use"),
    path("certificates/search/", certificate_search, name="certificate_search"),
]
