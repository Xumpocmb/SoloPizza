def validate_cart_items_for_branch(cart_items, branch):
    """Проверяет все товары в корзине на доступность в филиале"""
    unavailable_items = []
    for item_data in cart_items:
        # item_data is a dictionary from SessionCart, where 'object' holds the Product instance
        if not item_data['product'].is_available_in_branch(branch):
            unavailable_items.append(item_data['product'])
    return unavailable_items
