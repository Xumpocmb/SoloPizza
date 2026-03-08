from django.urls import path
from app_catalog.views import category_detail, item_detail, catalog_view, get_variant_data, get_product_variants

app_name = 'app_catalog'

urlpatterns = [
    path("", catalog_view, name="catalog"),
    path("category/<slug:slug>/", category_detail, name="category_detail"),
    path("item/<slug:slug>/", item_detail, name="item_detail"),
    path("variant-data/<int:variant_id>/", get_variant_data, name="get_variant_data"),
    path("product-variants/<int:product_id>/", get_product_variants, name="get_product_variants"),
]
