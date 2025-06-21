# from django.urls import path
# from app_order.views import order_list, create_order, order_detail, order_detail_editor, select_address, remove_item, \
#     item_sizes_api, add_to_order, board_params_api, addon_params_api
#
# app_name = 'app_order'
#
# urlpatterns = [
#     path('', order_list, name='order_list'),
#     path('create/', create_order, name='create_order'),
#     path('<int:order_id>/', order_detail, name='order_detail'),
#     path('editor/<int:order_id>/', order_detail_editor, name='order_detail_editor'),
#     path('select-address/', select_address, name='select_address'),
#     path('remove-item/<int:item_id>/', remove_item, name='remove_item'),
#     path('api/item-sizes/<int:item_id>/', item_sizes_api, name='item_sizes_api'),
#     path('api/item-sizes/<int:item_id>/', item_sizes_api, name='item_sizes_api'),
#     path('api/board-params/<int:size_id>/', board_params_api, name='board_params_api'),
#     path('api/addon-params/<int:size_id>/', addon_params_api, name='addon_params_api'),
#     path('add_to_order/<int:order_id>/', add_to_order, name='add_to_order'),
# ]
