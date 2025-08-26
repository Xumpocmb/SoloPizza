from django.urls import path
from app_order.views import checkout, order_detail, order_list, update_order, update_order_items, update_order_status, update_order_branch, print_check_non_fastfood, print_check_fastfood_only, add_item_to_order

app_name = 'app_order'

urlpatterns = [
    path("checkout/", checkout, name="checkout"),
    path("orders/", order_list, name="order_list"),
    path("order/<int:order_id>/", order_detail, name="order_detail"),
    path("<int:order_id>/update/", update_order, name="update_order"),
    path("<int:order_id>/update-items/", update_order_items, name="update_order_items"),
    path("<int:order_id>/update-status/", update_order_status, name="update_order_status"),
    path("<int:order_id>/update-branch/", update_order_branch, name="update_order_branch"),
    path("<int:order_id>/add-item/", add_item_to_order, name="add_item_to_order"),
    path("print-non-fastfood/<int:order_id>/", print_check_non_fastfood, name="print_non_fastfood_check"),
    path("print-fastfood/<int:order_id>/", print_check_fastfood_only, name="print_fastfood_check"),
]
