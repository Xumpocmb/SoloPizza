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
    cache_key = f'views.decorators.cache.cache_page.{catalog_url}'
    cache.delete(cache_key)
    
    # Очищаем кеш для страницы категории
    if instance.slug:
        category_url = reverse('app_catalog:category_detail', kwargs={'slug': instance.slug})
        cache_key = f'views.decorators.cache.cache_page.{category_url}'
        cache.delete(cache_key)


@receiver([post_save, post_delete], sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    """
    Очищает кеш товаров при изменении или удалении товара.
    """
    # Очищаем кеш для страницы товара
    if instance.slug:
        product_url = reverse('app_catalog:item_detail', kwargs={'slug': instance.slug})
        cache_key = f'views.decorators.cache.cache_page.{product_url}'
        cache.delete(cache_key)
    
    # Очищаем кеш для страницы категории
    if instance.category and instance.category.slug:
        category_url = reverse('app_catalog:category_detail', kwargs={'slug': instance.category.slug})
        cache_key = f'views.decorators.cache.cache_page.{category_url}'
        cache.delete(cache_key)
    
    # Очищаем кеш для страницы каталога
    catalog_url = reverse('app_catalog:catalog')
    cache_key = f'views.decorators.cache.cache_page.{catalog_url}'
    cache.delete(cache_key)
    
    # Если это акционный товар, очищаем кеш для страницы акций
    if instance.is_weekly_special or kwargs.get('update_fields') and 'is_weekly_special' in kwargs.get('update_fields'):
        discounts_url = reverse('app_home:discounts')
        cache_key = f'views.decorators.cache.cache_page.{discounts_url}'
        cache.delete(cache_key)


@receiver([post_save, post_delete], sender=ProductVariant)
def clear_variant_cache(sender, instance, **kwargs):
    """
    Очищает кеш при изменении или удалении варианта товара.
    """
    # Очищаем кеш для страницы товара
    if instance.product and instance.product.slug:
        product_url = reverse('app_catalog:item_detail', kwargs={'slug': instance.product.slug})
        cache_key = f'views.decorators.cache.cache_page.{product_url}'
        cache.delete(cache_key)
    
    # Очищаем кеш для страницы категории
    if instance.product and instance.product.category and instance.product.category.slug:
        category_url = reverse('app_catalog:category_detail', kwargs={'slug': instance.product.category.slug})
        cache_key = f'views.decorators.cache.cache_page.{category_url}'
        cache.delete(cache_key)


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
    cache_key = f'views.decorators.cache.cache_page.{catalog_url}'
    cache.delete(cache_key)
    
    # Для очистки кеша всех страниц товаров нам нужно найти все товары и очистить их кеш
    # Вместо использования delete_pattern, который не поддерживается в RedisCache
    from app_catalog.models import Product
    for product in Product.objects.all():
        if product.slug:
            product_url = reverse('app_catalog:item_detail', kwargs={'slug': product.slug})
            cache_key = f'views.decorators.cache.cache_page.{product_url}'
            cache.delete(cache_key)


@receiver([post_save, post_delete], sender=RollTopping)
@receiver([post_save, post_delete], sender=IceCreamTopping)
def clear_toppings_cache(sender, instance, **kwargs):
    """
    Очищает кеш при изменении или удалении топпингов для роллов и мороженого.
    """
    # Очищаем кеш для всех страниц каталога
    catalog_url = reverse('app_catalog:catalog')
    cache_key = f'views.decorators.cache.cache_page.{catalog_url}'
    cache.delete(cache_key)
    
    # Очищаем кеш для категорий роллов и мороженого
    from app_catalog.models import Category
    for category in Category.objects.filter(name__in=['Роллы', 'Мороженое']):
        if category.slug:
            category_url = reverse('app_catalog:category_detail', kwargs={'slug': category.slug})
            cache_key = f'views.decorators.cache.cache_page.{category_url}'
            cache.delete(cache_key)
            
    # Очищаем кеш для всех товаров в этих категориях
    from app_catalog.models import Product
    for product in Product.objects.filter(category__name__in=['Роллы', 'Мороженое']):
        if product.slug:
            product_url = reverse('app_catalog:item_detail', kwargs={'slug': product.slug})
            cache_key = f'views.decorators.cache.cache_page.{product_url}'
            cache.delete(cache_key)