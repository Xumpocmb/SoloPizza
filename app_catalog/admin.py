from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductVariant, PizzaSizes, PizzaBoard, PizzaSauce, BoardParams, PizzaAddon, AddonParams, RollTopping, IceCreamTopping, ComboDrinks


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_image', 'is_active', 'is_for_admin', 'order')
    list_editable = ('is_active', 'is_for_admin', 'order')
    list_filter = ('is_active', 'is_for_admin')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "Нет изображения"

    display_image.short_description = 'Изображение'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('value', 'size', 'unit', 'price')
    ordering = ('price',)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'is_weekly_special', 'has_base_sauce', 'has_border', 'has_addons', 'has_drink', 'has_additional_sauces', 'created_at']
    list_filter = ['category', 'is_active', 'is_weekly_special', 'has_base_sauce', 'has_border', 'has_addons', 'has_drink', 'has_additional_sauces']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline]
    readonly_fields = ['created_at']


class PizzaSizesAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class BoardParamsInline(admin.TabularInline):
    model = BoardParams
    extra = 1


class PizzaBoardAdmin(admin.ModelAdmin):
    inlines = [BoardParamsInline]
    list_display = ['__str__']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


class PizzaSauceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class AddonParamsInline(admin.TabularInline):
    model = AddonParams
    extra = 1


class PizzaAddonAdmin(admin.ModelAdmin):
    inlines = [AddonParamsInline]
    list_display = ['__str__']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(PizzaSizes, PizzaSizesAdmin)
admin.site.register(PizzaBoard, PizzaBoardAdmin)
admin.site.register(PizzaSauce, PizzaSauceAdmin)
admin.site.register(PizzaAddon, PizzaAddonAdmin)


@admin.register(IceCreamTopping)
class IceCreamToppingAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(RollTopping)
class ToppingAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


@admin.register(ComboDrinks)
class ComboDrinksAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
