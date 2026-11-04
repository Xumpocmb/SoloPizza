from django import template
from app_home.models import SiteSettings

register = template.Library()

@register.simple_tag
def are_orders_available():
    """Проверить, доступно ли оформление заказов"""
    return SiteSettings.is_orders_available()
