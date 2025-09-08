from django.urls import path
from .api_views import (
    get_product_variants,
    get_size_boards,
    get_size_addons,
    CategoryListView,
    CategoryDetailView,
    ProductListView,
    ProductDetailView,
    ProductVariantListView,
    PizzaSauceListView,
    PizzaBoardListView,
    PizzaAddonListView,
    PizzaSizesListView,
)

urlpatterns = [
    # Существующие API endpoints
    path('product-variants/<int:product_id>/', get_product_variants, name='get_product_variants'),
    path('size-boards/<int:size_id>/', get_size_boards, name='get_size_boards'),
    path('size-addons/<int:size_id>/', get_size_addons, name='get_size_addons'),
    
    # Новые API endpoints с использованием DRF
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category_detail'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('variants/', ProductVariantListView.as_view(), name='variant_list'),
    path('sauces/', PizzaSauceListView.as_view(), name='sauce_list'),
    path('boards/', PizzaBoardListView.as_view(), name='board_list'),
    path('addons/', PizzaAddonListView.as_view(), name='addon_list'),
    path('sizes/', PizzaSizesListView.as_view(), name='size_list'),
]
