from django.db.models import Min
from django.shortcuts import render, get_object_or_404

from app_catalog.models import Category, Product, AddonParams, BoardParams, ProductVariant, PizzaSauce


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    items = (
        Product.objects.filter(category=category)
        .annotate(min_price=Min('variants__price'))
    )
    context = {
        'title': f'Solo Pizza | Категория: {category.name}',
        'category': category,
        'items': items,
    }
    return render(request, 'app_catalog/category_detail.html', context=context)


def item_detail(request, slug):
    """Страница карточки товара без формы, просто отображаем данные."""
    item = get_object_or_404(Product, slug=slug)
    variants = ProductVariant.objects.filter(product=item)

    selected_variant_id = request.GET.get("size")

    if selected_variant_id and selected_variant_id.isdigit():
        try:
            selected_variant = variants.get(id=selected_variant_id)
        except ProductVariant.DoesNotExist:
            selected_variant = None
    else:
        selected_variant = variants.first()

    # Инициализируем переменные по умолчанию
    sauces = []
    boards = []
    addons = []
    drinks = []
    min_price = None
    is_pizza_or_calzone = False

    if selected_variant:
        is_pizza_or_calzone = item.category.name in ["Пицца", "Кальцоне"]

        min_price = selected_variant.price

        # Получаем размеры в зависимости от типа товара
        if is_pizza_or_calzone:
            sauces = PizzaSauce.objects.all() if is_pizza_or_calzone else []
            boards = BoardParams.objects.filter(size=selected_variant.size) if selected_variant.size else []
            addons = AddonParams.objects.filter(size=selected_variant.size) if selected_variant.size else []
            

        if item.category.name in ["Комбо"]:
            is_pizza_or_calzone = True
            boards = BoardParams.objects.filter(size=selected_variant.size) if selected_variant.size else []
            drinks = ["Кола 1л.", "Sprite 1л."]
            sauces = []
            addons = []

    context = {
        "item": item,
        "variants": variants,
        "selected_variant": selected_variant,
        "sauces": sauces,
        "boards": boards,
        "addons": addons,
        "drinks": drinks,
        "min_price": min_price,
        "is_pizza_or_calzone": is_pizza_or_calzone,
    }

    return render(request, "app_catalog/item_detail.html", context)
