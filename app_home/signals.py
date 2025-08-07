from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.urls import reverse

from .models import CafeBranch, Vacancy
from app_catalog.models import Product
from .context_processors import CACHE_KEY_BRANCHES


@receiver([post_save, post_delete], sender=CafeBranch)
def clear_branch_cache(sender, instance, **kwargs):
    """
    Очищает кеш филиалов при изменении или удалении филиала.
    """
    # Удаляем кеш со списком филиалов
    cache.delete(CACHE_KEY_BRANCHES)
    
    # Также удаляем кеш категорий для этого филиала
    # Так как мы не знаем, какие пользователи (админы или обычные) просматривали категории,
    # удаляем кеш для обоих типов пользователей
    cache.delete(f'categories_branch_{instance.id}_admin_True')
    cache.delete(f'categories_branch_{instance.id}_admin_False')
    
    # Очищаем кеш для страницы контактов
    contacts_url = reverse('app_home:contacts')
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{contacts_url}*')


@receiver([post_save, post_delete], sender=Vacancy)
def clear_vacancy_cache(sender, instance, **kwargs):
    """
    Очищает кеш страниц, связанных с вакансиями, при изменении или удалении вакансии.
    """
    # Очищаем кеш для страницы списка вакансий
    vacancy_list_url = reverse('app_home:vacancy_list')
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{vacancy_list_url}*')
    
    # Очищаем кеш для детальной страницы вакансии
    vacancy_detail_url = reverse('app_home:vacancy_detail', kwargs={'vacancy_id': instance.id})
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{vacancy_detail_url}*')
    
    # Очищаем кеш для главной страницы, так как там тоже отображаются вакансии
    home_url = reverse('app_home:home')
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{home_url}*')


# Сигнал для очистки кеша при изменении товаров перенесен в app_catalog/signals.py