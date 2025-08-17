#!/bin/bash

# Скрипт для тестирования задачи удаления заказов

# Переходим в директорию проекта
cd "$(dirname "$0")"

echo "Запуск задачи clear_orders для тестирования..."

# Запускаем задачу clear_orders через Django shell
python manage.py shell -c "from app_order.tasks import clear_orders; result = clear_orders.delay(); print(f'Задача запущена с ID: {result.id}')"

echo ""
echo "Проверка количества заказов до и после выполнения задачи:"
python manage.py shell -c "from app_order.models import Order; print(f'Количество заказов в базе данных: {Order.objects.count()}')"

echo ""
echo "Для проверки статуса задачи используйте:"
echo "python manage.py shell -c \"from celery.result import AsyncResult; print(AsyncResult('ID_ЗАДАЧИ').status)\""