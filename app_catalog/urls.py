from django.urls import path
from app_catalog.views import category_detail, item_detail, get_product_data, update_prices

app_name = 'app_catalog'

urlpatterns = [
    path('category/<slug:slug>/', category_detail, name='category_detail'),
    path('item/<slug:slug>/', item_detail, name='item_detail'),
    path('product-data/<slug:slug>/', get_product_data, name='get_product_data'),
    path('update-prices/', update_prices, name='update_prices'),
]
