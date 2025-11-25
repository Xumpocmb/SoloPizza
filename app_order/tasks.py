from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import connection
from .models import Order
import requests
from django.conf import settings


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
        if connection.vendor == 'sqlite':
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
        order = Order.objects.select_related('branch').get(id=order_id)
        
        # Получаем токен и ID чата из настроек
        bot_token = getattr(settings, 'BOT_TOKEN', None)
        chat_id = getattr(settings, 'CHAT_ID', None)
        
        if not bot_token or not chat_id:
            return "Отсутствуют настройки для уведомлений в Telegram"
        
        # Формируем сообщение
        order_text = (f'ФИЛИАЛ: {order.branch.name}\n\n'
                      f'Заказ {order.id}\n'
                      f'Способ доставки: {dict(Order.DELIVERY_CHOICES)[order.delivery_type]}\n'
                      f'Телефон: {order.phone_number}\n'
                      f'Создан: {timezone.localtime(order.created_at).strftime("%d.%m.%Y %H:%M:%S")}\n'
                      f'\nПодробности: https://solo-pizza.by/order/order/{order.id}/')
        
        # Отправляем сообщение в Telegram
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        params = {
            'chat_id': chat_id,
            'text': order_text
        }
        
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
