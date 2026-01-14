from django import forms
from django.contrib import admin
from .models import Order, OrderItem, OrderStatistic


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        total_price = cleaned_data.get('total_price', 0)

        if payment_method == 'split':
            cash_amount = cleaned_data.get('cash_amount', 0)
            card_amount = cleaned_data.get('card_amount', 0)
            noname_amount = cleaned_data.get('noname_amount', 0)

            split_total = cash_amount + card_amount + noname_amount

            # Check if the split payment total matches the order total
            if abs(split_total - total_price) >= 0.01:
                raise forms.ValidationError(
                    f'Сумма раздельной оплаты ({split_total:.2f} руб.) '
                    f'не совпадает с итоговой суммой заказа ({total_price:.2f} руб.).'
                )

        return cleaned_data


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
    form = OrderAdminForm
    list_display = [
        'id',
        'user',
        'session_key',
        'guest_token',
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
        'created_at',
        'user',
    ]
    search_fields = [
        'id',
        'user__username',
        'session_key',
        'guest_token',
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
                'user',
                'session_key',
                'guest_token',
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
        ('Раздельная оплата', {
            'fields': (
                ('cash_amount', 'card_amount', 'noname_amount'),
            ),
            'classes': ('collapse',)  # Makes this section collapsible
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


@admin.register(OrderStatistic)
class OrderStatisticAdmin(admin.ModelAdmin):
    list_display = ('date', 'orders_count', 'total_cash', 'total_card', 'total_amount')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    ordering = ('-date',)

