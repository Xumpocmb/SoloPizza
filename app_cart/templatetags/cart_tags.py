from django import template

register = template.Library()

@register.filter
def is_available_in_branch(cart_item, branch):
    return cart_item.item.category.branch.filter(id=branch.id).exists()