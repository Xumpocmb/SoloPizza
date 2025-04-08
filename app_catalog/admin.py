from django.contrib import admin
from app_catalog.models import Category, Item, ItemParams, ItemSizes, BoardParams, PizzaBoard, AddonParams, PizzaAddon, \
    PizzaSauce


class ItemParamsInline(admin.TabularInline):
    model = ItemParams
    extra = 1

class BoardParamsInline(admin.TabularInline):
    model = BoardParams
    extra = 1

@admin.register(PizzaBoard)
class PizzaBoardAdmin(admin.ModelAdmin):
    inlines = [BoardParamsInline]
    list_display = ['__str__']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(PizzaSauce)
class PizzaSauceAdmin(admin.ModelAdmin):
    list_display = ['__str__']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']

class AddonParamsInline(admin.TabularInline):
    model = AddonParams
    extra = 1

@admin.register(PizzaAddon)
class PizzaAddonAdmin(admin.ModelAdmin):
    inlines = [AddonParamsInline]
    list_display = ['__str__']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']

@admin.register(ItemSizes)
class ItemSizesAdmin(admin.ModelAdmin):
    list_display = ('__str__',)


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


