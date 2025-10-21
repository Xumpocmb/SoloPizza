from celery import shared_task
from django.utils import timezone
from .models import Category


@shared_task
def activate_combo_category():
    """
    Активирует категорию "Комбо"
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
    Деактивирует категорию "Комбо"
    """
    try:
        combo_category = Category.objects.get(name="Комбо")
        combo_category.is_active = False
        combo_category.save()
        return f"Категория 'Комбо' деактивирована в {timezone.now()}"
    except Category.DoesNotExist:
        return "Категория 'Комбо' не найдена"


@shared_task
def disable_weekly_special_for_all_products():
    """
    Отключает акцию "Пицца недели" для всех товаров.
    """
    from .models import Product
    updated_count = Product.objects.filter(is_weekly_special=True).update(is_weekly_special=False)
    return f"Отключена акция 'Пицца недели' для {updated_count} товаров."
