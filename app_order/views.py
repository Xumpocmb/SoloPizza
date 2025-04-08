from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from shapely.geometry import Point, Polygon

from app_catalog.models import AddonParams, PizzaSauce
from app_home.models import CafeBranch
from app_order.forms import OrderItemForm
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
    cart_items = (
        CartItem.objects.filter(user=request.user)
        .select_related("item", "item_params", "board", "sauce")
        .prefetch_related("addons")
    )

    if not cart_items.exists():
        return redirect("app_cart:view_cart")  # Перенаправляем, если корзина пуста

    if request.method == "POST":
        # Получаем данные из формы
        delivery_method = request.POST.get("delivery_method")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        address = request.POST.get("selected-address")
        apartment = request.POST.get("apartment")
        entrance = request.POST.get("entrance")
        floor = request.POST.get("floor")
        order_comment = request.POST.get("comment")

        # Проверяем выбранный метод доставки
        if delivery_method not in ["delivery", "pickup"]:
            return redirect("app_order:select_address")  # Некорректный метод доставки

        try:
            # Получаем выбранный филиал из сессии
            selected_branch_id = request.session.get(
                "selected_branch_id", 1
            )
            try:
                selected_branch = CafeBranch.objects.get(id=selected_branch_id)
            except CafeBranch.DoesNotExist:
                selected_branch = CafeBranch.objects.get(id=1)

            if delivery_method == "delivery":
                # Для доставки нужны координаты и адрес
                if not latitude or not longitude:
                    return redirect(
                        "app_order:select_address"
                    )  # Перенаправляем, если координаты не переданы

                branch = determine_branch(float(latitude), float(longitude))
                if not branch:
                    return redirect(
                        "app_order:select_address"
                    )  # Адрес вне зоны доставки

                # Создаем заказ с данными доставки
                order = Order.objects.create(
                    user=request.user,
                    total_price=0,  # Сигналы обновят стоимость позже
                    delivery_method="delivery",
                    latitude=float(latitude),
                    longitude=float(longitude),
                    address=address,
                    apartment=apartment,
                    entrance=entrance,
                    floor=floor,
                    comment=order_comment,
                    cafe_branch=branch,
                )
            elif delivery_method == "pickup":
                # Для самовывоза используем выбранный филиал из сессии
                order = Order.objects.create(
                    user=request.user,
                    total_price=0,  # Сигналы обновят стоимость позже
                    delivery_method="pickup",
                    comment=order_comment,
                    cafe_branch=selected_branch,  # Филиал из сессии
                )

            # Создаем элементы заказа
            for cart_item in cart_items:
                order_item = OrderItem.objects.create(
                    order=order,
                    item=cart_item.item,
                    item_params=cart_item.item_params,
                    quantity=cart_item.quantity,
                    price=cart_item.item_params.price,
                    board=cart_item.board,
                    sauce=cart_item.sauce,
                )

                # Добавляем выбранные добавки
                order_item.addons.set(cart_item.addons.all())

            # Очищаем корзину
            cart_items.delete()

            # Обновляем общую стоимость заказа
            order.calculate_total_price()

            return redirect("app_order:order_list")  # Перенаправляем на список заказов

        except Exception as e:
            # Логируем ошибку и перенаправляем пользователя
            print(f"Ошибка при создании заказа: {e}")
            return redirect("app_order:select_address")

    return redirect("app_order:select_address")


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__addons', 'items__board', 'items__sauce').filter(user=request.user),
        id=order_id
    )
    context = {
        'order': order,
    }
    return render(request, 'app_order/order_detail.html', context)

@login_required
def order_detail_editor(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__addons', 'items__board').filter(user=request.user),
        id=order_id
    )

    if request.method == 'POST':
        for item in order.items.all():
            form = OrderItemForm(request.POST, prefix=f'item-{item.id}', instance=item)
            if form.is_valid():
                form.save()
        order.calculate_total_price()
        return redirect('app_order:order_detail', order_id=order.id)

    else:
        # Создаем словарь форм для каждого товара
        forms = {
            item.id: OrderItemForm(instance=item, prefix=f'item-{item.id}')
            for item in order.items.all()
        }

    sauces = PizzaSauce.objects.filter(is_active=True)

    context = {
        'order': order,
        'forms': forms,
        'sauces': sauces,
    }
    return render(request, 'app_order/order_detail_editor.html', context)


@login_required
def remove_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
        order = item.order
        item.delete()

        # Пересчитываем общую стоимость заказа
        order.calculate_total_price()
        return redirect('order_detail', order_id=order.id)


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
