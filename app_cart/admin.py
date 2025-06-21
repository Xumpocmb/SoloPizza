# from django.contrib import admin
# from app_cart.models import CartItem
#
# class CartItemAdmin(admin.ModelAdmin):
#     # Поля, которые будут отображаться в списке объектов
#     list_display = ('user', 'item', 'item_params', 'quantity', 'total_price')
#
#     # Поля, по которым можно фильтровать записи
#     list_filter = ('user', 'item', 'item_params')
#
#     # Поля, по которым можно выполнять поиск
#     search_fields = ('user__username', 'item__name', 'item_params__size__name')
#
#     # Поля, которые можно редактировать прямо в списке
#     list_editable = ('quantity',)
#
#     # Поля, которые будут отображаться в форме редактирования
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('user', 'item', 'item_params', 'quantity')
#         }),
#         ('Дополнительные параметры', {
#             'fields': ('board', 'addons'),
#         }),
#     )
#
#     # Метод для расчета общей цены товара
#     @admin.display(description='Общая цена')
#     def total_price(self, obj):
#         base_price = obj.item_params.price
#         board_price = obj.board.price if obj.board else 0
#         addons_price = sum(addon.price for addon in obj.addons.all())
#         return base_price + board_price + addons_price
#
# # Регистрация модели
# admin.site.register(CartItem, CartItemAdmin)