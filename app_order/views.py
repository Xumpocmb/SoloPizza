from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404

from app_cart.models import CartItem
from app_order.forms import CheckoutForm, OrderEditForm
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

    if request.method == 'POST' and is_editable:
        form = OrderEditForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Изменения сохранены')
            return redirect('app_order:order_detail', order_id=order.id)
    else:
        form = OrderEditForm(instance=order)

    return render(request, 'app_order/order_detail.html', {
        'order': order,
        'order_items': order.items.all(),
        'form': form,
        'is_editable': is_editable,
    })