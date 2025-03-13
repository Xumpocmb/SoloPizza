from django.db import models


class CafeBranch(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название филиала")
    address = models.CharField(max_length=200, verbose_name="Адрес")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        db_table = 'branches'
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'

    def __str__(self):
        return f'Филиал: {self.name}'


class CafeBranchPhone(models.Model):
    branch = models.ForeignKey(CafeBranch, on_delete=models.CASCADE, related_name='branch_phones', verbose_name="Филиал")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер телефона")
