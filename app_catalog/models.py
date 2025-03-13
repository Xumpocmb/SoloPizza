from django.db import models
from app_home.models import CafeBranch


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название категории')
    image = models.ImageField(upload_to='category_images', blank=True, null=True, verbose_name='Изображение')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    branch = models.ManyToManyField(CafeBranch, blank=True, verbose_name='Филиалы')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    is_for_admin = models.BooleanField(default=False, verbose_name='Для администратора')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    time_update = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return f'Категория: {self.name}'


class Item(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)

    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    image = models.ImageField(upload_to='item_images', blank=True, null=True, verbose_name='Изображение')
    is_weekly_special = models.BooleanField(default=False, verbose_name='Пицца недели', blank=False, null=False)

    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')

    def __str__(self):
        return f'Категория: {self.category.name} | Товар: {self.name}'

    class Meta:
        db_table = 'items'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['id']


class PizzaSizes(models.Model):
    size = models.PositiveSmallIntegerField(verbose_name='Размер в см.', blank=True, null=True)
    slug = models.SlugField(max_length=3, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'pizza_sizes'
        verbose_name = 'Размер пиццы'
        verbose_name_plural = 'Размеры пиццы'

    def __str__(self):
        return f'Размер: {self.size} см.'


class CalconeSizes(models.Model):
    size = models.CharField(max_length=3, verbose_name='Размер', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'calcone_sizes'
        verbose_name = 'Размер кальцоне'
        verbose_name_plural = 'Размеры кальцоне'

    def __str__(self):
        return f'Размер: {self.size}'


class ItemParams(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True)
    count = models.DecimalField(max_digits=3, decimal_places=1, verbose_name='Количество в шт.', blank=True, null=True)
    size = models.ForeignKey(PizzaSizes, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Размер')
    code_size = models.ForeignKey(CalconeSizes, on_delete=models.SET_NULL, verbose_name='Размер для кальцоне', blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Вес в гр.', blank=True, null=True)
    volume = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Объем в л.', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена в руб.', blank=False, null=False)


    class Meta:
        db_table = 'item_params'
        verbose_name = 'Параметры товара'
        verbose_name_plural = 'Параметры товара'

    def __str__(self):
        parts = [f"Тов.: {self.item.name}" if self.item else "Без названия"]

        if self.size:
            parts.append(f"Разм.: {self.size.size}")
        if self.weight:
            parts.append(f"Вес: {self.weight} г")
        if self.volume:
            parts.append(f"Объем: {self.volume} л")
        if self.count:
            parts.append(f"Кол.: {self.count} шт")
        if self.code_size:
            parts.append(f"Разм.: {self.code_size.size}")

        parts.append(f"Цена: {self.price} руб")
        return " | ".join(parts)


class PizzaBoard(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название борта')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'pizza_boards'
        verbose_name = 'Борт для пиццы'
        verbose_name_plural = 'Борт для пиццы'

    def __str__(self):
        return f'Борт для пиццы: {self.name}'


class BoardParams(models.Model):
    board = models.ForeignKey(PizzaBoard, on_delete=models.CASCADE, blank=True, null=True)
    size = models.ForeignKey(PizzaSizes, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Размер')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена в руб.', blank=False, null=False)

    class Meta:
        db_table = 'board_params'
        verbose_name = 'Параметры борта'
        verbose_name_plural = 'Параметры борта'

    def __str__(self):
        return f'Параметры для: {self.board.name}'


class PizzaSauce(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название соуса')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'pizza_sauces'
        verbose_name = 'Соус-основа пиццы'
        verbose_name_plural = 'Соус-основа пиццы'

    def __str__(self):
        return f'Соус для пиццы: {self.name}'


class Topping(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название шапочки')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'toppings'
        verbose_name = 'Шапочка для запеченных роллов'
        verbose_name_plural = 'Шапочки для запеченных роллов'

    def __str__(self):
        return f'Шапочка для запеченных роллов: {self.name}'


class PizzaAddons(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название добавки')
    image = models.ImageField(upload_to='pizza_addons/', blank=True, null=True, verbose_name='Изображение')
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'pizza_addons'
        verbose_name = 'Добавка для пиццы'
        verbose_name_plural = 'Добавки для пиццы'

    def __str__(self):
        return f'Добавка для пиццы: {self.name}'


class AddonParams(models.Model):
    addon = models.ForeignKey(PizzaAddons, on_delete=models.CASCADE, related_name='params', blank=True, null=True)
    size = models.ForeignKey(PizzaSizes, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Размер')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена в руб.', blank=False, null=False)

    class Meta:
        db_table = 'addon_params'
        verbose_name = 'Параметры добавки'
        verbose_name_plural = 'Параметры добавки'

    def __str__(self):
        return f'Параметры для: {self.addon.name}'


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

