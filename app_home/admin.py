from django.contrib import admin
from app_home.models import CafeBranch, CafeBranchPhone, Vacancy


class CafeBranchPhoneAdmin(admin.TabularInline):
    model = CafeBranchPhone
    extra = 1
    verbose_name = "Номер телефона"
    verbose_name_plural = "Номера телефонов"


class CafeBranchAdmin(admin.ModelAdmin):
    inlines = [CafeBranchPhoneAdmin]
    list_display = ['name']
    search_fields = ['name']

admin.site.register(CafeBranch, CafeBranchAdmin)


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "salary", "is_active", "created_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description")
