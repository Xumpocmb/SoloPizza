from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .session_cart import SessionCart
from django.db.models import Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from app_cart.forms import AddToCartForm
from app_catalog.models import Product, ProductVariant, BoardParams, AddonParams, PizzaSauce
from app_home.models import OrderAvailability
from .models import CartItem


def add_to_cart(request, slug):
    if request.method == "POST":
        item = get_object_or_404(Product, slug=slug)
        variant = get_object_or_404(ProductVariant, id=request.POST.get("variant_id"), product=item)

        form = AddToCartForm(request.POST, product=item, variant=variant)

        if form.is_valid():
            data = form.cleaned_data

            # Получаем поля
            variant_id = data.get("variant_id")
            quantity = data.get("quantity")
            sauce_id = data.get("sauce_id")
            board1_id = data.get("board1_id")
            board2_id = data.get("board2_id")
            addons = data.get("addons", [])

            # Обработка бортов
            board1 = BoardParams.objects.filter(id=board1_id).first() if board1_id else None
            board2 = BoardParams.objects.filter(id=board2_id).first() if board2_id else None

            # Проверка на одинаковые борты для пиццы и комбо
            if board1 and board2 and board1_id == board2_id:
                messages.error(request, "Нельзя выбрать одинаковые борты.")
                return redirect("app_catalog:item_detail", slug=slug)

            # Проверка, что борты доступны для данного товара
            is_pizza_or_combo = item.category.name in ["Пицца", "Кальцоне"] or (item.category.name == "Комбо" and item.is_combo)
            if not is_pizza_or_combo:
                board1 = None
                board2 = None

            # Обработка соуса
            sauce = PizzaSauce.objects.filter(id=sauce_id).first() if sauce_id else None

            # Получаем выбранный напиток для комбо
            drink = request.POST.get("drink") if item.category.name == "Комбо" else None

            session_cart = SessionCart(request)
            session_cart.add(
                product_id=item.id,
                variant_id=variant.id,
                quantity=quantity,
                board1_id=board1.id if board1 else None,
                board2_id=board2.id if board2 else None,
                sauce_id=sauce.id if sauce else None,
                addons_ids=[addon.id for addon in addons] if addons else [],  # Ensure addons_ids is a list of IDs
                drink=drink,
            )

            messages.success(request, f'Товар "{item.name}" добавлен в корзину!')
            # Redirect back to the referring page if available, otherwise to item detail
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return HttpResponseRedirect(referer)
            return redirect("app_catalog:item_detail", slug=slug)
        else:
            messages.error(request, "Ошибка в форме. Пожалуйста, проверьте данные.")
            # Redirect back to the referring page if available, otherwise to item detail
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return HttpResponseRedirect(referer)
            return redirect("app_catalog:item_detail", slug=slug)

    # Redirect back to the referring page if available, otherwise to item detail
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return redirect("app_catalog:item_detail", slug=slug)


def view_cart(request):
    # Проверяем, доступно ли оформление заказов
    if not OrderAvailability.is_orders_available():
        messages.warning(request, "В настоящий момент оформление новых заказов недоступно. Приносим свои извинения за доставленные неудобства.")

    enriched_items = []
    subtotal = Decimal("0")

    session_cart = SessionCart(request)
    for item in session_cart:
        # For session cart, 'item' already contains product, variant, etc.
        # and 'total_price' is pre-calculated.
        enriched_items.append(
            {
                "object": item["product"],  # Using product for display, might need to adjust for variant details
                "item_total": Decimal(item["total_price"]),
                "original_total": Decimal(item["total_price"]),  # Assuming no discounts in session cart for now
                "has_discount": False,
                "variant": item["variant"],
                "quantity": item["quantity"],
                "board1": item["board1"],
                "board2": item["board2"],
                "sauce": item["sauce"],
                "addons": item["addons"],
                "drink": item["drink"],
                "item_key": item["item_key"],
            }
        )
        subtotal += Decimal(item["total_price"])

    context = {
        "items": enriched_items,
        "subtotal": subtotal,
    }

    return render(request, "app_cart/cart.html", context)


def update_quantity(request, item_id):
    if request.method == "POST":
        session_cart = SessionCart(request)
        item_key = request.POST.get("item_key")  # Need to pass item_key from template
        if item_key:
            current_item = session_cart.cart.get(item_key)
            if current_item:
                action = request.POST.get("action")
                if action == "increase":
                    current_item["quantity"] += 1
                elif action == "decrease" and current_item["quantity"] > 1:
                    current_item["quantity"] -= 1
                session_cart.save()

    return redirect("app_cart:view_cart")


def remove_item(request, item_id):  # item_id here will be item_key for session cart
    if request.method == "POST":
        session_cart = SessionCart(request)
        item_key = item_id  # item_id is actually the item_key for session cart
        session_cart.remove(item_key)

    return redirect("app_cart:view_cart")
