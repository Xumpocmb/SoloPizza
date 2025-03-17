from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from shapely.geometry import Point, Polygon

from app_catalog.models import AddonParams
from app_home.models import CafeBranch
from app_order.models import Order, OrderItem
from django.db.models import Sum
from app_cart.models import CartItem



@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'app_order/order_list.html', context)


@login_required
def create_order(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('app_cart:view_cart')  # Перенаправляем, если корзина пуста

    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        address = request.POST.get('selected-address')
        apartment = request.POST.get('apartment')
        entrance = request.POST.get('entrance')
        floor = request.POST.get('floor')
        order_comment = request.POST.get('comment')

        if not latitude or not longitude:
            return redirect('app_order:select_address')  # Перенаправляем, если координаты не переданы

        branch = determine_branch(float(latitude), float(longitude))
        if not branch:
            return redirect('app_order:select_address')  # Адрес вне зоны доставки

        total_price = cart_items.aggregate(total=Sum('item_params__price'))['total']
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            latitude=float(latitude),
            longitude=float(longitude),
            address=address,
            apartment=apartment,
            entrance=entrance,
            floor=floor,
            comment=order_comment,
            cafe_branch=branch,
        )

        for cart_item in cart_items:
            order_item = OrderItem.objects.create(
                order=order,
                item=cart_item.item,
                item_params=cart_item.item_params,
                quantity=cart_item.quantity,
                price=cart_item.item_params.price,
                board=cart_item.board,
            )

            # Получаем выбранные добавки для товара
            order_item.addons.set(cart_item.addons.all())

        cart_items.delete()

        return redirect('app_order:order_list')  # Перенаправляем на список заказов

    return redirect('app_order:select_address')


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__addons', 'items__board').filter(user=request.user),
        id=order_id
    )
    context = {
        'order': order,
    }
    return render(request, 'app_order/order_detail.html', context)


def determine_branch(user_latitude, user_longitude):
    user_point = Point(user_latitude, user_longitude)
    branches = CafeBranch.objects.filter(is_active=True)

    for branch in branches:
        polygon_coords = branch.delivery_zone
        polygon = Polygon(polygon_coords)

        if polygon.contains(user_point):
            return branch

    return None


def select_address(request):
    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if latitude and longitude:
            request.session['selected_address'] = {
                'latitude': latitude,
                'longitude': longitude,
            }
            return redirect('app_order:create_order')
    return render(request, 'app_order/select_address.html')