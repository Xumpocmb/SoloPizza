from django import template

from app_home.models import SiteSettings
from app_home.working_hours import is_order_time_allowed

register = template.Library()


@register.simple_tag(takes_context=True)
def are_orders_available(context):
    """Доступно ли оформление заказов с учётом настроек сайта и графика филиала."""
    request = context.get("request")
    user = getattr(request, "user", None)

    if not SiteSettings.is_orders_available(user):
        return False

    branch = context.get("selected_branch")

    return is_order_time_allowed(branch, user)
