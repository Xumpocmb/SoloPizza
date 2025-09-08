from django.urls import path
from .api_views import (
    OrderListView,
    OrderDetailView,
    OrderCreateView,
    OrderStatusView,
)

urlpatterns = [
    path('', OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('create/', OrderCreateView.as_view(), name='order_create'),
    path('<int:pk>/status/', OrderStatusView.as_view(), name='order_status'),
]