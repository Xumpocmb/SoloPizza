from django.urls import path
from app_catalog.api_views import get_product_variants, get_size_boards, get_size_addons

app_name = 'app_catalog_api'

urlpatterns = [
    path('product/<int:product_id>/variants/', get_product_variants, name='get_product_variants'),
    path('size/<int:size_id>/boards/', get_size_boards, name='get_size_boards'),
    path('size/<int:size_id>/addons/', get_size_addons, name='get_size_addons'),
]