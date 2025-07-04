from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404

from app_cart.models import CartItem
from app_order.forms import CheckoutForm, OrderEditForm, OrderItemEditForm
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
        .prefetch_related('items__product',
                          'items__variant',
                          'items__board',
                          'items__sauce',
                          'items__addons__addon'),
        id=order_id,
        user=request.user
    )
    is_editable = order.is_editable()

    if request.method == 'POST' and 'edit_item' in request.POST:
        item_id = request.POST.get('item_id')
        item = get_object_or_404(OrderItem, id=item_id, order=order)
        if item.is_editable():
            form = OrderItemEditForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
                messages.success(request, 'Изменения сохранены')
                return redirect('app_order:order_detail', order_id=order.id)

    if request.method == 'POST' and is_editable:
        form = OrderEditForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Изменения сохранены')
            return redirect('app_order:order_detail', order_id=order.id)
    else:
        form = OrderEditForm(instance=order, initial={
            'delivery_type': order.delivery_type,
            'address': order.address if order.delivery_type == 'delivery' else 'Самовывоз'
        })

    item_forms = []
    for item in order.items.all():
        item_forms.append({
            'item': item,
            'form': OrderItemEditForm(instance=item),
            'is_editable': item.is_editable()
        })

    return render(request, 'app_order/order_detail.html', {
        'order': order,
        'order_items': order.items.all(),
        'form': form,
        'item_forms': item_forms,
        'is_editable': is_editable,
    })


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