from django.apps import AppConfig


class AppOrderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_order'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
