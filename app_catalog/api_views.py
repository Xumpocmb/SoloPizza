from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from app_catalog.models import Product, PizzaSizes, BoardParams, AddonParams


def get_product_variants(request, product_id):
    """
    API-представление для получения вариантов продукта
    """
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all()
    
    variants_data = []
    for variant in variants:
        variant_data = {
            'id': variant.id,
            'name': f"{variant.value or ''} {variant.size.name if variant.size else ''} {variant.unit}".strip(),
            'price': float(variant.price),
        }
        
        if variant.size:
            variant_data['size'] = {
                'id': variant.size.id,
                'name': variant.size.name
            }
        
        variants_data.append(variant_data)
    
    return JsonResponse(variants_data, safe=False)


def get_size_boards(request, size_id):
    """
    API-представление для получения бортов для размера пиццы
    """
    size = get_object_or_404(PizzaSizes, id=size_id)
    board_params = BoardParams.objects.filter(size=size)
    
    boards_data = []
    for board_param in board_params:
        boards_data.append({
            'id': board_param.board.id,
            'name': board_param.board.name,
            'price': float(board_param.price)
        })
    
    return JsonResponse(boards_data, safe=False)


def get_size_addons(request, size_id):
    """
    API-представление для получения добавок для размера пиццы
    """
    size = get_object_or_404(PizzaSizes, id=size_id)
    addon_params = AddonParams.objects.filter(size=size)
    
    addons_data = []
    for addon_param in addon_params:
        addons_data.append({
            'id': addon_param.addon.id,
            'name': addon_param.addon.name,
            'price': float(addon_param.price)
        })
    
    return JsonResponse(addons_data, safe=False)