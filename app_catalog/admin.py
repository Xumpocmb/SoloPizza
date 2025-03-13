from django.contrib import admin
from app_catalog.models import Category, Item, ItemParams, PizzaBoard, CafeBranch, PizzaSizes, PizzaSauce, Topping, \
    PizzaAddons, BoardParams, AddonParams, IceCreamTopping, CalconeSizes


class ItemParamsInline(admin.TabularInline):
    model = ItemParams
    extra = 1


class BoardParamsInline(admin.TabularInline):
    model = BoardParams
    extra = 1


class AddonParamsInline(admin.TabularInline):
    model = AddonParams
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_active']
    list_editable = ['is_active']
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    inlines = [ItemParamsInline]
    list_display = ['__str__', 'is_active']
    search_fields = ['name']
    list_filter = ['category', 'is_active']
    prepopulated_fields = {"slug": ("name",)}


@admin.register(PizzaBoard)
class PizzaBoardAdmin(admin.ModelAdmin):
    inlines = [BoardParamsInline]
    list_display = ['__str__']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(PizzaSizes)
class PizzaSizesAdmin(admin.ModelAdmin):
    list_display = ['size']
    prepopulated_fields = {"slug": ("size",)}


@admin.register(PizzaSauce)
class PizzaSauceAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(Topping)
class ToppingAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(PizzaAddons)
class PizzaAddonsAdmin(admin.ModelAdmin):
    inlines = [AddonParamsInline]
    list_display = ['name']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(IceCreamTopping)
class IceCreamToppingAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(CalconeSizes)
class CalconeSizes(admin.ModelAdmin):
    list_display = ['size']
    prepopulated_fields = {"slug": ("size",)}
    search_fields = ['size']
