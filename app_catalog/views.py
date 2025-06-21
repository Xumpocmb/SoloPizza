from django.db.models import Min
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from app_catalog.models import Category, Product, AddonParams, BoardParams, PizzaSizes, ProductVariant, PizzaSauce
from app_catalog.models import Category


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

    # Получаем все варианты товара (ProductVariant) по полю product
    variants = ProductVariant.objects.filter(product=item)

    selected_variant_id = request.GET.get('size')

    if selected_variant_id and selected_variant_id.isdigit():
        try:
            selected_variant = variants.get(id=selected_variant_id)
        except ProductVariant.DoesNotExist:
            selected_variant = None
    else:
        selected_variant = variants.first()

    if selected_variant:
        sauces = PizzaSauce.objects.all() if item.category.name in ["Пицца", "Кальцоне"] else []

        # Пример: если размер хранится как строка в `value`, например "30 см"
        size_name = selected_variant.value

        boards = (
            BoardParams.objects.filter(size__name=size_name)
            if item.category.name == "Пицца"
            else []
        )
        addons = (
            AddonParams.objects.filter(size__name=size_name)
            if item.category.name == "Пицца"
            else []
        )
        drinks = ["Кола 1л.", "Sprite 1л."] if item.category.name in ["Комбо"] else []
        min_price = selected_variant.price
    else:
        sauces = []
        boards = []
        addons = []
        drinks = []
        min_price = None

    context = {
        "item": item,
        "variants": variants,
        "selected_variant": selected_variant,
        "sauces": sauces,
        "boards": boards,
        "addons": addons,
        "drinks": drinks,
        "min_price": min_price,
    }

    return render(request, "app_catalog/item_detail.html", context)


def get_product_data(request, slug):
    print("get_product_data")
    """Возвращает данные о размерах, бортах и добавках для карточки товара."""
    item = get_object_or_404(Product, slug=slug)  # Теперь ищем товар по slug

    # Получаем размеры и цены товара
    sizes = ProductVariant.objects.filter(item=item)
    sizes_data = [
        {
            "id": size.size.id,
            "name": f"{size.size.name} {size.value if size.value else ''} {size.unit if size.unit else ''}",
            "price": float(size.price),
            "default": idx == 0  # Первый размер по умолчанию
        }
        for idx, size in enumerate(sizes)
    ]

    # Получаем борты и их цены для первого размера
    first_size = sizes.first().size if sizes.exists() else None
    boards = BoardParams.objects.filter(size=first_size) if first_size else []
    boards_data = [
        {
            "id": board.board.id,
            "name": board.board.name,
            "price": float(board.price)
        }
        for board in boards
    ]

    # Получаем добавки и их цены для первого размера
    addons = AddonParams.objects.filter(size=first_size) if first_size else []
    addons_data = [
        {
            "id": addon.addon.id,
            "name": addon.addon.name,
            "price": float(addon.price)
        }
        for addon in addons
    ]

    return JsonResponse({
        "sizes": sizes_data,
        "boards": boards_data,
        "addons": addons_data
    })

def update_prices(request):
    print("update_prices")
    """Обновляет цены борта и добавок при изменении размера товара."""
    size_id = request.GET.get('size')
    size = get_object_or_404(PizzaSizes, id=size_id)

    boards = BoardParams.objects.filter(size=size)
    boards_data = [
        {
            "id": board.board.id,
            "name": board.board.name,
            "price": float(board.price)
        }
        for board in boards
    ]

    addons = AddonParams.objects.filter(size=size)
    addons_data = [
        {
            "id": addon.addon.id,
            "name": addon.addon.name,
            "price": float(addon.price)
        }
        for addon in addons
    ]

    return JsonResponse({
        "boards": boards_data,
        "addons": addons_data
    })
