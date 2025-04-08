from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    """
    Инлайн для отображения товаров в заказе.
    """
    model = OrderItem
    extra = 0  # Не добавляем пустые строки для новых товаров
    readonly_fields = ('item', 'item_params', 'quantity', 'price')  # Делаем поля только для чтения

    def has_add_permission(self, request, obj=None):
        """
        Запрещаем добавление новых товаров через админку.
        """
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Админка для модели Order.
    """
    list_display = (
        'id',
        'user',
        'status',
        'total_price',
        'created_at',
        'cafe_branch',
    )
    list_filter = ('status', 'cafe_branch', 'created_at')
    search_fields = ('id', 'user__username', 'user__email', 'address')
    readonly_fields = ('created_at', 'updated_at', 'total_price')  # Делаем поля только для чтения
    inlines = [OrderItemInline]  # Добавляем инлайн для товаров в заказе

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'status', 'total_price', 'created_at', 'updated_at'),
        }),
        ('Адрес доставки', {
            'fields': ('latitude', 'longitude', 'address', 'apartment', 'entrance', 'floor'),
        }),
        ('Дополнительно', {
            'fields': ('comment', 'cafe_branch'),
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Переопределяем метод сохранения, чтобы обновить связанную логику (если необходимо).
        """
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """
        Оптимизируем запросы для улучшения производительности.
        """
        return super().get_queryset(request).select_related('user', 'cafe_branch').prefetch_related('items')
