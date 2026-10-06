from django.urls import path
from app_order.views import (
    checkout,
    order_detail,
    order_list,
    poll_new_orders,
    update_order,
    delete_order_item,
    update_order_status,
    update_order_branch,
    print_check_non_fastfood,
    print_check_fastfood_only,
    add_cart_to_order,
    order_statistics_view,
    detail_statistics_view,
    reports_view,
    send_detail_statistics_email,
    send_order_statistics_email,
)

app_name = "app_order"

urlpatterns = [
    path("checkout/", checkout, name="checkout"),
    path("orders/", order_list, name="order_list"),
    path("orders/poll-new/", poll_new_orders, name="poll_new_orders"),
    path("order/<int:order_id>/", order_detail, name="order_detail"),
    path("<int:order_id>/update/", update_order, name="update_order"),
    path("<int:order_id>/items/<int:item_id>/delete/", delete_order_item, name="delete_order_item"),
    path("<int:order_id>/update-status/", update_order_status, name="update_order_status"),
    path("<int:order_id>/update-branch/", update_order_branch, name="update_order_branch"),
    path("add-cart-to-order/", add_cart_to_order, name="add_cart_to_order"),
    path("print-non-fastfood/<int:order_id>/", print_check_non_fastfood, name="print_non_fastfood_check"),
    path("print-fastfood/<int:order_id>/", print_check_fastfood_only, name="print_fastfood_check"),
    path("statistics/", order_statistics_view, name="order_statistics"),
    path("statistics/detail/<str:date>/", detail_statistics_view, name="detail_statistics"),
    path("reports/", reports_view, name="reports"),
    path("send-detail-statistics-email/", send_detail_statistics_email, name="send_detail_statistics_email"),
    path("send-order-statistics-email/", send_order_statistics_email, name="send_order_statistics_email"),
]
