from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from shapely.geometry import Point, Polygon

from app_catalog.models import AddonParams, PizzaSauce, ItemParams, BoardParams, Item
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
        forms = {
            item.id: OrderItemForm(instance=item, prefix=f'item-{item.id}')
            for item in order.items.all()
        }

    context = {
        'order': order,
        'forms': forms,
    }
    return render(request, 'app_order/order_detail_editor.html', context)


@login_required
def add_to_order(request, order_id):
    # Получаем заказ пользователя
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = Item.objects.all()
    sauces = PizzaSauce.objects.all()
    if request.method == "POST":
        try:
            # Извлекаем данные из POST-запроса
            item_id = request.POST.get('item')
            size_id = request.POST.get('size')
            quantity = request.POST.get('quantity', 1)
            board_id = request.POST.get('board')
            sauce_id = request.POST.get('sauce')
            addon_ids = request.POST.getlist('addons')

            # Валидация данных
            item = Item.objects.get(id=item_id)
            size = ItemParams.objects.get(size_id=size_id, item_id=item_id)
            quantity = int(quantity)

            # Опциональные поля
            board = BoardParams.objects.get(id=board_id) if board_id else None
            sauce = PizzaSauce.objects.get(id=sauce_id) if sauce_id else None
            addons = AddonParams.objects.filter(id__in=addon_ids)

            # Создаем новый элемент заказа
            order_item = OrderItem.objects.create(
                order=order,
                item=item,
                item_params=size,
                quantity=quantity,
                price=size.price,
                board=board,
                sauce=sauce,
            )

            order_item.addons.set(addons)

            order.calculate_total_price()

            messages.success(request, f"Товар '{item.name}' успешно добавлен в заказ.", extra_tags='success')

            return redirect('app_order:order_detail_editor', order_id=order.id)

        except Exception as e:
            messages.error(request, "Ошибка при добавлении товара", extra_tags='error')
            return redirect('app_order:add_to_order', order_id=order.id)

    context = {
        "order": order,
        "items": items,
        "sauces": sauces,
    }
    return render(request, "app_order/order_add_items.html", context)


@login_required
def remove_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
        order = item.order
        item.delete()

        # Пересчитываем общую стоимость заказа
        order.calculate_total_price()
        return redirect('app_order:order_detail_editor', order_id=order.id)


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


def item_sizes_api(request, item_id):
    # Получаем параметры товара
    params = ItemParams.objects.filter(item_id=item_id).values('id', 'size__id', 'size__name', 'value', 'unit')

    data = []
    for param in params:
        if param['size__id']:
            data.append({
                'id': param['size__id'],  # Используем size__id вместо id
                'name': param['size__name']
            })
        elif param['value']:
            data.append({
                'id': param['id'],  # Для товаров без size_id оставляем id
                'name': f"{param['value']} {param['unit']}"
            })

    return JsonResponse(data, safe=False)


def board_params_api(request, size_id):
    boards = BoardParams.objects.filter(size_id=size_id).values('id', 'board__name', 'price')
    data = [{'id': board['id'], 'name': board['board__name'], 'price': str(board['price'])} for board in boards]
    return JsonResponse(data, safe=False)


def addon_params_api(request, size_id):
    addons = AddonParams.objects.filter(size_id=size_id).values('id', 'addon__name', 'price')
    data = [{'id': addon['id'], 'name': addon['addon__name'], 'price': str(addon['price'])} for addon in addons]
    return JsonResponse(data, safe=False)

