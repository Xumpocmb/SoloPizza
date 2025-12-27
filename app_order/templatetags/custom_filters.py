from django import template

register = template.Library()

@register.filter(name='get')
def get(dictionary, key):
    """
    Фильтр для получения значения из словаря по ключу.
    """
    return dictionary.get(key)

@register.filter(name='format_price')
def format_price(value):
    """
    Форматирует цену, добавляя "руб." и заменяя запятую на точку.
    """
    if value is None:
        return "0.00 руб."
    return f"{value:.2f} руб.".replace(',', '.')