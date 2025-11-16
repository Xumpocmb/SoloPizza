from django.urls import path
from app_cart.views import add_to_cart, view_cart, update_quantity, remove_item

app_name = 'app_cart'

urlpatterns = [
    path('add/<slug:slug>/', add_to_cart, name='add_to_cart'),
    path('view/', view_cart, name='view_cart'),
    path('update/<str:item_id>/', update_quantity, name='update_quantity'),
    path('remove/<str:item_id>/', remove_item, name='remove_item'),
]
