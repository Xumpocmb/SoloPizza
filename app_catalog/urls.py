from django.urls import path
from app_catalog.views import category_detail, item_detail

app_name = 'app_catalog'

urlpatterns = [
    path('category/<slug:slug>/', category_detail, name='category_detail'),
    path('item/<slug:slug>/', item_detail, name='item_detail'),
]
