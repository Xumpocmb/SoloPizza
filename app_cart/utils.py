def validate_cart_items_for_branch(cart_items, branch):
    """Проверяет все товары в корзине на доступность в филиале"""
    unavailable_items = []
    for item in cart_items:
        if not item.is_available_in_branch(branch):
            unavailable_items.append(item)
    return unavailable_items