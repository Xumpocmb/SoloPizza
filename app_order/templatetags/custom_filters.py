from django import template

register = template.Library()


@register.filter(name="get")
def get(dictionary, key):
    """
    Фильтр для получения значения из словаря по ключу.
    """
    return dictionary.get(key)


@register.filter(name="format_price")
def format_price(value):
    """
    Форматирует цену, добавляя "руб." и заменяя запятую на точку.
    """
    if value is None:
        return "0.00 руб."
    # Преобразуем в Decimal для правильной обработки строк и чисел
    from decimal import Decimal

    try:
        if isinstance(value, str):
            value = Decimal(value.replace(",", "."))
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))
    except:
        # Если не удалось преобразовать, возвращаем исходное значение как строку
        return f"{value} руб."
    return f"{value:.2f} руб."


@register.filter(name="get_first_value")
def get_first_value(dictionary):
    """
    Фильтр для получения первого значения из словаря.
    """
    if dictionary:
        for key, value in dictionary.items():
            return value
    return None


@register.filter(name="get_dict_value")
def get_dict_value(obj, key):
    """
    Фильтр для получения значения из объекта (словаря или атрибута) по ключу.
    """
    if hasattr(obj, "__getitem__"):
        try:
            return obj[key]
        except (KeyError, TypeError):
            return None
    elif hasattr(obj, key):
        return getattr(obj, key)
    return None
