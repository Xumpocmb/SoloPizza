from django.urls import path
from app_order.views import checkout, order_detail, order_list, update_order, update_order_items

app_name = 'app_order'

urlpatterns = [
    path('checkout/', checkout, name='checkout'),
    path('orders/', order_list, name='order_list'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
    path('<int:order_id>/update/', update_order, name='update_order'),
    path('<int:order_id>/update-items/', update_order_items, name='update_order_items'),
]
