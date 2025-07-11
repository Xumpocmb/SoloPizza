from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render

from app_catalog.models import Product, ProductVariant, BoardParams, AddonParams, PizzaSauce
from .models import CartItem


@login_required()
def add_to_cart(request, slug):
    if request.method == 'POST':
        item = get_object_or_404(Product, slug=slug)
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))
        sauce_id = request.POST.get('sauce_id')
        board_id = request.POST.get('board_id')
        addon_ids = request.POST.getlist('addon_ids')

        variant = get_object_or_404(ProductVariant, id=variant_id, product=item)
        sauce = get_object_or_404(PizzaSauce, id=sauce_id) if sauce_id else None
        board = get_object_or_404(BoardParams, id=board_id) if board_id else None
        addons = AddonParams.objects.filter(id__in=addon_ids) if addon_ids else []

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            item=item,
            item_variant=variant,
            sauce=sauce,
            board=board,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        cart_item.addons.set(addons)

        messages.success(request, f'Товар "{item.name}" добавлен в корзину!')
        return redirect('app_catalog:item_detail', slug=slug)

    return redirect('app_catalog:item_detail', slug=slug)


@login_required
def view_cart(request):
    # Получаем все товары в корзине для текущего пользователя
    cart_items = CartItem.objects.filter(user=request.user).select_related(
        'item',
        'item_variant',
        'board',
        'board__board',
        'sauce'
    ).prefetch_related('addons', 'addons__addon')

    # Рассчитываем общую сумму корзины
    total_price = Decimal('0.00')
    discount_amount = Decimal('0.00')
    for item in cart_items:
        item_total = item.calculate_cart_total()
        total_price += item_total

        # Рассчитываем сумму скидки (только для пицц недели)
        if item.item.is_weekly_special and item.item.category.name == "Пицца":
            original_price = item.item_variant.price * item.quantity
            discount_amount += original_price * Decimal('0.1')  # 10% от оригинальной цены

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'discount_amount': discount_amount,
        'subtotal': total_price + discount_amount,  # Цена без учета скидки
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
