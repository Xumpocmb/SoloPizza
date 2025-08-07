from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.urls import reverse

from app_catalog.models import (Category, Product, ProductVariant, PizzaSizes, 
                              PizzaBoard, PizzaSauce, PizzaAddon, BoardParams, 
                              AddonParams, RollTopping, IceCreamTopping)


@receiver([post_save, post_delete], sender=Category)
def clear_category_cache(sender, instance, **kwargs):
    """
    Очищает кеш категорий при изменении или удалении категории.
    """
    # Очищаем кеш для страницы каталога
    catalog_url = reverse('app_catalog:catalog')
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{catalog_url}*')
    
    # Очищаем кеш для страницы категории
    if instance.slug:
        category_url = reverse('app_catalog:category_detail', kwargs={'slug': instance.slug})
        cache.delete_pattern(f'views.decorators.cache.cache_page.*.{category_url}*')


@receiver([post_save, post_delete], sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    """
    Очищает кеш товаров при изменении или удалении товара.
    """
    # Очищаем кеш для страницы товара
    if instance.slug:
        product_url = reverse('app_catalog:item_detail', kwargs={'slug': instance.slug})
        cache.delete_pattern(f'views.decorators.cache.cache_page.*.{product_url}*')
    
    # Очищаем кеш для страницы категории
    if instance.category and instance.category.slug:
        category_url = reverse('app_catalog:category_detail', kwargs={'slug': instance.category.slug})
        cache.delete_pattern(f'views.decorators.cache.cache_page.*.{category_url}*')
    
    # Очищаем кеш для страницы каталога
    catalog_url = reverse('app_catalog:catalog')
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{catalog_url}*')
    
    # Если это акционный товар, очищаем кеш для страницы акций
    if instance.is_weekly_special or kwargs.get('update_fields') and 'is_weekly_special' in kwargs.get('update_fields'):
        discounts_url = reverse('app_home:discounts')
        cache.delete_pattern(f'views.decorators.cache.cache_page.*.{discounts_url}*')


@receiver([post_save, post_delete], sender=ProductVariant)
def clear_variant_cache(sender, instance, **kwargs):
    """
    Очищает кеш при изменении или удалении варианта товара.
    """
    # Очищаем кеш для страницы товара
    if instance.product and instance.product.slug:
        product_url = reverse('app_catalog:item_detail', kwargs={'slug': instance.product.slug})
        cache.delete_pattern(f'views.decorators.cache.cache_page.*.{product_url}*')
    
    # Очищаем кеш для страницы категории
    if instance.product and instance.product.category and instance.product.category.slug:
        category_url = reverse('app_catalog:category_detail', kwargs={'slug': instance.product.category.slug})
        cache.delete_pattern(f'views.decorators.cache.cache_page.*.{category_url}*')


@receiver([post_save, post_delete], sender=BoardParams)
@receiver([post_save, post_delete], sender=AddonParams)
@receiver([post_save, post_delete], sender=PizzaSauce)
@receiver([post_save, post_delete], sender=PizzaSizes)
@receiver([post_save, post_delete], sender=PizzaBoard)
@receiver([post_save, post_delete], sender=PizzaAddon)
def clear_pizza_params_cache(sender, instance, **kwargs):
    """
    Очищает кеш при изменении или удалении параметров пиццы (борты, добавки, соусы, размеры).
    """
    # Очищаем кеш для всех страниц товаров категории "Пицца"
    # Поскольку мы не знаем, какие конкретно товары затронуты, очищаем кеш для всех страниц каталога
    catalog_url = reverse('app_catalog:catalog')
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{catalog_url}*')
    
    # Также можно очистить кеш для всех страниц товаров
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{reverse("app_catalog:item_detail", kwargs={"slug": "*"})}*')


@receiver([post_save, post_delete], sender=RollTopping)
@receiver([post_save, post_delete], sender=IceCreamTopping)
def clear_toppings_cache(sender, instance, **kwargs):
    """
    Очищает кеш при изменении или удалении топпингов для роллов и мороженого.
    """
    # Очищаем кеш для всех страниц каталога
    catalog_url = reverse('app_catalog:catalog')
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{catalog_url}*')
    
    # Также можно очистить кеш для всех страниц товаров
    cache.delete_pattern(f'views.decorators.cache.cache_page.*.{reverse("app_catalog:item_detail", kwargs={"slug": "*"})}*')