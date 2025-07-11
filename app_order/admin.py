# # app_orders/admin.py
# from django.contrib import admin
# from .models import Order, OrderItem, OrderItemAddon

# class OrderItemAddonInline(admin.TabularInline):
#     model = OrderItemAddon
#     extra = 0

# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 0
#     inlines = [OrderItemAddonInline]

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'status', 'total_price', 'created_at')
#     list_filter = ('status', 'payment_method', 'created_at')
#     search_fields = ('user__username', 'phone_number', 'address')
#     inlines = [OrderItemInline]
#     readonly_fields = ('created_at', 'updated_at')
