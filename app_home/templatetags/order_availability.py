from django import template
from app_home.models import OrderAvailability

register = template.Library()

@register.simple_tag
def are_orders_available():
    """Проверить, доступно ли оформление заказов"""
    return OrderAvailability.is_orders_available()
