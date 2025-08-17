from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib import messages

from .models import PeriodicTask
from .tasks import run_task_now


@admin.register(PeriodicTask)
class PeriodicTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'task', 'schedule_type', 'get_schedule_display', 'enabled', 'last_run']
    list_filter = ['enabled', 'schedule_type', 'task']
    search_fields = ['name', 'description']
    readonly_fields = ['last_run', 'date_created', 'date_updated']
    fieldsets = [
        (None, {
            'fields': ['name', 'task', 'description', 'enabled']
        }),
        (_('Расписание'), {
            'fields': ['schedule_type', 'hour', 'minute', 'day_of_week', 'day_of_month']
        }),
        (_('Аргументы'), {
            'fields': ['args', 'kwargs'],
            'classes': ['collapse']
        }),
        (_('Информация'), {
            'fields': ['last_run', 'date_created', 'date_updated'],
            'classes': ['collapse']
        }),
    ]
    actions = ['enable_tasks', 'disable_tasks', 'run_tasks_now']
    
    def get_schedule_display(self, obj):
        """Отображение расписания в удобном формате"""
        if obj.schedule_type == 'daily':
            return f"Ежедневно в {obj.hour:02d}:{obj.minute:02d}"
        elif obj.schedule_type == 'weekly':
            days = {
                '0': 'Воскресенье',
                '1': 'Понедельник',
                '2': 'Вторник',
                '3': 'Среда',
                '4': 'Четверг',
                '5': 'Пятница',
                '6': 'Суббота',
                '1-5': 'Будни',
                '0,6': 'Выходные',
            }
            day_display = days.get(obj.day_of_week, obj.day_of_week)
            return f"{day_display} в {obj.hour:02d}:{obj.minute:02d}"
        elif obj.schedule_type == 'monthly':
            return f"{obj.day_of_month} числа каждого месяца в {obj.hour:02d}:{obj.minute:02d}"
        else:
            return f"Пользовательское: {obj.hour:02d}:{obj.minute:02d}, {obj.day_of_week}, {obj.day_of_month}"
    
    get_schedule_display.short_description = _('Расписание')
    
    def enable_tasks(self, request, queryset):
        """Включить выбранные задачи"""
        updated = queryset.update(enabled=True)
        self.message_user(request, _(f'Включено {updated} задач'), messages.SUCCESS)
    
    enable_tasks.short_description = _('Включить выбранные задачи')
    
    def disable_tasks(self, request, queryset):
        """Выключить выбранные задачи"""
        updated = queryset.update(enabled=False)
        self.message_user(request, _(f'Выключено {updated} задач'), messages.SUCCESS)
    
    disable_tasks.short_description = _('Выключить выбранные задачи')
    
    def run_tasks_now(self, request, queryset):
        """Запустить выбранные задачи немедленно"""
        count = 0
        for task in queryset:
            try:
                # Запускаем задачу асинхронно
                run_task_now.delay(task.id)
                
                # Обновляем время последнего запуска
                task.last_run = timezone.now()
                task.save(update_fields=['last_run'])
                
                count += 1
            except Exception as e:
                self.message_user(
                    request, 
                    _(f'Ошибка при запуске задачи "{task.name}": {str(e)}'), 
                    messages.ERROR
                )
        
        self.message_user(request, _(f'Запущено {count} задач'), messages.SUCCESS)
    
    run_tasks_now.short_description = _('Запустить выбранные задачи сейчас')
