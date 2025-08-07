from celery.schedules import crontab

# Настройка периодических задач Celery
CELERYBEAT_SCHEDULE = {
    'clear-orders-every-day': {
        'task': 'app_order.tasks.clear_orders',
        'schedule': crontab(hour=8, minute=0),  # Запуск каждый день в 08:00
        'args': (),
    },
    'activate-combo-category': {
        'task': 'app_catalog.tasks.activate_combo_category',
        'schedule': crontab(hour=11, minute=0, day_of_week='1-5'),  # Запуск в 11:00 с понедельника по пятницу
        'args': (),
    },
    'deactivate-combo-category': {
        'task': 'app_catalog.tasks.deactivate_combo_category',
        'schedule': crontab(hour=17, minute=0, day_of_week='1-5'),  # Запуск в 17:00 с понедельника по пятницу
        'args': (),
    },
    'deactivate-combo-weekend': {
        'task': 'app_catalog.tasks.deactivate_combo_category',
        'schedule': crontab(hour=0, minute=0, day_of_week='0,6'),  # Запуск в 00:00 в субботу и воскресенье
        'args': (),
    },
}
