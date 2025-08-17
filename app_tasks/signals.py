from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PeriodicTask


@receiver(post_save, sender=PeriodicTask)
def update_celery_task_signal(sender, instance, created, **kwargs):
    """
    Обновляет или создает задачу Celery Beat при сохранении модели PeriodicTask
    """
    from .tasks import update_celery_task
    # Запускаем задачу асинхронно
    update_celery_task.delay(instance.id)


@receiver(post_delete, sender=PeriodicTask)
def delete_celery_task_signal(sender, instance, **kwargs):
    """
    Удаляет задачу Celery Beat при удалении модели PeriodicTask
    """
    from .tasks import delete_celery_task
    # Запускаем задачу асинхронно
    delete_celery_task.delay(instance.id)