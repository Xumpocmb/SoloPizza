from django.apps import AppConfig


class AppCatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_catalog'
    verbose_name = 'Каталог'
    
    def ready(self):
        import app_catalog.signals  # Импортируем сигналы при запуске приложения
