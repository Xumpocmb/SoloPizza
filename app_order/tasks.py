from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import connection
from .models import Order


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
