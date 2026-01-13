from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import time
from app_cart.models import CartItem  # Still needed for `CartItem.objects.total_quantity` in some cases
from app_cart.session_cart import SessionCart  # Import SessionCart
from app_cart.utils import validate_cart_items_for_branch
from app_home.models import CafeBranch, WorkingHours
from app_order.forms import CheckoutForm, OrderEditForm, OrderItemFormSet, AddToOrderForm
from app_order.models import OrderItem, Order, OrderStatistic
from app_home.models import OrderAvailability
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
import requests
import os


DEFAULT_BRANCH_ID = 1


def is_order_time_allowed(user):
    """
    Проверяет, разрешено ли пользователю делать заказ в текущее время.
    Администраторы и сотрудники могут делать заказы в любое время.
    Обычные пользователи могут делать заказы в соответствии с графиком работы филиала.
    """
    # Администраторы и сотрудники могут делать заказы в любое время
    if user.is_superuser or user.is_staff or settings.DEBUG:
        return True

    # Получаем текущее время в часовом поясе проекта
    current_time = timezone.localtime()
    current_day_of_week = current_time.isoweekday()  # 1 - понедельник, 7 - воскресенье
    current_time_only = current_time.time()

    # Получаем ID выбранного филиала из сессии
    selected_branch_id = user.profile.selected_branch_id if hasattr(user, "profile") and user.profile.selected_branch_id else DEFAULT_BRANCH_ID

    # Получаем график работы для выбранного филиала в текущий день недели
    try:
        working_hours = WorkingHours.objects.get(branch_id=selected_branch_id, day_of_week=current_day_of_week)
    except WorkingHours.DoesNotExist:
        # Если для текущего дня не установлен график, считаем, что филиал закрыт
        return False

    # Если филиал закрыт в этот день, заказы не принимаются
    if working_hours.is_closed:
        return False

    # Проверяем, находится ли текущее время в рабочем интервале филиала
    return working_hours.opening_time <= current_time_only <= working_hours.closing_time


