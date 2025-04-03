from django.db import models
from app_home.models import CafeBranch
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название категории')
    image = models.ImageField(upload_to='category_images', blank=True, null=True, verbose_name='Изображение')
    branch = models.ManyToManyField(CafeBranch, blank=True, verbose_name='Филиалы')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    is_for_admin = models.BooleanField(default=False, verbose_name='Для администратора',
                                       help_text='Установите, если хотите скрыть эту категорию от пользователей. Она будет видна только администраторам')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    time_update = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return f'Категория: {self.name}'

class Item(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Категория')

    name = models.CharField(max_length=100, verbose_name='Название товара')
    description = models.TextField(verbose_name='Описание товара')
    image = models.ImageField(upload_to='item_images', blank=True, null=True, verbose_name='Изображение')
    is_weekly_special = models.BooleanField(default=False, verbose_name='Акция: Пицца недели', blank=False, null=False)

    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return f'Категория: {self.category.name} | Товар: {self.name}'

    class Meta:
        db_table = 'items'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['id']

class ItemSizes(models.Model):
    name = models.CharField(default='Размер', max_length=50, verbose_name='Размер')

    class Meta:
        db_table = 'item_sizes'
        verbose_name = 'Размер пиццы и кальцоне'
        verbose_name_plural = 'Размеры пиццы и кальцоне'

    def __str__(self):
        return f'Размер: {self.name}'

class ItemParams(models.Model):
    UNIT_CHOICES = [
        ('pcs', 'шт'),
        ('cm', 'см'),
        ('ml', 'мл'),
        ('g', 'гр'),
        ('l', 'л'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='Товар')
    size = models.ForeignKey(ItemSizes, on_delete=models.CASCADE, verbose_name='Размер для пиццы или кальцоне', blank=True, null=True)
    value = models.CharField(null=True, blank=True, max_length=50, verbose_name='Значение')
    unit = models.CharField(null=True, blank=True, choices=UNIT_CHOICES, max_length=50, verbose_name='Единица измерения')
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2, verbose_name='Цена в руб.', blank=False, null=False)

    class Meta:
        db_table = 'item_params'
        verbose_name = 'Параметры товара'
        verbose_name_plural = 'Параметры товара'

    def __str__(self):
        return f'Параметры товара {self.item.name}'

class PizzaBoard(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название борта')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'pizza_boards'
        verbose_name = 'Борт для пиццы'
        verbose_name_plural = 'Борты для пиццы'

    def __str__(self):
        return f'Борт: {self.name}'

class BoardParams(models.Model):
    board = models.ForeignKey(PizzaBoard, on_delete=models.CASCADE, verbose_name='Борт')
    size = models.ForeignKey(ItemSizes, on_delete=models.CASCADE, verbose_name='Размер')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена в руб.')

    def __str__(self):
        return f'Борт: {self.board.name} | Размер: {self.size.name} | Цена: {self.price}'

    class Meta:
        db_table = 'board_params'
        verbose_name = 'Параметр борта'
        verbose_name_plural = 'Параметры бортов'

class PizzaAddon(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название добавки')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        db_table = 'pizza_addons'
        verbose_name = 'Добавка для пиццы'
        verbose_name_plural = 'Добавки для пиццы'

    def __str__(self):
        return f'Добавка: {self.name}'

class AddonParams(models.Model):
    addon = models.ForeignKey(PizzaAddon, on_delete=models.CASCADE, verbose_name='Добавка')
    size = models.ForeignKey(ItemSizes, on_delete=models.CASCADE, verbose_name='Размер')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена в руб.')

    def get_display_name(self):
        """Возвращает человекочитаемое описание добавки."""
        return f'{self.addon.name} ({self.size.name}): {self.price} руб.'

    def __str__(self):
        return self.get_display_name()


@receiver(post_delete, sender=Category)
@receiver(post_delete, sender=Item)
def delete_image_file(sender, instance, **kwargs):
    """Удаляет файл изображения при удалении объекта."""
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)