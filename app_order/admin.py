from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'variant', 'quantity', 'get_price']
    fields = ['product', 'variant', 'quantity', 'get_price']

    def get_price(self, obj):
        return f"{obj.calculate_item_total()['final_total']:.2f} руб."

    get_price.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer_name',
        'phone_number',
        'get_status_display',
        'get_delivery_type_display',
        'total_price',
        'created_at'
    ]
    list_filter = [
        'status',
        'delivery_type',
        'payment_method',
        'created_at'
    ]
    search_fields = [
        'id',
        'customer_name',
        'phone_number'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'display_order_summary'
    ]
    inlines = [OrderItemInline]
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'status',
                'customer_name',
                'phone_number',
                'branch',
                ('delivery_type', 'address'),
                ('payment_method', 'payment_status'),
                'comment',
                'display_order_summary'
            )
        }),
        ('Финансовая информация', {
            'fields': (
                ('subtotal', 'discount_amount'),
                ('delivery_cost', 'total_price'),
            )
        }),
        ('Дополнительно', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def display_order_summary(self, obj):
        items = obj.items.all()
        summary = []
        for item in items:
            summary.append(
                f"{item.product.name} x{item.quantity} - {item.calculate_item_total()['final_total']:.2f} руб.")
        return "\n".join(summary)

    display_order_summary.short_description = 'Состав заказа'