from django.contrib import admin

from app_cart.models import CartItem


class AddonInline(admin.TabularInline):
    model = CartItem.addons.through
    extra = 0
    verbose_name = "Добавка"
    verbose_name_plural = "Добавки"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'item_info', 'quantity', 'total_price', 'created_at')
    list_filter = ('session_key', 'created_at')
    search_fields = ('session_key', 'item__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AddonInline]

    fieldsets = (
        (None, {
            'fields': ('session_key', 'item', 'item_variant', 'quantity')
        }),
        ('Дополнительные опции', {
            'fields': ('board1', 'board2', 'sauce'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def item_info(self, obj):
        size = obj.get_size_display()
        info = f"{obj.item.name}"
        if size:
            info += f" ({size})"
        if obj.board1:
            info += f" | Борт1: {obj.board1.board.name}"
        if obj.board2:
            info += f" | Борт2: {obj.board2.board.name}"
        if obj.sauce:
            info += f" | Соус: {obj.sauce.name}"
        if obj.addons.exists():
            addons = ", ".join(a.addon.name for a in obj.addons.all())
            info += f" | Добавки: {addons}"
        return info

    item_info.short_description = "Товар"

    def total_price(self, obj):
        return f"{obj.calculate_cart_item_total()} руб."

    total_price.short_description = "Сумма"

    def get_exclude(self, request, obj=None):
        return ['addons'] if obj else []
