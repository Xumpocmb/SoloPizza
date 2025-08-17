from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppTasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_tasks'
    verbose_name = _('Управление задачами')
    
    def ready(self):
        # Импортируем сигналы при загрузке приложения
        import app_tasks.signals
