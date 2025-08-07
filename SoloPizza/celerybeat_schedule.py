from celery.schedules import crontab

# Настройка периодических задач Celery
CELERYBEAT_SCHEDULE = {
    'clear-orders-every-day': {
        'task': 'app_order.tasks.clear_orders',
        'schedule': crontab(hour=8, minute=0),  # Запуск каждый день в 08:00
        'args': (),
    },
}
