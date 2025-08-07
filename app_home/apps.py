from django.apps import AppConfig


class AppHomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_home'
    verbose_name = 'Главная'
    
    def ready(self):
        # Импортируем сигналы при загрузке приложения
        import app_home.signals
