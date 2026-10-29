from django import template

register = template.Library()


@register.filter
def is_available_in_branch(product, branch):
    """Доступен ли товар в филиале.

    Логика живёт в Product.is_available_in_branch, чтобы не расходилась с
    проверкой в app_cart.utils.validate_cart_items_for_branch.
    """
    return product.is_available_in_branch(branch)
