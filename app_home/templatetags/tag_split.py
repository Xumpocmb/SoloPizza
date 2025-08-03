from django import template

register = template.Library()


@register.filter
def split(value, arg):
    """
    Разделяет строку по разделителю
    Пример: {{ value|split:"," }}
    """
    return value.split(arg)


@register.filter
def strip(value):
    """
    Убирает лишние пробелы в начале и конце строки
    """
    if isinstance(value, str):
        return value.strip()
    return value
