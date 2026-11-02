from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from app_api import views

app_name = "app_api"

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="app_api:schema"), name="swagger-ui"),
    path("meta/", views.MetaView.as_view(), name="meta"),
    path("branches/", views.BranchListView.as_view(), name="branches"),
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("categories/<slug:slug>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("products/", views.ProductListView.as_view(), name="products"),
    path("products/featured/", views.FeaturedProductListView.as_view(), name="featured-products"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
]
