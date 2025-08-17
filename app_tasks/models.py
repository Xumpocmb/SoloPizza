from django.db import models
from django.utils.translation import gettext_lazy as _


class PeriodicTask(models.Model):
    """Модель для хранения периодических задач"""
    TASK_CHOICES = [
        ('app_catalog.tasks.activate_combo_category', 'Активировать категорию Комбо'),
        ('app_catalog.tasks.deactivate_combo_category', 'Деактивировать категорию Комбо'),
        ('app_order.tasks.clear_orders', 'Очистить список заказов'),
    ]
    
    SCHEDULE_TYPE_CHOICES = [
        ('daily', 'Ежедневно'),
        ('weekly', 'Еженедельно'),
        ('monthly', 'Ежемесячно'),
        ('custom', 'Пользовательское расписание'),
    ]
    
    name = models.CharField(_('Название'), max_length=200)
    task = models.CharField(_('Задача'), max_length=200, choices=TASK_CHOICES)
    description = models.TextField(_('Описание'), blank=True)
    
    # Расписание
    schedule_type = models.CharField(_('Тип расписания'), max_length=20, choices=SCHEDULE_TYPE_CHOICES, default='daily')
    hour = models.IntegerField(_('Час'), default=0)
    minute = models.IntegerField(_('Минута'), default=0)
    day_of_week = models.CharField(_('День недели'), max_length=20, blank=True, 
                                help_text=_('Формат: 0-6, где 0=Воскресенье, 1=Понедельник, ..., 6=Суббота. Пример: 1-5 для будних дней'))
    day_of_month = models.CharField(_('День месяца'), max_length=10, blank=True,
                                 help_text=_('Формат: 1-31. Оставьте пустым, если не используется'))
    
    # Статус
    enabled = models.BooleanField(_('Включено'), default=True)
    last_run = models.DateTimeField(_('Последний запуск'), null=True, blank=True)
    
    # Аргументы
    args = models.TextField(_('Аргументы'), blank=True, 
                          help_text=_('Аргументы в формате JSON. Пример: ["arg1", "arg2"]'))
    kwargs = models.TextField(_('Именованные аргументы'), blank=True,
                            help_text=_('Аргументы в формате JSON. Пример: {"key1": "value1"}'))
    
    date_created = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    date_updated = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('Периодическая задача')
        verbose_name_plural = _('Периодические задачи')
        ordering = ['name']
    
    def __str__(self):
        return self.name
