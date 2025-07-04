from django.urls import path
from app_order.views import checkout, order_detail

app_name = 'app_order'

urlpatterns = [
    path('checkout/', checkout, name='checkout'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
]
