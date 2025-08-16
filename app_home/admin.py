from django.contrib import admin
from app_home.models import CafeBranch, CafeBranchPhone, Vacancy, VacancyApplication, Feedback, Discount


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['name', 'percent']
    search_fields = ['name']


class CafeBranchPhoneAdmin(admin.TabularInline):
    model = CafeBranchPhone
    extra = 1
    verbose_name = "Номер телефона"
    verbose_name_plural = "Номера телефонов"


class CafeBranchAdmin(admin.ModelAdmin):
    inlines = [CafeBranchPhoneAdmin]
    list_display = ['name', 'check_font_size', 'check_tape_width']
    search_fields = ['name']
    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "address", "is_active", "latitude", "longitude", "delivery_zone")
        }),
        ("Настройки печати чеков", {
            "fields": ("check_font_size", "check_tape_width")
        }),
    )

admin.site.register(CafeBranch, CafeBranchAdmin)


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "salary", "is_active", "created_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description")


@admin.register(VacancyApplication)
class VacancyApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "vacancy", "age", "phone", "experience_years", "created_at")
    list_filter = ("vacancy", "created_at", "experience_years")
    search_fields = ("name", "phone", "work_experience")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Основная информация", {
            "fields": ("vacancy", "name", "age", "phone", "created_at")
        }),
        ("Опыт работы", {
            "fields": ("experience_years", "work_experience")
        }),
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "phone", "message")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Информация", {
            "fields": ("name", "phone", "created_at")
        }),
        ("Вопрос/предложение", {
            "fields": ("message",)
        }),
    )
