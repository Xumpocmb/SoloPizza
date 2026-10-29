from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden, Http404, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import time, datetime
from functools import wraps
from app_cart.models import CartItem
from app_cart.session_cart import SessionCart
from app_cart.utils import validate_cart_items_for_branch
from app_home.context_processors import get_active_branches, get_selected_branch_id
from app_home.models import CafeBranch, WorkingHours
from app_order.forms import CheckoutForm, OrderEditForm
from app_order import statistics
from app_order.models import OrderItem, Order, suspended_order_totals
from app_home.models import OrderAvailability
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
import requests
import os


DEFAULT_BRANCH_ID = 1


def get_recipient_emails():
    """Возвращает список email-адресов получателей из настроек."""
    return [email.strip() for email in settings.EMAIL_RECIPIENTS_LIST if email.strip()]


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

    # Получаем выбранный филиал (объекты из контекстного процессора — с телефонами и графиком)
    selected_branch_id = get_selected_branch_id(request)
    selected_branch = next((branch for branch in get_active_branches(request) if branch.id == selected_branch_id), None)
    if selected_branch is None:
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

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Проверяем товары перед созданием заказа
            unavailable_items = validate_cart_items_for_branch(cart_items, selected_branch)

            if unavailable_items:
                messages.error(request, f"Некоторые товары недоступны в филиале '{selected_branch.name}': " f"{', '.join(item.name for item in unavailable_items)}")
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

            with suspended_order_totals():
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
            # ------------------------------
            # --- УВЕДОМЛЕНИЯ В ТГ ОТКЛЮЧЕНЫ
            # ------------------------------

            # if not settings.DEBUG and not request.user.is_superuser and not request.user.is_staff:
            #     from .tasks import send_order_notification

            #     send_order_notification.delay(order.id)
            messages.success(request, f"Ваш заказ №{order.print_number} успешно оформлен!")
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


def _order_detail_queryset():
    return Order.objects.select_related("user", "branch").prefetch_related(
        "items__product__category",
        "items__variant__size",
        "items__board1__board",
        "items__board2__board",
        "items__sauce",
        "items__addons__addon",
    )


