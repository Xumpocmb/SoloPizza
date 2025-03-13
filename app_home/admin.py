from django.contrib import admin
from app_home.models import CafeBranch, CafeBranchPhone


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


