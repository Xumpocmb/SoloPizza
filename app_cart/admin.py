from django.contrib import admin

from app_cart.models import CartItem


class AddonInline(admin.TabularInline):
    model = CartItem.addons.through
    extra = 0
    verbose_name = "Добавка"
    verbose_name_plural = "Добавки"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_info', 'quantity', 'total_price', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__username', 'item__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AddonInline]

    fieldsets = (
        (None, {
            'fields': ('user', 'item', 'item_variant', 'quantity')
        }),
        ('Дополнительные опции', {
            'fields': ('board', 'sauce'),
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
        if obj.board:
            info += f" | Борт: {obj.board.board.name}"
        if obj.sauce:
            info += f" | Соус: {obj.sauce.name}"
        if obj.addons.exists():
            addons = ", ".join(a.addon.name for a in obj.addons.all())
            info += f" | Добавки: {addons}"
        return info

    item_info.short_description = "Товар"

    def total_price(self, obj):
        return f"{obj.calculate_cart_total()} руб."

    total_price.short_description = "Сумма"

    def get_exclude(self, request, obj=None):
        return ['addons'] if obj else []
