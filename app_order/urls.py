from django.urls import path
from app_order.views import checkout, order_detail, order_list

app_name = 'app_order'

urlpatterns = [
    path('checkout/', checkout, name='checkout'),
    path('orders/', order_list, name='order_list'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
]