def order_detail(request, order_id):
    # Если пользователь является персоналом, то он может видеть любой заказ
    # Иначе пользователь может видеть только свои заказы
    if request.user.is_staff or request.user.is_superuser:
        order = get_object_or_404(_order_detail_queryset(), id=order_id)
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

        order = get_object_or_404(_order_detail_queryset(), order_query_conditions)

    totals = Order.objects.get_order_totals(order)
    is_editable = order.is_editable()

    order_form = OrderEditForm(instance=order)

    items = [item for item, _ in totals["items"]]
    for item, calculation in totals["items"]:
        item.set_total_cache(calculation)

    breadcrumbs = [{"title": _("Главная"), "url": "/"}, {"title": _("Мои заказы"), "url": reverse("app_order:order_list")}, {"title": _("Заказ #%(number)s") % {"number": order.print_number}, "url": "#"}]

    return render(
        request,
        "app_order/order_detail.html",
        {
            "order": order,
            "totals": totals,  # Передаем в контекст
            "form": order_form,
            "items": items,
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
def delete_order_item(request, order_id, item_id):
    # Если пользователь является персоналом, то он может удалять товары в любом заказе
    # Иначе пользователь может удалять товары только в своих заказах
    if request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    else:
        session_key = request.session.session_key or request.session.create()
        order = get_object_or_404(Order, id=order_id, session_key=session_key)

    if not order.is_editable():
        return HttpResponseForbidden("Заказ нельзя редактировать")

    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
    order_item.delete()
    order.recalculate_totals()
    messages.success(request, "Товар удалён из заказа")

    return redirect("app_order:order_detail", order_id=order.id)


def order_list(request):
    # Получаем выбранный филиал из сессии
    selected_branch_id = get_selected_branch_id(request)

    # Debug: Get the current guest token value
    current_guest_token = request.COOKIES.get("guest_token")
    current_session_key = request.session.session_key

    if request.user.is_staff:
        orders = (
            Order.objects.filter(branch_id=selected_branch_id, created_at__date=timezone.localdate())
            .select_related("branch")
            .order_by("-created_at")
        )
    else:
        # Prioritize user's orders if authenticated
        if request.user.is_authenticated:
            orders = Order.objects.filter(
                user=request.user,
                branch_id=selected_branch_id,
                created_at__date=timezone.localdate(),
            ).select_related("branch").order_by("-created_at")
        else:
            # For unauthenticated users, show orders that match their tokens
            # Since guest_token is a UUID4 (cryptographically secure), we can safely
            # allow access to orders that were created with this token, regardless of user assignment
            guest_token = request.COOKIES.get("guest_token")
            if guest_token:
                orders = Order.objects.filter(
                    guest_token=guest_token,
                    branch_id=selected_branch_id,
                    created_at__date=timezone.localdate(),
                ).select_related("branch").order_by("-created_at")
            else:
                # Fallback to session_key if no guest_token
                session_key = request.session.session_key or request.session.create()
                orders = Order.objects.filter(
                    session_key=session_key,
                    user__isnull=True,
                    branch_id=selected_branch_id,
                    created_at__date=timezone.localdate(),
                ).select_related("branch").order_by("-created_at")

    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        orders = orders.filter(Q(id__icontains=search_query) | Q(customer_name__icontains=search_query) | Q(phone_number__icontains=search_query))

    if status_filter:
        orders = orders.filter(status=status_filter)

    paginator = Paginator(orders, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    breadcrumbs = [{"title": _("Главная"), "url": "/"}, {"title": _("Мои заказы"), "url": reverse("app_order:order_list")}]  # Текущая страница

    # Получаем информацию о выбранном филиале
    branches = get_active_branches(request)
    selected_branch = next((branch for branch in branches if branch.id == selected_branch_id), None)
    if selected_branch is None:
        # выбранный филиал мог быть отключён, тогда показываем именно его
        try:
            selected_branch = CafeBranch.objects.get(id=selected_branch_id)
        except CafeBranch.DoesNotExist:
            selected_branch = CafeBranch.objects.get(id=DEFAULT_BRANCH_ID)

    context = {
        "page_obj": page_obj,
        "status_choices": Order.STATUS_CHOICES,
        "search_query": search_query,
        "status_filter": status_filter,
        "breadcrumbs": breadcrumbs,
        "selected_branch": selected_branch,
        "branches": branches,
        "current_guest_token": current_guest_token,
        "current_session_key": current_session_key,
        # Момент отрисовки страницы: по нему считаются заказы, созданные после открытия списка
        "order_poll_config": {
            "url": reverse("app_order:poll_new_orders"),
            "since": timezone.now().timestamp(),
        },
    }
    return render(request, "app_order/order_list.html", context)


def _staff_required(view):
    """Доступ только для сотрудников (is_staff или суперпользователь)."""

    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({"error": "forbidden"}, status=403)
        return view(request, *args, **kwargs)

    return wrapper


@_staff_required
def poll_new_orders(request):
    """
    Возвращает заказы филиала, созданные после отметки времени, переданной в ?since=.
    Нужен сотрудникам на странице списка заказов, чтобы узнавать о новых
    заказах без перезагрузки страницы.
    """
    selected_branch_id = get_selected_branch_id(request)

    # Отметку фиксируем до выборки, иначе заказ, созданный между запросом и ответом, потеряется
    now = timezone.now()

    try:
        since = float(request.GET.get("since", 0))
    except (TypeError, ValueError):
        since = 0.0

    # Заказы, оформленные из этой же сессии, сотруднику не показываем
    orders = Order.objects.filter(branch_id=selected_branch_id).exclude(session_key=request.session.session_key).select_related("branch").order_by("created_at")

    if since:
        orders = orders.filter(created_at__gt=datetime.fromtimestamp(since, tz=timezone.get_current_timezone()))

    payload = [
        {
            "id": order.id,
            "number": order.print_number,
            "customer_name": order.customer_name,
            "phone_number": order.phone_number or "",
            "delivery_type": order.get_delivery_type_display(),
            "payment_status": order.payment_status,
            "total_price": str(order.total_price),
            "created_at": timezone.localtime(order.created_at).strftime("%H:%M"),
            "detail_url": reverse("app_order:order_detail", args=[order.id]),
        }
        for order in orders[:20]
    ]

    return JsonResponse({"orders": payload, "server_time": now.timestamp()})


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
    items = order.items.all().select_related("product__category", "variant__size", "board1__board", "board2__board", "sauce").prefetch_related("addons__addon")

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
@require_POST
def add_cart_to_order(request):
    """Добавляет товары из корзины в выбранный сотрудником заказ."""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Доступ запрещен")

    order = get_object_or_404(Order, id=request.POST.get("order_id"))

    if not order.is_editable():
        messages.error(request, "Этот заказ нельзя редактировать")
        return redirect("app_cart:view_cart")

    session_cart = SessionCart(request)
    cart_items = list(session_cart)

    if not cart_items:
        messages.error(request, "Корзина пуста")
        return redirect("app_cart:view_cart")

    with suspended_order_totals():
        for item_data in cart_items:
            order_item = OrderItem.objects.create(
                order=order,
                product=item_data["product"],
                variant=item_data["variant"],
                quantity=item_data["quantity"],
                board1=item_data["board1"],
                board2=item_data["board2"],
                sauce=item_data["sauce"],
                drink=item_data["drink"],
            )
            if item_data["addons"]:
                order_item.addons.set(item_data["addons"])

    order.recalculate_totals()
    session_cart.clear()

    messages.success(request, f"Товары добавлены в заказ №{order.print_number}")
    return redirect("app_order:order_detail", order_id=order.id)


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

    # Получаем позиции фастфуда по опции категории
    items = (
        order.items.filter(product__category__is_fastfood=True)
        .select_related("product__category", "variant__size", "board1__board", "board2__board", "sauce")
        .prefetch_related("addons__addon")
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


def _parse_date(value):
    """Разбирает дату из query/POST вида YYYY-MM-DD, возвращает None при пустом/неверном значении."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


STATISTICS_SORT_FIELDS = {"date", "orders_count", "total_cash", "total_card", "total_noname", "total_amount"}


@login_required
def order_statistics_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Доступ запрещен")

    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    rows = statistics.summarize_by_day(
        statistics.get_orders(_parse_date(start_date), _parse_date(end_date))
    )

    sort_by = request.GET.get("sort", "date")
    if sort_by not in STATISTICS_SORT_FIELDS:
        sort_by = "date"
    sort_dir = request.GET.get("dir", "desc")

    rows.sort(key=lambda day: day[sort_by], reverse=sort_dir != "asc")

    paginator = Paginator(rows, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "start_date": start_date,
        "end_date": end_date,
        "breadcrumbs": [{"title": _("Главная"), "url": "/"}, {"title": _("Статистика заказов"), "url": "#"}],
    }
    return render(request, "app_order/order_statistics.html", context)


@login_required
def detail_statistics_view(request, date):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Доступ запрещен")

    selected_date = _parse_date(date)
    if selected_date is None:
        raise Http404("Неверный формат даты")

    branch_statistics = statistics.build_branch_statistics(
        statistics.get_orders(selected_date, selected_date)
    )

    context = {
        "branch_statistics": branch_statistics,
        "selected_date": selected_date,
        "breadcrumbs": [
            {"title": _("Главная"), "url": "/"},
            {"title": _("Статистика заказов"), "url": reverse("app_order:order_statistics")},
            {"title": _("Детальная статистика за %(date)s") % {"date": selected_date.strftime("%d.%m.%Y")}, "url": "#"},
        ],
    }
    return render(request, "app_order/detail_statistics.html", context)


@login_required
def reports_view(request):
    """
    Отображает статистику по заказам за текущий день.
    Доступна сотрудникам и суперпользователю.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("app_order:order_list")

    # Дата за сегодня по местному времени — как в нумерации заказов
    today = timezone.localdate()
    orders_today = statistics.get_orders(today, today)

    branch_stats = statistics.build_branch_statistics(orders_today)

    # Подсчет общих сумм для всех филиалов
    total_orders_count = sum(branch["orders_count"] for branch in branch_stats.values())
    total_cash = sum(branch["total_cash"] for branch in branch_stats.values())
    total_card = sum(branch["total_card"] for branch in branch_stats.values())
    total_noname = sum(branch["total_noname"] for branch in branch_stats.values())
    total_amount = total_cash + total_card + total_noname

    # Статистика по сотрудникам (is_staff=True)
    employee_stats = {}
    for order in orders_today.filter(user__is_staff=True).select_related("user"):
        user = order.user
        if user not in employee_stats:
            employee_stats[user] = {"orders_count": 0, "total_amount": Decimal("0.00")}
        employee_stats[user]["orders_count"] += 1
        employee_stats[user]["total_amount"] += order.total_price

    employee_statistics = [
        {
            "user": user,
            "orders_count": data["orders_count"],
            "total_amount": data["total_amount"],
        }
        for user, data in employee_stats.items()
    ]
    employee_statistics.sort(key=lambda x: x["total_amount"], reverse=True)

    context = {
        "branch_statistics": branch_stats,
        "selected_date": today,
        "total_orders_count": total_orders_count,
        "total_cash": total_cash,
        "total_card": total_card,
        "total_noname": total_noname,
        "total_amount": total_amount,
        "employee_statistics": employee_statistics,
        "breadcrumbs": [{"title": _("Главная"), "url": "/"}, {"title": _("Отчеты"), "url": "#"}],
    }

    return render(request, "app_order/reports.html", context)


@login_required
@require_POST
def send_detail_statistics_email(request):
    """
    Отправляет детальную статистику по филиалам за выбранный день на email.
    Считает данные по заказам в реальном времени.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Доступ запрещен")

    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings

    selected_date = _parse_date(request.POST.get("date"))
    if selected_date is None:
        messages.error(request, "Неверный формат даты")
        return redirect(request.META.get("HTTP_REFERER", "app_order:order_list"))

    branch_statistics = statistics.build_branch_statistics(
        statistics.get_orders(selected_date, selected_date)
    )

    if not branch_statistics:
        messages.warning(request, f"Нет данных за {selected_date.strftime('%d.%m.%Y')}")
        return redirect(request.META.get("HTTP_REFERER", "app_order:order_list"))

    try:
        recipient_emails = get_recipient_emails()

        if recipient_emails:
            email_context = {
                "branch_statistics": branch_statistics,
                "selected_date": selected_date,
            }
            html_message = render_to_string("app_order/email/branch_statistics_email.html", email_context)

            send_mail(
                f'Дневной отчет по филиалам за {selected_date.strftime("%d.%m.%Y")}',
                "",  # Plain text message (can be empty)
                settings.EMAIL_HOST_USER,
                recipient_emails,  # Отправляем на все email-адреса
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(request, f"Отчет за {selected_date.strftime('%d.%m.%Y')} успешно отправлен на {', '.join(recipient_emails)}")
        else:
            messages.error(request, "Адрес получателя (EMAIL_RECIPIENT) не настроен в settings.py.")
    except Exception as e:
        messages.error(request, f"Ошибка при отправке email: {e}")

    return redirect(request.META.get("HTTP_REFERER", "app_order:order_list"))


@login_required
def send_order_statistics_email(request):
    """
    Отправляет статистику заказов за выбранный период на email.
    Считает данные по заказам в реальном времени.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Доступ запрещен")

    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings

    start_date = _parse_date(request.POST.get("start_date"))
    end_date = _parse_date(request.POST.get("end_date"))

    if start_date is None or end_date is None:
        messages.error(request, "Неверный формат даты")
        return redirect(request.META.get("HTTP_REFERER", "app_order:order_statistics"))

    branch_stats = statistics.build_branch_statistics(
        statistics.get_orders(start_date, end_date)
    )

    if not branch_stats:
        messages.warning(request, f"Нет данных за период с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}")
        return redirect(request.META.get("HTTP_REFERER", "app_order:order_statistics"))

    try:
        recipient_emails = get_recipient_emails()

        if recipient_emails:
            email_context = {
                "branch_statistics": branch_stats,
                "start_date": start_date,
                "end_date": end_date,
            }
            html_message = render_to_string("app_order/email/order_statistics_email.html", email_context)

            send_mail(
                f'Отчет по филиалам за период с {start_date.strftime("%d.%m.%Y")} по {end_date.strftime("%d.%m.%Y")}',
                "",
                settings.EMAIL_HOST_USER,
                recipient_emails,
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(request, f"Отчет за период с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')} успешно отправлен на {', '.join(recipient_emails)}")
        else:
            messages.error(request, "Адрес получателя (EMAIL_RECIPIENT) не настроен в settings.py.")
    except Exception as e:
        messages.error(request, f"Ошибка при отправке email: {e}")

    return redirect(request.META.get("HTTP_REFERER", "app_order:order_statistics"))
