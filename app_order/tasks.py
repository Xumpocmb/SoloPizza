from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Order


@shared_task
def clear_orders():
    """
    Задача для очистки списка заказов.
    Удаляет все заказы из базы данных.
    Запускается ежедневно в 08:00.
    """
    # Получаем и удаляем все заказы
    all_orders = Order.objects.all()
    count = all_orders.count()
    all_orders.delete()
    
    return f"Удалено {count} заказов."
