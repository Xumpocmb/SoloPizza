from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'app_order/order_list.html', context)


from django.db.models import Sum
from app_cart.models import CartItem

@login_required
def create_order(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('app_cart:view_cart')  # Если корзина пуста, перенаправляем на страницу корзины

    # Создаем заказ
    order = Order.objects.create(
        user=request.user,
        total_price=sum(item.item_params.price * item.quantity for item in cart_items),
    )

    # Создаем товары в заказе
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            item=cart_item.item,
            item_params=cart_item.item_params,
            quantity=cart_item.quantity,
            board=cart_item.board,
            price=cart_item.item_params.price,
        )

    # Очищаем корзину
    cart_items.delete()

    return redirect('app_order:order_list')


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'app_order/order_detail.html', context)