def checkout(request):
    # Проверяем, доступно ли оформление заказов
    if not OrderAvailability.is_orders_available():
        messages.error(request, "В настоящий момент оформление новых заказов недоступно. Приносим свои извинения за доставленные неудобства.")
        return redirect("app_cart:view_cart")

    session_cart = SessionCart(request)
    cart_items = list(session_cart)  # Get items from session cart
    cart_totals = session_cart.get_total_price()  # Get total price from session cart

    if not cart_items:  # Check if session cart is empty
        return redirect("app_cart:view_cart")

    # Получаем выбранный филиал
    selected_branch_id = request.session.get("selected_branch_id", DEFAULT_BRANCH_ID)
    try:
        selected_branch = CafeBranch.objects.get(id=selected_branch_id)
    except CafeBranch.DoesNotExist:
        selected_branch = CafeBranch.objects.get(id=DEFAULT_BRANCH_ID)

    # Проверяем, разрешено ли пользователю делать заказ в текущее время
    if not is_order_time_allowed(request.user):
        # Получаем график работы для выбранного филиала в текущий день недели
        from datetime import datetime

        current_day_of_week = datetime.now().isoweekday()
        try:
            working_hours = WorkingHours.objects.get(branch=selected_branch, day_of_week=current_day_of_week)
            if working_hours.is_closed:
                time_info = "закрыто"
            else:
                time_info = f"с {working_hours.opening_time.strftime('%H:%M')} до {working_hours.closing_time.strftime('%H:%M')}"
        except WorkingHours.DoesNotExist:
            time_info = "график работы не установлен"

        messages.error(request, f"Заказы принимаются в соответствии с графиком работы филиала: {time_info}.")
        return redirect("app_cart:view_cart")

    # Получаем выбранный филиал
    selected_branch_id = request.session.get("selected_branch_id", DEFAULT_BRANCH_ID)
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
                messages.error(request, f"Некоторые товары недоступны в филиале '{selected_branch.name}': " f"{', '.join(item.item.name for item in unavailable_items)}")
                return redirect("app_cart:view_cart")

            session_key = request.session.session_key or request.session.create()

            # Ensure guest_token exists - get from cookie or create new one
            guest_token = request.COOKIES.get("guest_token")
            if not guest_token:
                from uuid import uuid4

                guest_token = str(uuid4())

            order = form.save(commit=False)
            order.session_key = session_key
            order.user = request.user if request.user.is_authenticated else None
            order.guest_token = guest_token

            # Default payment status to False for all orders
            order.payment_status = False
            order.status = "new"  # Ensure status is 'new' for all new orders

            if request.user.is_authenticated:
                # Only staff can create "paid" orders directly
                order.payment_status = True if request.user.is_staff else False

            order.branch = selected_branch
            order.save()

            for item_data in cart_items:
                # Retrieve actual model instances for product, variant, etc.
                product = item_data["product"]
                variant = item_data["variant"]
                board1 = item_data["board1"]
                board2 = item_data["board2"]
                sauce = item_data["sauce"]
                addons = item_data["addons"]
                drink = item_data["drink"]

                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=variant,
                    quantity=item_data["quantity"],
                    board1=board1,
                    board2=board2,
                    sauce=sauce,
                    drink=drink,
                )
                if addons:
                    order_item.addons.set(addons)

            # Пересчитываем итоги заказа после добавления всех товаров
            order.recalculate_totals()
            session_cart.clear()  # Clear the session cart after order is placed
            if not settings.DEBUG and not request.user.is_superuser and not request.user.is_staff:
                from .tasks import send_order_notification

                send_order_notification.delay(order.id)
            messages.success(request, f"Ваш заказ №{order.id} успешно оформлен!")
            response = redirect("app_order:order_detail", order_id=order.id)
            # Set guest_token cookie if it doesn't exist, using the same token as the order
            if not request.COOKIES.get("guest_token"):
                response.set_cookie("guest_token", guest_token, max_age=60 * 60 * 24 * 365 * 10)  # 10 years
            return response
    else:
        # Проверяем товары при заходе на страницу оформления
        unavailable_items = validate_cart_items_for_branch(cart_items, selected_branch)
        if unavailable_items:
            messages.error(request, f"Некоторые товары недоступны в филиале '{selected_branch.name}'. " "Пожалуйста, измените состав корзины или выберите другой филиал.")
            return redirect("app_cart:view_cart")

        initial = {}
        if request.user.is_authenticated:
            initial = {
                "customer_name": request.user.get_full_name(),
                "phone_number": getattr(request.user, "phone", ""),
            }
        form = CheckoutForm(initial=initial)

    context = {
        "form": form,
        "cart_items": cart_items,
        "cart_totals": cart_totals,
        "selected_branch": selected_branch,
    }

    return render(request, "app_order/checkout.html", context)


# Функция send_notify больше не используется, так как уведомления отправляются через Celery задачу send_order_notification


def order_detail(request, order_id):
    # Если пользователь является персоналом, то он может видеть любой заказ
    # Иначе пользователь может видеть только свои заказы
    if request.user.is_staff or request.user.is_superuser:
        order = get_object_or_404(
            Order.objects.select_related("user", "branch").prefetch_related(
                "items__product", "items__variant", "items__board1__board", "items__board2__board", "items__sauce", "items__addons__addon"
            ),
            id=order_id,
        )
    else:
        # For non-staff/superuser users, try to find the order by user, guest_token, or session_key
        order_query_conditions = Q(id=order_id)

        # If user is authenticated, prioritize their orders
        if request.user.is_authenticated:
            order_query_conditions &= Q(user=request.user)
        else:
            # For unauthenticated users, allow access via guest token
            # (secure because guest_token is UUID4 - cryptographically unique)
            guest_token = request.COOKIES.get("guest_token")
            session_key = request.session.session_key

            # Build OR conditions for guest_token and session_key
            guest_or_session_query = Q()
            if guest_token:
                guest_or_session_query |= Q(guest_token=guest_token)
            if session_key:
                # For session_key, still ensure no user is assigned for security
                guest_or_session_query |= Q(session_key=session_key, user__isnull=True)

            # Combine with order ID
            if guest_or_session_query:
                order_query_conditions &= guest_or_session_query
            else:
                # If no guest_token or session_key, it's an invalid request for unauthenticated user
                raise Http404("Order not found with provided credentials.")

        order = get_object_or_404(
            Order.objects.select_related("user", "branch").prefetch_related(
                "items__product", "items__variant", "items__board1__board", "items__board2__board", "items__sauce", "items__addons__addon"
            ),
            order_query_conditions,
        )
    totals = Order.objects.get_order_totals(order.id)  # Добавляем расчет сумм
    is_editable = order.is_editable()

    order_form = OrderEditForm(instance=order)
    items_formset = OrderItemFormSet(instance=order)

    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Мои заказы", "url": reverse("app_order:order_list")}, {"title": f"Заказ #{order.id}", "url": "#"}]

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
            "selected_branch": order.branch,  # Добавляем филиал в контекст
        },
    )


