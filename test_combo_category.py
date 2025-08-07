#!/usr/bin/env python
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SoloPizza.settings')
django.setup()

# Импорт после настройки Django
from app_catalog.models import Category
from app_catalog.tasks import activate_combo_category, deactivate_combo_category


def test_combo_category_tasks():
    """
    Функция для тестирования задач активации и деактивации категории "Комбо".
    """
    # Проверяем существование категории "Комбо"
    try:
        combo_category = Category.objects.get(name="Комбо")
        print(f"Текущий статус категории 'Комбо': {'активна' if combo_category.is_active else 'неактивна'}")
        
        # Тестируем активацию
        print("\nТестирование активации категории 'Комбо'...")
        result = activate_combo_category()
        print(f"Результат: {result}")
        
        # Проверяем статус после активации
        combo_category.refresh_from_db()
        print(f"Статус после активации: {'активна' if combo_category.is_active else 'неактивна'}")
        
        # Тестируем деактивацию
        print("\nТестирование деактивации категории 'Комбо'...")
        result = deactivate_combo_category()
        print(f"Результат: {result}")
        
        # Проверяем статус после деактивации
        combo_category.refresh_from_db()
        print(f"Статус после деактивации: {'активна' if combo_category.is_active else 'неактивна'}")
        
    except Category.DoesNotExist:
        print("Категория 'Комбо' не найдена в базе данных.")
        print("Создаем категорию 'Комбо' для тестирования...")
        
        # Создаем категорию для тестирования
        combo_category = Category.objects.create(
            name="Комбо",
            is_active=False,
            slug="kombo"
        )
        print(f"Категория 'Комбо' создана со статусом: {'активна' if combo_category.is_active else 'неактивна'}")
        
        # Повторяем тестирование
        test_combo_category_tasks()


if __name__ == "__main__":
    print("Начало тестирования задач для категории 'Комбо'...\n")
    test_combo_category_tasks()
    print("\nТестирование завершено.")