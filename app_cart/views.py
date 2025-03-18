from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render

from app_catalog.models import Item, ItemParams, BoardParams, AddonParams
from .models import CartItem


def add_to_cart(request, slug):
    if request.method == 'POST':
        # Получаем товар
        item = get_object_or_404(Item, slug=slug)

        # Получаем выбранные параметры из POST-данных
        size_id = request.POST.get('size')
        board_id = request.POST.get('board')
        addon_ids = request.POST.getlist('addons')  # Может быть несколько добавок
        quantity = int(request.POST.get('quantity', 1))

        # Проверяем, что размер выбран
        size = get_object_or_404(ItemParams, id=size_id, item=item)

        # Формируем данные о товаре
        item_data = {
            'item_slug': item.slug,
            'size_id': size_id,
            'quantity': quantity,
            'board_id': board_id,
            'addon_ids': addon_ids,
        }

        # Проверяем, что борт существует (если выбран)
        board = None
        if board_id:
            board = get_object_or_404(BoardParams, id=board_id, size=size.size)

        # Получаем добавки (если выбраны)
        addons = AddonParams.objects.filter(id__in=addon_ids, size=size.size)

        if request.user.is_authenticated:
            # Создаем или обновляем запись в корзине
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                item=item,
                item_params=size,
                board=board,
            )
            cart_item.addons.set(addons)  # Обновляем добавки
            cart_item.quantity = quantity
            cart_item.save()
        else:
            # Если пользователь не авторизован, сохраняем товар в сессии
            cart_in_session = request.session.get('cart_in_session', [])
            for cart_item in cart_in_session:
                if (cart_item['item_slug'] == item.slug and
                        cart_item['size_id'] == size_id and
                        cart_item['board_id'] == board_id and
                        set(cart_item['addon_ids']) == set(addon_ids)):
                    # Если такой товар уже есть, увеличиваем количество
                    cart_item['quantity'] += quantity
                    break
            else:
                # Иначе добавляем новый товар
                cart_in_session.append(item_data)

            request.session['cart_in_session'] = cart_in_session
            messages.info(request, f'Товар "{item.name}" будет добавлен в корзину после авторизации.')

            # Перенаправляем на страницу входа
            return redirect('app_user:login')

        return redirect('app_cart:view_cart')  # Перенаправляем в корзину
    else:
        return redirect('app_cart:view_cart')


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('item_params', 'board').prefetch_related('addons')

    # Добавляем общую цену для каждого товара
    for item in cart_items:
        base_price = item.item_params.price
        board_price = item.board.price if item.board else 0
        addons_price = item.addons.aggregate(total=Sum('price'))['total'] or 0
        item.total_price = (base_price + board_price + addons_price) * item.quantity  # Умножаем на количество

    # Общая сумма корзины
    total_price = sum(item.total_price for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'app_cart/cart.html', context)


@login_required
def update_quantity(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        action = request.POST.get('action')

        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1

        cart_item.save()

    return redirect('app_cart:view_cart')

@login_required
def remove_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        cart_item.delete()

    return redirect('app_cart:view_cart')
