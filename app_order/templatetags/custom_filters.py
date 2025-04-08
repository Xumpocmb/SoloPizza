from django import template

register = template.Library()

@register.filter(name='get')
def get(dictionary, key):
    """
    Фильтр для получения значения из словаря по ключу.
    """
    return dictionary.get(key)