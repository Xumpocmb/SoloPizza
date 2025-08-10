from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import time
from app_cart.models import CartItem
from app_cart.utils import validate_cart_items_for_branch
from app_home.models import CafeBranch
from app_order.forms import CheckoutForm, OrderEditForm, OrderItemFormSet
from app_order.models import OrderItem, Order
from decimal import Decimal, ROUND_HALF_UP



DEFAULT_BRANCH_ID = 1


def is_order_time_allowed(user):
    """
    Проверяет, разрешено ли пользователю делать заказ в текущее время.
    Администраторы и сотрудники могут делать заказы в любое время.
    Обычные пользователи могут делать заказы только с 11:00 до 22:30.
    """
    # Администраторы и сотрудники могут делать заказы в любое время
    if user.is_superuser or user.is_staff:
        return True
    
    # Получаем текущее время в часовом поясе проекта
    current_time = timezone.localtime().time()
    
    start_time = time(11, 0)  # 11:00
    end_time = time(22, 30)    # 22:30
    
    # Проверяем, находится ли текущее время в разрешенном интервале
    return start_time <= current_time <= end_time


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related(
        'item', 'item__category'
    )
    cart_totals = CartItem.objects.get_cart_totals(request.user)

    if not cart_items.exists():
        return redirect("app_cart:view_cart")
        
    # Проверяем, разрешено ли пользователю делать заказ в текущее время
    if not is_order_time_allowed(request.user):
        messages.error(
            request,
            "Заказы принимаются только с 11:00 до 22:30."
        )
        return redirect("app_cart:view_cart")

    # Получаем выбранный филиал
    selected_branch_id = request.session.get('selected_branch_id', DEFAULT_BRANCH_ID)
    try:
        selected_branch = CafeBranch.objects.get(id=selected_branch_id)
    except CafeBranch.DoesNotExist:
        selected_branch = CafeBranch.objects.get(id=DEFAULT_BRANCH_ID)

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Проверяем товары перед созданием заказа
            unavailable_items = validate_cart_items_for_branch(cart_items, selected_branch)

            if unavailable_items:
                messages.error(
                    request,
                    f"Некоторые товары недоступны в филиале '{selected_branch.name}': "
                    f"{', '.join(item.item.name for item in unavailable_items)}"
                )
                return redirect("app_cart:view_cart")

            order = form.save(user=request.user)
            order.branch = selected_branch
            order.save()

            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.item,
                    variant=cart_item.item_variant,
                    quantity=cart_item.quantity,
                    board1=cart_item.board1,
                    board2=cart_item.board2,
                    sauce=cart_item.sauce,
                ).addons.set(cart_item.addons.all())

            cart_items.delete()
            return redirect("app_order:order_detail", order_id=order.id)
    else:
        # Проверяем товары при заходе на страницу оформления
        unavailable_items = validate_cart_items_for_branch(cart_items, selected_branch)
        if unavailable_items:
            messages.error(
                request,
                f"Некоторые товары недоступны в филиале '{selected_branch.name}'. "
                "Пожалуйста, измените состав корзины или выберите другой филиал."
            )
            return redirect("app_cart:view_cart")

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
            "selected_branch": selected_branch,
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

    breadcrumbs = [
        {'title': 'Главная', 'url': '/'},
        {'title': 'Мои заказы', 'url': reverse('app_order:order_list')},
        {'title': f'Заказ #{order.id}', 'url': '#'}
    ]

    return render(
        request,
        "app_order/order_detail.html",
        {
            "order": order,
            "totals": totals,  # Передаем в контекст
            "form": order_form,
            "item_formset": items_formset,
            "is_editable": is_editable,
            "breadcrumbs": breadcrumbs,
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


@login_required
def order_list(request):
    if request.user.is_staff:
        orders = Order.objects.all().order_by("-created_at")
    else:
        orders = Order.objects.filter(user=request.user).order_by("-created_at")

    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        orders = orders.filter(Q(id__icontains=search_query) | Q(customer_name__icontains=search_query) | Q(phone_number__icontains=search_query))

    if status_filter:
        orders = orders.filter(status=status_filter)

    paginator = Paginator(orders, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    breadcrumbs = [
        {'title': 'Главная', 'url': '/'},
        {'title': 'Мои заказы', 'url': reverse('app_order:order_list')}  # Текущая страница
    ]

    context = {
        "page_obj": page_obj,
        "status_choices": Order.STATUS_CHOICES,
        "search_query": search_query,
        "status_filter": status_filter,
        "breadcrumbs": breadcrumbs,
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


def print_check_non_fastfood(request, order_id):
    """
    Генерирует HTML для печати чека заказа БЕЗ фастфуда.
    Включает полную информацию о заказе.
    """
    order = get_object_or_404(Order, id=order_id)

    # Получаем позиции, исключая фастфуд
    items = (
        order.items.exclude(product__category__name="Фастфуд")
        .select_related("product__category", "variant__size", "board1__board", "board2__board", "sauce")
        .prefetch_related("addons")
    )

    # Пересчитываем итоги только для этой части
    subtotal_part = Decimal("0.00")
    discount_amount_part = Decimal("0.00")
    items_data = []

    for item in items:
        calc = item.calculate_item_total()
        # Цена за единицу без добавок (для отображения)
        base_item_price = (calc["final_total"] - (calc.get("additions_total", Decimal("0.00")))) / item.quantity if item.quantity > 0 else Decimal("0.00")
        # Округляем до 2 знаков
        base_item_price = base_item_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        items_data.append(
            {"item": item, "calculation": calc, "base_unit_price": base_item_price, "final_line_total": calc["final_total"]}  # Цена за единицу без добавок  # Итог по строке
        )
        subtotal_part += calc["original_total"]
        discount_amount_part += calc["discount_amount"]

    # Итог для этой части
    part_total = subtotal_part - discount_amount_part

    context = {
        "order": order,
        "items_data": items_data,
        "subtotal_part": subtotal_part.quantize(Decimal("0.01")),
        "discount_amount_part": discount_amount_part.quantize(Decimal("0.01")),
        "part_total": part_total.quantize(Decimal("0.01")),  # Итог только для этой части
        "check_title": "ЧЕК (Без Фастфуда)",
        "show_order_details": True,  # Флаг для отображения деталей заказа
    }
    return render(request, "app_order/print_check.html", context)


def print_check_fastfood_only(request, order_id):
    """
    Генерирует HTML для печати чека ТОЛЬКО с фастфудом.
    НЕ включает общую информацию о заказе.
    """
    order = get_object_or_404(Order, id=order_id)

    # Получаем только позиции фастфуда
    items = (
        order.items.filter(product__category__name="Фастфуд")
        .select_related("product__category", "variant__size", "board1__board", "board2__board", "sauce")
        .prefetch_related("addons")
    )

    # Пересчитываем итоги только для этой части
    subtotal_part = Decimal("0.00")
    discount_amount_part = Decimal("0.00")
    items_data = []

    for item in items:
        calc = item.calculate_item_total()
        # Цена за единицу без добавок (для отображения)
        base_item_price = (calc["final_total"] - (calc.get("additions_total", Decimal("0.00")))) / item.quantity if item.quantity > 0 else Decimal("0.00")
        # Округляем до 2 знаков
        base_item_price = base_item_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        items_data.append(
            {"item": item, "calculation": calc, "base_unit_price": base_item_price, "final_line_total": calc["final_total"]}  # Цена за единицу без добавок  # Итог по строке
        )
        subtotal_part += calc["original_total"]
        discount_amount_part += calc["discount_amount"]

    # Итог для этой части
    part_total = subtotal_part - discount_amount_part

    context = {
        "order": order,  # Передаем для потенциального доступа к ID или дате
        "items_data": items_data,
        "subtotal_part": subtotal_part.quantize(Decimal("0.01")),
        "discount_amount_part": discount_amount_part.quantize(Decimal("0.01")),
        "part_total": part_total.quantize(Decimal("0.01")),  # Итог только для этой части
        "check_title": "ЧЕК (Только Фастфуд)",
        "show_order_details": False,  # Флаг для НЕ отображения деталей заказа
    }
    return render(request, "app_order/print_check.html", context)
