from django.contrib import admin
from app_home.models import CafeBranch, CafeBranchPhone, Vacancy, VacancyApplication, Feedback, Discount, OrderAvailability, WorkingHours, Partner, SnowSettings, Marquee


@admin.register(SnowSettings)
class SnowSettingsAdmin(admin.ModelAdmin):
    list_display = ("is_enabled",)

    def has_add_permission(self, request):
        # Only allow one instance of SnowSettings
        if SnowSettings.objects.exists():
            return False
        return True


@admin.register(OrderAvailability)
class OrderAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("is_available", "updated_at")
    list_editable = ("is_available",)
    list_display_links = None  # Remove the link from the display to avoid confusion
    readonly_fields = ("updated_at",)
    fieldsets = (
        (None, {"fields": ("is_available",)}),
        ("Информация", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        # Only allow one instance of OrderAvailability
        if OrderAvailability.objects.exists():
            return False
        return True


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ["name", "percent"]
    search_fields = ["name"]


class CafeBranchPhoneAdmin(admin.TabularInline):
    model = CafeBranchPhone
    extra = 1
    verbose_name = "Номер телефона"
    verbose_name_plural = "Номера телефонов"


class CafeBranchAdmin(admin.ModelAdmin):
    inlines = [CafeBranchPhoneAdmin]
    list_display = ["name", "check_font_size", "check_tape_width"]
    search_fields = ["name"]
    fieldsets = (
        ("Основная информация", {"fields": ("name", "address", "is_active", "latitude", "longitude", "delivery_zone")}),
        ("Настройки печати чеков", {"fields": ("check_font_size", "check_tape_width")}),
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
        ("Основная информация", {"fields": ("vacancy", "name", "age", "phone", "created_at")}),
        ("Опыт работы", {"fields": ("experience_years", "work_experience")}),
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "phone", "message")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Информация", {"fields": ("name", "phone", "created_at")}),
        ("Вопрос/предложение", {"fields": ("message",)}),
    )


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ["branch", "get_day_of_week_display", "opening_time", "closing_time", "is_closed"]
    list_filter = ["branch", "day_of_week", "is_closed"]
    list_editable = ["opening_time", "closing_time", "is_closed"]
    search_fields = ["branch__name"]
    list_per_page = 50

    fieldsets = (
        (None, {"fields": ("branch", "day_of_week")}),
        ("Время работы", {"fields": ("opening_time", "closing_time", "is_closed"), "classes": ("collapse",) if False else ()}),
    )

    def get_day_of_week_display(self, obj):
        return obj.get_day_of_week_display()

    get_day_of_week_display.short_description = "День недели"


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "link")
    search_fields = ("name",)
    list_per_page = 20


@admin.register(Marquee)
class MarqueeAdmin(admin.ModelAdmin):
    list_display = ("text", "is_active")
    list_editable = ("is_active",)
    search_fields = ("text",)
    list_per_page = 20
