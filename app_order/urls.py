from django.urls import path
from app_order.views import order_list, create_order, order_detail, order_detail_editor, select_address, remove_item

app_name = 'app_order'

urlpatterns = [
    path('', order_list, name='order_list'),
    path('create/', create_order, name='create_order'),
    path('<int:order_id>/', order_detail, name='order_detail'),
    path('editor/<int:order_id>/', order_detail_editor, name='order_detail_editor'),
    path('select-address/', select_address, name='select_address'),
    path('remove-item/<int:item_id>/', remove_item, name='remove_item'),
]