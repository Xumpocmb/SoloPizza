from celery.schedules import crontab

# Настройка периодических задач Celery
# Эти задачи будут добавлены в базу данных при первом запуске
# В дальнейшем управление задачами происходит через админ-панель
CELERYBEAT_SCHEDULE = {
    # Задачи перенесены в модель PeriodicTask и управляются через админ-панель
    # Эти настройки используются только при первоначальной настройке
    # или если не используется django_celery_beat
}

# Функция для создания начальных задач в базе данных
def create_initial_tasks():
    """
    Создает начальные периодические задачи в базе данных,
    если они еще не существуют.
    
    Эта функция вызывается при запуске сервера.
    """
    try:
        from app_tasks.models import PeriodicTask
        from django.utils import timezone
        
        # Проверяем, есть ли уже задачи в базе
        if PeriodicTask.objects.count() == 0:
            # Создаем задачу очистки заказов
            PeriodicTask.objects.create(
                name="Очистка заказов",
                task="app_order.tasks.clear_orders",
                description="Очищает список заказов каждый день в 08:00",
                schedule_type="daily",
                hour=8,
                minute=0,
                enabled=True,
            )
            
            # Создаем задачу активации категории Комбо
            PeriodicTask.objects.create(
                name="Активация категории Комбо",
                task="app_catalog.tasks.activate_combo_category",
                description="Активирует категорию Комбо в 11:00 с понедельника по пятницу",
                schedule_type="weekly",
                hour=11,
                minute=0,
                day_of_week="1-5",
                enabled=True,
            )
            
            # Создаем задачу деактивации категории Комбо в будни
            PeriodicTask.objects.create(
                name="Деактивация категории Комбо (будни)",
                task="app_catalog.tasks.deactivate_combo_category",
                description="Деактивирует категорию Комбо в 17:00 с понедельника по пятницу",
                schedule_type="weekly",
                hour=17,
                minute=0,
                day_of_week="1-5",
                enabled=True,
            )
            
            # Создаем задачу деактивации категории Комбо в выходные
            PeriodicTask.objects.create(
                name="Деактивация категории Комбо (выходные)",
                task="app_catalog.tasks.deactivate_combo_category",
                description="Деактивирует категорию Комбо в 00:00 в субботу и воскресенье",
                schedule_type="weekly",
                hour=0,
                minute=0,
                day_of_week="0,6",
                enabled=True,
            )
            
            print("Созданы начальные периодические задачи")
    except Exception as e:
        print(f"Ошибка при создании начальных задач: {e}")
        # Не вызываем исключение, чтобы не блокировать запуск сервера
