from django import template
from django.utils.safestring import mark_safe

from app_home.schema import render_json_ld, restaurant_schema

register = template.Library()


@register.simple_tag(takes_context=True)
def restaurant_json_ld(context):
    """Микроразметка Schema.org.

    Филиалы и выбранный филиал берутся из контекста (site_context_processor),
    поэтому разметка всегда соответствует тому, что видит посетитель.
    Пример: {% restaurant_json_ld %}
    """
    return mark_safe(render_json_ld(restaurant_schema(context.get("branches") or [], context.get("selected_branch"))))
