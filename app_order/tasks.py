from celery import shared_task
from django.utils import timezone
from django.conf import settings

import requests

from .models import Order


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
            f"Заказ {order.print_number}\n"
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