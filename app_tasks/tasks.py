from celery import shared_task
from django.utils import timezone
from django_celery_beat.models import PeriodicTask as CeleryPeriodicTask, CrontabSchedule, IntervalSchedule
import json

@shared_task
def update_celery_task(task_id):
    """
    Обновляет задачу Celery Beat на основе модели PeriodicTask
    """
    from app_tasks.models import PeriodicTask
    
    try:
        task = PeriodicTask.objects.get(id=task_id)
        
        # Получаем или создаем расписание в зависимости от типа
        if task.schedule_type == 'daily':
            # Ежедневное расписание
            schedule, _ = CrontabSchedule.objects.get_or_create(
                hour=task.hour,
                minute=task.minute,
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
        elif task.schedule_type == 'weekly':
            # Еженедельное расписание
            schedule, _ = CrontabSchedule.objects.get_or_create(
                hour=task.hour,
                minute=task.minute,
                day_of_week=task.day_of_week or '*',
                day_of_month='*',
                month_of_year='*',
            )
        elif task.schedule_type == 'monthly':
            # Ежемесячное расписание
            schedule, _ = CrontabSchedule.objects.get_or_create(
                hour=task.hour,
                minute=task.minute,
                day_of_week='*',
                day_of_month=task.day_of_month or '1',
                month_of_year='*',
            )
        elif task.schedule_type == 'custom':
            # Пользовательское расписание (используем crontab выражение)
            parts = task.crontab_expression.split()
            if len(parts) == 5:
                minute, hour, day_of_month, month_of_year, day_of_week = parts
                schedule, _ = CrontabSchedule.objects.get_or_create(
                    minute=minute,
                    hour=hour,
                    day_of_month=day_of_month,
                    month_of_year=month_of_year,
                    day_of_week=day_of_week,
                )
            else:
                raise ValueError(f"Неверный формат crontab выражения: {task.crontab_expression}")
        else:
            raise ValueError(f"Неизвестный тип расписания: {task.schedule_type}")
        
        # Подготавливаем аргументы
        kwargs = {}
        if task.kwargs:
            try:
                kwargs = json.loads(task.kwargs)
            except json.JSONDecodeError:
                kwargs = {}
        
        args = []
        if task.args:
            try:
                args = json.loads(task.args)
                if not isinstance(args, list):
                    args = []
            except json.JSONDecodeError:
                args = []
        
        # Получаем или создаем задачу Celery Beat
        celery_task_name = f"app_tasks.{task.id}"
        celery_task, created = CeleryPeriodicTask.objects.update_or_create(
            name=celery_task_name,
            defaults={
                'task': task.task,
                'crontab': schedule if isinstance(schedule, CrontabSchedule) else None,
                'interval': schedule if isinstance(schedule, IntervalSchedule) else None,
                'args': json.dumps(args),
                'kwargs': json.dumps(kwargs),
                'enabled': task.enabled,
                'description': task.description,
            }
        )
        
        # Обновляем информацию о задаче
        if not created:
            task.last_updated = timezone.now()
            task.save(update_fields=['last_updated'])
            
        return f"Задача {task.name} успешно {'создана' if created else 'обновлена'}"
    
    except Exception as e:
        return f"Ошибка при обновлении задачи {task_id}: {str(e)}"

@shared_task
def delete_celery_task(task_id):
    """
    Удаляет задачу Celery Beat
    """
    try:
        celery_task_name = f"app_tasks.{task_id}"
        CeleryPeriodicTask.objects.filter(name=celery_task_name).delete()
        return f"Задача {task_id} успешно удалена"
    except Exception as e:
        return f"Ошибка при удалении задачи {task_id}: {str(e)}"

@shared_task
def run_task_now(task_id):
    """
    Запускает задачу немедленно
    """
    from app_tasks.models import PeriodicTask
    from celery import current_app
    
    try:
        task = PeriodicTask.objects.get(id=task_id)
        
        # Подготавливаем аргументы
        kwargs = {}
        if task.kwargs:
            try:
                kwargs = json.loads(task.kwargs)
            except json.JSONDecodeError:
                kwargs = {}
        
        args = []
        if task.args:
            try:
                args = json.loads(task.args)
                if not isinstance(args, list):
                    args = []
            except json.JSONDecodeError:
                args = []
        
        # Запускаем задачу
        task_result = current_app.send_task(task.task, args=args, kwargs=kwargs)
        
        # Обновляем информацию о последнем запуске
        task.last_run = timezone.now()
        task.save(update_fields=['last_run'])
        
        return f"Задача {task.name} запущена, ID результата: {task_result.id}"
    
    except Exception as e:
        return f"Ошибка при запуске задачи {task_id}: {str(e)}"