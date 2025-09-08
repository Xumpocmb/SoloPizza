from django.urls import path
from .api_views import (
    CartItemListView,
    CartItemDetailView,
    CartSummaryView,
)

urlpatterns = [
    path('items/', CartItemListView.as_view(), name='cart_item_list'),
    path('items/<int:pk>/', CartItemDetailView.as_view(), name='cart_item_detail'),
    path('summary/', CartSummaryView.as_view(), name='cart_summary'),
]