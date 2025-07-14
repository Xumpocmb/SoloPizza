import os

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import slugify

from app_home.models import CafeBranch


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название категории')
    image = models.ImageField(upload_to='category_images', blank=True, null=True, verbose_name='Изображение')
    branch = models.ManyToManyField(CafeBranch, blank=True, verbose_name='Филиалы')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    is_for_admin = models.BooleanField(default=False, verbose_name='Для администратора',
                                       help_text='Установите, если хотите скрыть эту категорию от пользователей. Она будет видна только администраторам')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order']

    def __str__(self):
        return f'Категория: {self.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL-адрес', unique=True)
    description = models.TextField('Описание', null=True, blank=True)
    image = models.ImageField(upload_to='item_images', blank=True, null=True, verbose_name='Изображение')
    is_weekly_special = models.BooleanField(default=False, verbose_name='Акция: Пицца недели', blank=False, null=False)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        db_table = 'products'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PizzaSizes(models.Model):
    name = models.CharField(default='Размер', max_length=50, verbose_name='Размер')

    class Meta:
        db_table = 'pizza_sizes'
        verbose_name = 'Размер пиццы и кальцоне'
        verbose_name_plural = 'Размеры пиццы и кальцоне'

    def __str__(self):
        return f'Размер: {self.name}'


class ProductVariant(models.Model):
    UNIT_CHOICES = [
        ('pcs', 'шт'),
        ('cm', 'см'),
        ('ml', 'мл'),
        ('g', 'гр'),
        ('l', 'л'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    value = models.CharField(null=True, blank=True, max_length=50, verbose_name='Значение', help_text="Значение для товаров")
    size = models.ForeignKey(PizzaSizes, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Размер', help_text="Размер для пиццы и кальцоне")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs', verbose_name='Единица измерения')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)

    is_spicy = models.BooleanField('Острый', default=False, blank=True)
    is_alcoholic = models.BooleanField('Алкогольный', default=False, blank=True)
    is_combo = models.BooleanField('Комбо-набор', default=False, blank=True)
    is_sweet = models.BooleanField('Сладкий', default=False, blank=True)

    class Meta:
        verbose_name = 'Вариант товара'
        verbose_name_plural = 'Варианты товаров'

    def __str__(self):
        return f"{self.product.name} - ({self.price}₽)"


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


class PizzaSauce(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название соуса')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'pizza_sauces'
        verbose_name = 'Соус для пиццы'
        verbose_name_plural = 'Соусы для пиццы'

    def __str__(self):
        return f'Соус для пиццы: {self.name}'


class BoardParams(models.Model):
    board = models.ForeignKey(PizzaBoard, on_delete=models.CASCADE, verbose_name='Борт')
    size = models.ForeignKey(PizzaSizes, on_delete=models.CASCADE, verbose_name='Размер')
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
    size = models.ForeignKey(PizzaSizes, on_delete=models.CASCADE, verbose_name='Размер')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена в руб.')

    class Meta:
        db_table = 'addon_params'
        verbose_name = 'Параметр добавки'
        verbose_name_plural = 'Параметры добавок'

    def get_display_name(self):
        """Возвращает человекочитаемое описание добавки."""
        return f'{self.addon.name} ({self.size.name}): {self.price} руб.'

    def __str__(self):
        return self.get_display_name()


class RollTopping(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название шапочки')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'roll_toppings'
        verbose_name = 'Шапочка для запеченных роллов'
        verbose_name_plural = 'Шапочки для запеченных роллов'

    def __str__(self):
        return f'Шапочка для запеченных роллов: {self.name}'


class IceCreamTopping(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'ice_cream_toppings'
        verbose_name = 'Топпинг для мороженного'
        verbose_name_plural = 'Топпинги для мороженного'

    def __str__(self):
        return f'Топпинг для мороженного: {self.name}'

    def save(self, *args, **kwargs):
        self.slug = slugify(f"topping-{self.name}")
        super().save(*args, **kwargs)


@receiver(post_delete, sender=Category)
@receiver(post_delete, sender=Product)
def delete_image_file(sender, instance, **kwargs):
    """Удаляет файл изображения при удалении объекта."""
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
