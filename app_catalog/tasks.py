from celery import shared_task
from django.utils import timezone
from .models import Category


@shared_task
def activate_combo_category():
    """
    Активирует категорию "Комбо" в рабочие дни с 11:00.
    """
    # Проверяем, что сегодня рабочий день (понедельник-пятница)
    weekday = timezone.now().weekday()
    if weekday < 5:  # 0-4 это понедельник-пятница
        try:
            combo_category = Category.objects.get(name="Комбо")
            combo_category.is_active = True
            combo_category.save()
            return f"Категория 'Комбо' активирована в {timezone.now()}"
        except Category.DoesNotExist:
            return "Категория 'Комбо' не найдена"
    return "Сегодня выходной, категория 'Комбо' не активирована"


@shared_task
def deactivate_combo_category():
    """
    Деактивирует категорию "Комбо" в 17:00 или в выходные дни.
    """
    try:
        combo_category = Category.objects.get(name="Комбо")
        combo_category.is_active = False
        combo_category.save()
        return f"Категория 'Комбо' деактивирована в {timezone.now()}"
    except Category.DoesNotExist:
        return "Категория 'Комбо' не найдена"