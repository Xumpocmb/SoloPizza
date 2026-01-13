from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import connection
from .models import Order, OrderStatistic, OrderItem
from django.db import models
from django.db.models import Sum, Q, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


@shared_task
def clear_orders():
    """
    Задача для очистки списка заказов.
    Удаляет все заказы из базы данных и сбрасывает счетчик ID.
    Запускается ежедневно в 08:00.
    """
    # Получаем и удаляем все заказы
    all_orders = Order.objects.all()
    count = all_orders.count()
    all_orders.delete()

    # Сбрасываем счетчик ID для таблицы заказов
    with connection.cursor() as cursor:
        # Определяем имя таблицы заказов
        table_name = Order._meta.db_table

        # Для SQLite
        if connection.vendor == "sqlite":
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
        # Для PostgreSQL (закомментировано, но оставлено для будущего использования)
        # elif connection.vendor == 'postgresql':
        #     cursor.execute(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1;")

    return f"Удалено {count} заказов. Счетчик ID сброшен."


@shared_task
def send_order_notification(order_id):
    """
    Отправляет уведомление о новом заказе в Telegram
    """
    try:
        order = Order.objects.select_related("branch").get(id=order_id)

        # Получаем токен и ID чата из настроек
        bot_token = getattr(settings, "BOT_TOKEN", None)
        chat_id = getattr(settings, "CHAT_ID", None)

        if not bot_token or not chat_id:
            return "Отсутствуют настройки для уведомлений в Telegram"

        # Формируем сообщение
        order_text = (
            f"ФИЛИАЛ: {order.branch.name}\n\n"
            f"Заказ {order.id}\n"
            f"Способ доставки: {dict(Order.DELIVERY_CHOICES)[order.delivery_type]}\n"
            f"Телефон: {order.phone_number}\n"
            f'Создан: {timezone.localtime(order.created_at).strftime("%d.%m.%Y %H:%M:%S")}\n'
            f"\nПодробности: https://solo-pizza.by/order/order/{order.id}/"
        )

        # Отправляем сообщение в Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {"chat_id": chat_id, "text": order_text}

        try:
            response = requests.get(url=url, params=params)
        except requests.exceptions.RequestException as e:
            return f"Ошибка при отправке запроса в Telegram: {str(e)}"

        if response.status_code != 200:
            return f"Ошибка при отправке уведомления: {response.status_code} - {response.text}"

        return f"Уведомление о заказе #{order_id} отправлено"

    except Order.DoesNotExist:
        return f"Объект Order с id {order_id} не найден"
    except Exception as e:
        return f"Ошибка при отправке уведомления: {str(e)}"


@shared_task
def collect_order_statistics():
    """
    Собирает статистику по заказам за текущий день и сохраняет ее в БД.
    Запускается ежедневно.
    """
    today = timezone.now().date()

    # Фильтруем заказы за сегодняшний день со статусом, не равным 'Отменен', и только оплаченные
    orders_today = Order.objects.filter(created_at__date=today, payment_status=True).exclude(status="canceled")

    # Сбор статистики по филиалам
    branch_stats = {}

    for order in orders_today.select_related("branch"):
        branch_id = order.branch.id
        branch_name = order.branch.name

        if branch_id not in branch_stats:
            branch_stats[branch_id] = {
                "name": branch_name,
                "orders_count": 0,
                "total_cash": Decimal("0.00"),
                "total_card": Decimal("0.00"),
                "total_noname": Decimal("0.00"),
                "sold_items": {},
            }

        # Увеличиваем количество заказов для филиала
        branch_stats[branch_id]["orders_count"] += 1

        # Добавляем сумму заказа к соответствующему методу оплаты
        order_total = order.total_price
        if order.payment_method == "cash":
            branch_stats[branch_id]["total_cash"] += order_total
        elif order.payment_method == "card":
            branch_stats[branch_id]["total_card"] += order_total
        elif order.payment_method == "noname":
            branch_stats[branch_id]["total_noname"] += order_total

    # Обработка позиций заказов для статистики по товарам
    order_items = OrderItem.objects.filter(order__in=orders_today).select_related("product", "variant", "order__branch")

    for item in order_items:
        branch_id = item.order.branch.id
        item_name = f"{item.product.name} ({item.get_size_display()})"

        if item_name not in branch_stats[branch_id]["sold_items"]:
            branch_stats[branch_id]["sold_items"][item_name] = {"quantity": 0, "payment_methods": {}}

        branch_stats[branch_id]["sold_items"][item_name]["quantity"] += item.quantity
        payment_method = item.order.get_payment_method_display()

        # Get the final total for the item
        item_final_total = item.calculate_item_total()["final_total"]

        if payment_method not in branch_stats[branch_id]["sold_items"][item_name]["payment_methods"]:
            branch_stats[branch_id]["sold_items"][item_name]["payment_methods"][payment_method] = Decimal("0.00")
        branch_stats[branch_id]["sold_items"][item_name]["payment_methods"][payment_method] += item_final_total

    # Добавляем итоговую сумму для каждого филиала
    for branch_id in branch_stats:
        branch_stats[branch_id]["total_amount"] = (
            branch_stats[branch_id]["total_cash"] + branch_stats[branch_id]["total_card"] + branch_stats[branch_id]["total_noname"]
        )

    # Подсчет общих сумм для всех филиалов
    total_orders_count = sum(branch["orders_count"] for branch in branch_stats.values())
    total_cash = sum(branch["total_cash"] for branch in branch_stats.values())
    total_card = sum(branch["total_card"] for branch in branch_stats.values())
    total_noname = sum(branch["total_noname"] for branch in branch_stats.values())
    total_amount = total_cash + total_card + total_noname

    # Создаем или обновляем запись в статистике
    statistic, created = OrderStatistic.objects.update_or_create(
        date=today,
        defaults={
            "orders_count": total_orders_count,
            "total_cash": total_cash,
            "total_card": total_card,
            "total_noname": total_noname,
            "total_amount": total_amount,
            "sold_items": branch_stats,  # Теперь содержит статистику по филиалам
        },
    )

    # Отправка email отчета
    email_status = ""
    try:
        recipient_email = getattr(settings, "EMAIL_RECIPIENT", None)
        if recipient_email:
            email_context = {
                "branch_statistics": branch_stats,
                "selected_date": today,
            }
            html_message = render_to_string("app_order/email/branch_statistics_email.html", email_context)

            send_mail(
                f'Дневной отчет по филиалам за {today.strftime("%d.%m.%Y")}',
                '',  # Plain text message (can be empty)
                settings.EMAIL_HOST_USER,
                [recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            email_status = f"Отчет успешно отправлен на {recipient_email}."
        else:
            email_status = "Адрес получателя (EMAIL_RECIPIENT) не настроен в settings.py."
    except Exception as e:
        email_status = f"Ошибка при отправке email: {e}"

    if created:
        return f"Статистика за {today} создана. Заказов: {total_orders_count}, общая сумма: {total_amount}. {email_status}"
    else:
        return f"Статистика за {today} обновлена. Заказов: {total_orders_count}, общая сумма: {total_amount}. {email_status}"
