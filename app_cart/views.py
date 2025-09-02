from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from app_cart.forms import AddToCartForm
from app_catalog.models import Product, ProductVariant, BoardParams, AddonParams, PizzaSauce
from .models import CartItem


@login_required
def add_to_cart(request, slug):
    if request.method == 'POST':
        item = get_object_or_404(Product, slug=slug)
        variant = get_object_or_404(ProductVariant, id=request.POST.get('variant_id'), product=item)

        form = AddToCartForm(request.POST, product=item, variant=variant)

        if form.is_valid():
            data = form.cleaned_data

            # Получаем поля
            variant_id = data.get('variant_id')
            quantity = data.get('quantity')
            sauce_id = data.get('sauce_id')
            board1_id = data.get('board1_id')
            board2_id = data.get('board2_id')
            addon_ids = data.get('addons', [])

            # Обработка бортов
            board1 = BoardParams.objects.filter(id=board1_id).first() if board1_id else None
            board2 = BoardParams.objects.filter(id=board2_id).first() if board2_id else None

            # Проверка на одинаковые борты для пиццы и комбо
            if board1 and board2 and board1_id == board2_id:
                messages.error(request, 'Нельзя выбрать одинаковые борты.')
                return redirect('app_catalog:item_detail', slug=slug)
                
            # Проверка, что борты доступны для данного товара
            is_pizza_or_combo = item.category.name in ["Пицца", "Кальцоне"] or (item.category.name == "Комбо" and item.is_combo)
            if not is_pizza_or_combo:
                board1 = None
                board2 = None

            # Обработка соуса
            sauce = PizzaSauce.objects.filter(id=sauce_id).first() if sauce_id else None

            # Обработка добавок
            addons = AddonParams.objects.filter(id__in=addon_ids) if addon_ids else []

            # Получаем выбранный напиток для комбо
            drink = request.POST.get('drink') if item.category.name == "Комбо" else None
            
            # Создание/обновление элемента корзины
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                item=item,
                item_variant=variant,
                sauce=sauce,
                board1=board1,
                board2=board2,
                drink=drink,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            cart_item.addons.set(addons)

            # Показываем уведомление только если пользователь не персонал и не суперпользователь
            if not request.user.is_staff and not request.user.is_superuser:
                messages.success(request, f'Товар "{item.name}" добавлен в корзину!')
            return redirect('app_catalog:item_detail', slug=slug)
        else:
            messages.error(request, 'Ошибка в форме. Пожалуйста, проверьте данные.')
            return redirect('app_catalog:item_detail', slug=slug)

    return redirect('app_catalog:item_detail', slug=slug)



@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related(
        'item', 'item_variant', 'sauce', 'board1', 'board2'
    ).prefetch_related('addons')
    
    enriched_items = []
    subtotal = Decimal('0')
    discount = Decimal('0')
    
    for item in cart_items:
        calculation = item.calculate_cart_item_total()
        enriched_items.append({
            'object': item,
            'item_total': calculation['final_total'],
            'original_total': calculation['original_total'],
            'has_discount': calculation['is_weekly_pizza']
        })
        subtotal += calculation['original_total']
        discount += calculation['discount_amount']
    
    context = {
        'items': enriched_items,
        'subtotal': subtotal,
        'discount_amount': discount,
        'total_price': subtotal - discount,
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
