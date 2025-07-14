from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from app_cart.models import CartItem
from app_order.forms import CheckoutForm, OrderEditForm, OrderItemFormSet
from app_order.models import OrderItem, Order


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    cart_totals = CartItem.objects.get_cart_totals(request.user)

    if not cart_items.exists():
        return redirect("app_cart:view_cart")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Создаем заказ
            order = form.save(user=request.user)

            # Переносим товары из корзины в заказ
            for cart_item in cart_items:
                order_item = OrderItem.objects.create(
                    order=order,
                    product=cart_item.item,
                    variant=cart_item.item_variant,
                    quantity=cart_item.quantity,
                    board1=cart_item.board1,
                    board2=cart_item.board2,
                    sauce=cart_item.sauce,
                )
                order_item.addons.set(cart_item.addons.all())

            # Очищаем корзину
            cart_items.delete()

            return redirect("app_order:order_detail", order_id=order.id)
    else:
        initial = {
            "customer_name": request.user.get_full_name(),
            "phone_number": getattr(request.user, "phone", ""),
        }
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "app_order/checkout.html",
        {
            "form": form,
            "cart_items": cart_items,
            "cart_totals": cart_totals,
        },
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related(
            "items__product", "items__variant", "items__board1__board", "items__board2__board", "items__sauce", "items__addons__addon"
        ),
        id=order_id,
        user=request.user,
    )
    totals = Order.objects.get_order_totals(order.id)  # Добавляем расчет сумм
    is_editable = order.is_editable()

    order_form = OrderEditForm(instance=order)
    items_formset = OrderItemFormSet(instance=order)

    return render(
        request,
        "app_order/order_detail.html",
        {
            "order": order,
            "totals": totals,  # Передаем в контекст
            "form": order_form,
            "item_formset": items_formset,
            "is_editable": is_editable,
        },
    )


@login_required
@require_POST
def update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not order.is_editable():
        return HttpResponseForbidden("Заказ нельзя редактировать")

    form = OrderEditForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        messages.success(request, "Изменения в заказе сохранены")
    else:
        messages.error(request, "Ошибка при сохранении заказа")

    return redirect("app_order:order_detail", order_id=order.id)


@login_required
@require_POST
def update_order_items(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not order.is_editable():
        return HttpResponseForbidden("Заказ нельзя редактировать")

    formset = OrderItemFormSet(request.POST, instance=order, form_kwargs={"request": request})  # Ключевое изменение - передаем request

    if formset.is_valid():
        formset.save()
        order.recalculate_totals()
        messages.success(request, "Изменения в товарах сохранены")
    else:
        messages.error(request, "Ошибка при сохранении товаров")

    return redirect("app_order:order_detail", order_id=order.id)


def update_order_totals(order):
    """Обновляет суммы заказа на основе текущих товаров с учетом бортов и добавок"""
    order.subtotal = Decimal("0")
    order.discount_amount = Decimal("0")
    order.total_price = Decimal("0")

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
            item.discount_amount = Decimal("0.1") * item_price  # 10% от базовой стоимости
        else:
            item.discount_amount = Decimal("0")

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
        orders = Order.objects.all().order_by("-created_at")
    else:
        orders = Order.objects.filter(user=request.user).order_by("-created_at")

    # Поиск и фильтрация
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        orders = orders.filter(Q(id__icontains=search_query) | Q(customer_name__icontains=search_query) | Q(phone_number__icontains=search_query))

    if status_filter:
        orders = orders.filter(status=status_filter)

    # Пагинация
    paginator = Paginator(orders, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "status_choices": Order.STATUS_CHOICES,
        "search_query": search_query,
        "status_filter": status_filter,
    }
    return render(request, "app_order/order_list.html", context)


@require_POST
@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get("status")
    
    print(new_status)

    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
        messages.success(request, f"Статус заказа #{order_id} изменен на «{order.get_status_display()}»")
    else:
        messages.error(request, "Неверный статус заказа")

    return redirect(request.META.get("HTTP_REFERER", "app_order:order_list"))