@login_required
@require_POST
def update_order(request, order_id):
    # Если пользователь является персоналом, то он может редактировать любой заказ
    # Иначе пользователь может редактировать только свои заказы
    if request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    else:
        session_key = request.session.session_key or request.session.create()
        order = get_object_or_404(Order, id=order_id, session_key=session_key)

    if not order.is_editable():
        return HttpResponseForbidden("Заказ нельзя редактировать")

    form = OrderEditForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        order.recalculate_totals()  # Пересчитываем стоимость заказа после сохранения
        messages.success(request, "Изменения в заказе сохранены")
    else:
        messages.error(request, "Ошибка при сохранении заказа")

    return redirect("app_order:order_detail", order_id=order.id)


@login_required
@require_POST
def update_order_items(request, order_id):
    # Если пользователь является персоналом, то он может редактировать товары в любом заказе
    # Иначе пользователь может редактировать товары только в своих заказах
    if request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    else:
        session_key = request.session.session_key or request.session.create()
        order = get_object_or_404(Order, id=order_id, session_key=session_key)

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


def order_list(request):
    # Получаем выбранный филиал из сессии
    selected_branch_id = request.session.get("selected_branch_id", DEFAULT_BRANCH_ID)

    # Debug: Get the current guest token value
    current_guest_token = request.COOKIES.get("guest_token")
    current_session_key = request.session.session_key

    if request.user.is_staff:
        orders = Order.objects.filter(branch_id=selected_branch_id).order_by("-created_at")
    else:
        # Prioritize user's orders if authenticated
        if request.user.is_authenticated:
            orders = Order.objects.filter(user=request.user, branch_id=selected_branch_id).order_by("-created_at")
        else:
            # For unauthenticated users, show orders that match their tokens
            # Since guest_token is a UUID4 (cryptographically secure), we can safely
            # allow access to orders that were created with this token, regardless of user assignment
            guest_token = request.COOKIES.get("guest_token")
            if guest_token:
                orders = Order.objects.filter(guest_token=guest_token, branch_id=selected_branch_id).order_by("-created_at")
            else:
                # Fallback to session_key if no guest_token
                session_key = request.session.session_key or request.session.create()
                orders = Order.objects.filter(session_key=session_key, user__isnull=True, branch_id=selected_branch_id).order_by("-created_at")

    # Additional debug info for unauthenticated users
    debug_total_orders_for_guest_token = 0
    debug_total_orders_for_guest_token_anon_only = 0  # Orders with no user assigned
    debug_total_orders_for_guest_token_all = 0  # All orders with this guest token
    debug_total_orders_for_session_key = 0
    debug_total_orders_for_session_key_anon_only = 0
    debug_total_orders_for_user = 0

    if not request.user.is_authenticated:
        if current_guest_token:
            debug_total_orders_for_guest_token_all = Order.objects.filter(guest_token=current_guest_token).count()
            debug_total_orders_for_guest_token_anon_only = Order.objects.filter(guest_token=current_guest_token, user__isnull=True, branch_id=selected_branch_id).count()
        if current_session_key:
            debug_total_orders_for_session_key = Order.objects.filter(session_key=current_session_key).count()
            debug_total_orders_for_session_key_anon_only = Order.objects.filter(session_key=current_session_key, user__isnull=True, branch_id=selected_branch_id).count()
    elif request.user.is_authenticated:
        debug_total_orders_for_user = Order.objects.filter(user=request.user).count()

    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        orders = orders.filter(Q(id__icontains=search_query) | Q(customer_name__icontains=search_query) | Q(phone_number__icontains=search_query))

    if status_filter:
        orders = orders.filter(status=status_filter)

    paginator = Paginator(orders, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Мои заказы", "url": reverse("app_order:order_list")}]  # Текущая страница

    # Получаем информацию о выбранном филиале
    try:
        selected_branch = CafeBranch.objects.get(id=selected_branch_id)
    except CafeBranch.DoesNotExist:
        selected_branch = CafeBranch.objects.get(id=DEFAULT_BRANCH_ID)

    # Получаем список всех филиалов для возможности изменения филиала заказа
    branches = CafeBranch.objects.filter(is_active=True)

    context = {
        "page_obj": page_obj,
        "status_choices": Order.STATUS_CHOICES,
        "search_query": search_query,
        "status_filter": status_filter,
        "breadcrumbs": breadcrumbs,
        "selected_branch": selected_branch,
        "branches": branches,
        "current_guest_token": current_guest_token,  # Debug information
        "current_session_key": current_session_key,
        "debug_total_orders_for_guest_token_all": debug_total_orders_for_guest_token_all,
        "debug_total_orders_for_guest_token_anon_only": debug_total_orders_for_guest_token_anon_only,
        "debug_total_orders_for_session_key": debug_total_orders_for_session_key,
        "debug_total_orders_for_session_key_anon_only": debug_total_orders_for_session_key_anon_only,
        "debug_total_orders_for_user": debug_total_orders_for_user,
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


@require_POST
@login_required
def update_order_branch(request, order_id):
    """Изменение филиала для конкретного заказа"""
    if not request.user.is_staff:
        return HttpResponseForbidden("Доступ запрещен")

    order = get_object_or_404(Order, id=order_id)
    new_branch_id = request.POST.get("branch_id")

    try:
        new_branch = CafeBranch.objects.get(id=new_branch_id)
        order.branch = new_branch
        order.save()
        messages.success(request, f"Филиал заказа #{order_id} изменен на «{new_branch.name}»")
    except CafeBranch.DoesNotExist:
        messages.error(request, "Выбранный филиал не найден")

    return redirect(request.META.get("HTTP_REFERER", "app_order:order_list"))


@login_required
def print_check_non_fastfood(request, order_id):
    """
    Генерирует HTML для печати чека со ВСЕМИ товарами заказа.
    Включает полную информацию о заказе.
    """
    # Проверка прав доступа - только для администраторов и персонала
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("app_order:order_list")

    order = get_object_or_404(Order, id=order_id)

    # Получаем все позиции заказа
    items = order.items.all().select_related("product__category", "variant__size", "board1__board", "board2__board", "sauce").prefetch_related("addons")

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

        # Создаем полное описание с информацией о цене и количестве
        full_description = item.get_full_description(include_price_info=True, base_unit_price=base_item_price, final_line_total=calc["final_total"])

        items_data.append({"item": item, "calculation": calc, "base_unit_price": base_item_price, "final_line_total": calc["final_total"], "full_description": full_description})
        subtotal_part += calc["original_total"]
        discount_amount_part += calc["discount_amount"]

    # Итог для этой части
    part_total = subtotal_part - discount_amount_part

    # Если это заказ с доставкой и стоимость доставки больше 0, добавляем её к итогу
    if order.delivery_type == "delivery" and order.delivery_cost > 0:
        part_total += order.delivery_cost

    context = {
        "order": order,
        "items_data": items_data,
        "subtotal_part": subtotal_part.quantize(Decimal("0.01")),
        "discount_amount_part": discount_amount_part.quantize(Decimal("0.01")),
        "part_total": part_total.quantize(Decimal("0.01")),  # Итог только для этой части
        "check_title": "ЧЕК (Все товары)",
        "show_order_details": True,  # Флаг для отображения деталей заказа
        "branch": order.branch,  # Передаем филиал для доступа к настройкам печати
    }
    return render(request, "app_order/print_check.html", context)


@login_required
def add_item_to_order(request, order_id):
    """Добавление товара в существующий заказ"""
    # Проверка прав доступа - только для администраторов и персонала
    if not request.user.is_staff:
        return redirect("app_order:order_list")

    order = get_object_or_404(Order, id=order_id)

    # Проверяем, можно ли редактировать заказ
    if not order.is_editable():
        messages.error(request, "Этот заказ нельзя редактировать")
        return redirect("app_order:order_detail", order_id=order.id)

    if request.method == "POST":
        form = AddToOrderForm(request.POST, order=order)
        if form.is_valid():
            product = form.cleaned_data["product"]
            variant = form.cleaned_data["variant"]
            quantity = form.cleaned_data["quantity"]
            board1 = form.cleaned_data.get("board1")
            board2 = form.cleaned_data.get("board2")
            sauce = form.cleaned_data.get("sauce")
            addons = form.cleaned_data.get("addons", [])

            # Создаем новый элемент заказа
            order_item = OrderItem.objects.create(order=order, product=product, variant=variant, quantity=quantity, board1=board1, board2=board2, sauce=sauce)

            # Добавляем добавки, если они есть
            if addons:
                order_item.addons.set(addons)

            # Пересчитываем итоги заказа
            order.recalculate_totals()

            messages.success(request, f"Товар '{product.name}' добавлен в заказ")
            return redirect("app_order:order_detail", order_id=order.id)
    else:
        form = AddToOrderForm(order=order)

    return render(
        request,
        "app_order/add_item_to_order.html",
        {
            "form": form,
            "order": order,
        },
    )


@login_required
def print_check_fastfood_only(request, order_id):
    """
    Генерирует HTML для печати чека ТОЛЬКО с фастфудом.
    НЕ включает общую информацию о заказе.
    """
    # Проверка прав доступа - только для администраторов и персонала
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("app_order:order_list")

    order = get_object_or_404(Order, id=order_id)

    # Получаем позиции фастфуда, соусов и бургеров
    items = (
        order.items.filter(product__category__name__in=["Фастфуд", "Бургеры", "Соусы", "Сковородки"])
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

        # Создаем полное описание с информацией о цене и количестве
        full_description = item.get_full_description(include_price_info=True, base_unit_price=base_item_price, final_line_total=calc["final_total"])

        items_data.append({"item": item, "calculation": calc, "base_unit_price": base_item_price, "final_line_total": calc["final_total"], "full_description": full_description})
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
        "branch": order.branch,  # Передаем филиал для доступа к настройкам печати
    }
    return render(request, "app_order/print_check.html", context)


@login_required
def order_statistics_view(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Доступ запрещен")

    statistics_list = OrderStatistic.objects.all()

    # Filtering
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date:
        statistics_list = statistics_list.filter(date__gte=start_date)
    if end_date:
        statistics_list = statistics_list.filter(date__lte=end_date)

    # Sorting
    sort_by = request.GET.get("sort", "date")
    sort_dir = request.GET.get("dir", "desc")

    if sort_dir == "asc":
        statistics_list = statistics_list.order_by(sort_by)
    else:
        statistics_list = statistics_list.order_by(f"-{sort_by}")

    paginator = Paginator(statistics_list, 30)  # 30 записей на страницу
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "start_date": start_date,
        "end_date": end_date,
        "breadcrumbs": [{"title": "Главная", "url": "/"}, {"title": "Статистика заказов", "url": "#"}],
    }
    return render(request, "app_order/order_statistics.html", context)


@login_required
def branch_statistics_view(request, date):
    if not request.user.is_staff:
        return HttpResponseForbidden("Доступ запрещен")

    # Конвертируем строку даты в объект даты
    from datetime import datetime

    try:
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        # Если формат даты неверный, возвращаем ошибку
        raise Http404("Неверный формат даты")

    # Получаем статистику для выбранной даты
    try:
        statistic = OrderStatistic.objects.get(date=selected_date)
    except OrderStatistic.DoesNotExist:
        raise Http404("Статистика для указанной даты не найдена")

    # Получаем структуру данных по филиалам
    branch_statistics = statistic.sold_items

    context = {
        "branch_statistics": branch_statistics,
        "selected_date": selected_date,
        "breadcrumbs": [
            {"title": "Главная", "url": "/"},
            {"title": "Статистика заказов", "url": reverse("app_order:order_statistics")},
            {"title": f"Статистика по филиалам за {selected_date.strftime('%d.%m.%Y')}", "url": "#"},
        ],
    }
    return render(request, "app_order/branch_statistics.html", context)
