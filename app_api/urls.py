from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from app_api import views

app_name = "app_api"

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="app_api:schema"), name="swagger-ui"),
    path("meta/", views.MetaView.as_view(), name="meta"),
    path("branches/", views.BranchListView.as_view(), name="branches"),
    path("contacts/", views.ContactsView.as_view(), name="contacts"),
    path("announcements/", views.AnnouncementListView.as_view(), name="announcements"),
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("categories/<slug:slug>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("products/", views.ProductListView.as_view(), name="products"),
    path("products/featured/", views.FeaturedProductListView.as_view(), name="featured-products"),
    path("products/weekly-special/", views.WeeklySpecialProductView.as_view(), name="weekly-special-product"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("auth/google/", views.GoogleLoginView.as_view(), name="auth-google"),
    path("auth/apple/", views.AppleLoginView.as_view(), name="auth-apple"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/items/", views.CartItemsView.as_view(), name="cart-items"),
    path("cart/items/<int:pk>/", views.CartItemDetailView.as_view(), name="cart-item"),
    path("cart/branch/", views.CartBranchView.as_view(), name="cart-branch"),
    path("vacancies/", views.VacancyListView.as_view(), name="vacancies"),
    path("vacancies/<int:pk>/", views.VacancyDetailView.as_view(), name="vacancy-detail"),
    path(
        "vacancies/<int:vacancy_pk>/applications/",
        views.VacancyApplicationView.as_view(),
        name="vacancy-applications",
    ),
]
