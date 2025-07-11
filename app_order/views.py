from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST

from app_cart.models import CartItem
from app_catalog.models import BoardParams
from app_order.forms import CheckoutForm, OrderEditForm, OrderItemEditForm, OrderItemFormSet
from app_order.models import OrderItemAddon, OrderItem, Order


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('app_cart:view_cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                customer_name=form.cleaned_data['name'],
                phone_number=form.cleaned_data['phone'],
                address=form.cleaned_data['address'] if form.cleaned_data[
                                                            'delivery_type'] == 'delivery' else 'Самовывоз',
                delivery_type=form.cleaned_data['delivery_type'],
                payment_method=form.cleaned_data['payment_method'],
                comment=form.cleaned_data['comment'],
                status='new',
                discount_amount=0,
                subtotal=0,
                total_price=0,
            )

            for cart_item in cart_items:
                is_weekly_special = cart_item.item.is_weekly_special and cart_item.item.category.name == "Пицца"
                discount = Decimal('0.1') * cart_item.item_variant.price if is_weekly_special else Decimal('0')

                order_item = OrderItem.objects.create(
                    order=order,
                    product=cart_item.item,
                    variant=cart_item.item_variant,
                    quantity=cart_item.quantity,
                    price=cart_item.item_variant.price,
                    board=cart_item.board,
                    sauce=cart_item.sauce,
                    is_weekly_special=is_weekly_special,
                    discount_amount=discount * cart_item.quantity,
                )

                for addon in cart_item.addons.all():
                    OrderItemAddon.objects.create(
                        order_item=order_item,
                        addon=addon.addon,
                        price=addon.price
                    )

                order.subtotal += cart_item.item_variant.price * cart_item.quantity
                order.discount_amount += discount * cart_item.quantity

            order.total_price = order.subtotal - order.discount_amount
            order.save()

            cart_items.delete()

            messages.success(request, 'Ваш заказ успешно оформлен!')
            return redirect('app_order:order_detail', order_id=order.id)
    else:
        initial_data = {
            'name': request.user.get_full_name(),
            'phone': request.user.phone if hasattr(request.user, 'phone') else '',
        }
        form = CheckoutForm(initial=initial_data)

    return render(request, 'app_order/checkout.html', {
        'form': form,
        'cart_items': cart_items,
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('user')
             .prefetch_related(
                 'items__product',
                 'items__variant',
                 'items__board',
                 'items__sauce',
                 'items__addons__addon'
             ),
        id=order_id,
        user=request.user
    )
    is_editable = order.is_editable()

    order_form = OrderEditForm(instance=order)
    items_formset = OrderItemFormSet(instance=order)

    return render(request, 'app_order/order_detail.html', {
        'order': order,
        'form': order_form,
        'item_formset': items_formset,
        'is_editable': is_editable,
    })



@login_required
@require_POST
def update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not order.is_editable():
        return HttpResponseForbidden("Заказ нельзя редактировать")

    form = OrderEditForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        messages.success(request, 'Изменения в заказе сохранены')
    else:
        messages.error(request, 'Ошибка при сохранении заказа')

    return redirect('app_order:order_detail', order_id=order.id)


@login_required
@require_POST
def update_order_items(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not order.is_editable():
        return HttpResponseForbidden("Заказ нельзя редактировать")

    formset = OrderItemFormSet(request.POST, instance=order)
    if formset.is_valid():
        formset.save()
        update_order_totals(order)
        messages.success(request, 'Изменения в товарах сохранены')
    else:
        messages.error(request, 'Ошибка при сохранении товаров')

    return redirect('app_order:order_detail', order_id=order.id)


def update_order_totals(order):
    """Обновляет суммы заказа на основе текущих товаров с учетом бортов и добавок"""
    order.subtotal = Decimal('0')
    order.discount_amount = Decimal('0')
    order.total_price = Decimal('0')

    for item in order.items.all():
        # Базовая стоимость товара (вариант * количество)
        item_price = item.price * item.quantity
        item_subtotal = item_price

        # Добавляем стоимость борта, если есть
        if item.board:
            item_subtotal += item.board.price * item.quantity

        # Добавляем стоимость всех добавок
        for addon in item.addons.all():
            item_subtotal += addon.price * item.quantity

        # Рассчитываем скидку (если есть акция)
        if item.is_weekly_special:
            item.discount_amount = Decimal('0.1') * item_price  # 10% от базовой стоимости
        else:
            item.discount_amount = Decimal('0')

        item.save()

        # Обновляем суммы заказа
        order.subtotal += item_subtotal
        order.discount_amount += item.discount_amount

    # Итоговая сумма с учетом скидки
    order.total_price = order.subtotal - order.discount_amount
    order.save()


@login_required
def order_list(request):
    # Фильтрация заказов для пользователя (админы видят все)
    if request.user.is_staff:
        orders = Order.objects.all().order_by('-created_at')
    else:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Поиск и фильтрация
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    if status_filter:
        orders = orders.filter(status=status_filter)

    # Пагинация
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_choices': Order.STATUS_CHOICES,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'app_order/order_list.html', context)


def get_boards_by_size(request):
    print("get_boards_by_size")
    size_id = request.GET.get('size_id')
    if size_id:
        boards = BoardParams.objects.filter(size_id=size_id).select_related('board')
        data = {
            'boards': [
                {
                    'id': board.id,
                    'name': board.board.name,
                    'price': str(board.price)
                }
                for board in boards
            ]
        }
        return JsonResponse(data)
    return JsonResponse({'boards': []})