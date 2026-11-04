from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin

from app_home.models import CafeBranch, CafeBranchPhone, Vacancy, VacancyApplication, Feedback, Discount, WorkingHours, Partner, Announcement, Certificate, InfoPage, SiteSettings


@admin.register(Discount)
class DiscountAdmin(TabbedTranslationAdmin):
    list_display = ["name", "percent"]
    search_fields = ["name"]


class CafeBranchPhoneAdmin(admin.TabularInline):
    model = CafeBranchPhone
    extra = 1
    verbose_name = "Номер телефона"
    verbose_name_plural = "Номера телефонов"


class CafeBranchAdmin(TabbedTranslationAdmin):
    inlines = [CafeBranchPhoneAdmin]
    list_display = ["name", "check_digit", "check_font_size", "check_tape_width"]
    search_fields = ["name"]
    fieldsets = (
        ("Основная информация", {"fields": ("name", "address", "is_active", "latitude", "longitude", "delivery_zone")}),
        ("Настройки печати чеков", {"fields": ("check_digit", "check_font_size", "check_tape_width")}),
    )


admin.site.register(CafeBranch, CafeBranchAdmin)


@admin.register(Vacancy)
class VacancyAdmin(TabbedTranslationAdmin):
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
class PartnerAdmin(TabbedTranslationAdmin):
    list_display = ("name", "link")
    search_fields = ("name",)
    list_per_page = 20


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("text", "is_active")
    list_editable = ("is_active",)
    search_fields = ("text",)
    list_per_page = 20


@admin.register(InfoPage)
class InfoPageAdmin(TabbedTranslationAdmin):
    list_display = ("promo_heading", "steps_title")
    search_fields = ("promo_heading", "steps_title")

    def has_add_permission(self, request):
        # Контент страницы «Информация» хранится в единственной записи.
        if InfoPage.objects.exists():
            return False
        return True


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Логотип", {"fields": ("logo", "logo_alt")}),
        ("Оформление заказов", {"fields": ("orders_available",)}),
        ("Снег", {"fields": ("snow_enabled",)}),
        ("Предпросмотр", {"fields": ("logo_preview", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("logo_preview", "updated_at")

    @admin.display(description="Текущий логотип")
    def logo_preview(self, obj):
        if not obj or not obj.logo:
            return "Логотип не загружен — используется стандартный"
        return format_html(
            '<img src="{}" alt="{}" style="max-height: 80px; width: auto;">',
            obj.logo.url,
            obj.logo_alt,
        )

    def has_add_permission(self, request):
        # Настройки сайта хранятся в единственной записи.
        if SiteSettings.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        # Удаление ломает singleton: запись пересоздастся с настройками по умолчанию.
        return False


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("code", "created_at", "expires_at", "is_used", "used_at")
    list_filter = ("is_used", "created_at", "expires_at")
    search_fields = ("code",)
    readonly_fields = ("code", "created_at", "expires_at")
    list_per_page = 20

    def has_view_permission(self, request, obj=None):
        # Only allow staff and superusers to view certificates
        return request.user.is_staff or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Only allow staff and superusers to change certificates
        return request.user.is_staff or request.user.is_superuser

    def has_add_permission(self, request):
        # Only allow staff and superusers to add certificates
        return request.user.is_staff or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Only allow staff and superusers to delete certificates
        return request.user.is_staff or request.user.is_superuser
