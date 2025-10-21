from django.db.models import Min
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from app_catalog.models import (Category, Product, AddonParams, BoardParams, 
                               ProductVariant, PizzaSauce, PizzaAddon, PizzaBoard, 
                               PizzaSizes)
from app_home.models import Discount


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    items = (
        Product.objects.filter(category=category)
        .annotate(min_price=Min('variants__price'))
    )

    breadcrumbs = [
        {'title': 'Главная', 'url': '/'},
        {'title': 'Каталог', 'url': reverse('app_catalog:catalog')},
        {'title': category.name, 'url': category.get_absolute_url()},
    ]

    sauces = PizzaSauce.objects.all()
    boards = BoardParams.objects.all()
    addons = AddonParams.objects.all()
    drinks = ["Кола 1л.", "Sprite 1л.", "Фанта 1л.", "Вода 0.5л."]
    
    # Получаем скидку для акции "Пицца недели"
    try:
        weekly_pizza_discount = Discount.objects.get(slug='picca-nedeli').percent
    except Discount.DoesNotExist:
        weekly_pizza_discount = 20  # Значение по умолчанию, если скидка не найдена

    context = {
        'title': f'Solo Pizza | Категория: {category.name}',
        'category': category,
        'items': items,
        "breadcrumbs": breadcrumbs,
        "sauces": sauces,
        "boards": boards,
        "addons": addons,
        "drinks": drinks,
        "weekly_pizza_discount": weekly_pizza_discount,
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
            sauces = PizzaSauce.objects.all()
            boards = BoardParams.objects.filter(size=selected_variant.size) if selected_variant.size else []
            addons = AddonParams.objects.filter(size=selected_variant.size) if selected_variant.size else []
            

        if item.category.name in ["Комбо"]:
            size_32 = PizzaSizes.objects.filter(name="32").first()
            if size_32:
                boards = BoardParams.objects.filter(size=size_32)
            else:
                boards = []
            drinks = ["Кола 1л.", "Sprite 1л.", "Фанта 1л."]

    category = item.category
    breadcrumbs = [
        {'title': 'Главная', 'url': '/'},
        {'title': 'Каталог', 'url': reverse('app_catalog:catalog')},
        {'title': category.name, 'url': category.get_absolute_url()},
        {'title': item.name, 'url': '#'}
    ]

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
        "breadcrumbs": breadcrumbs,
        "category": category,
    }

    return render(request, "app_catalog/item_detail.html", context)


def catalog_view(request):

    context = {}

    breadcrumbs = [
        {'title': 'Главная', 'url': '/'},
        {'title': 'Каталог', 'url': reverse('app_catalog:catalog')},
    ]

    context = {
        "breadcrumbs": breadcrumbs,
    }
    return render(request, "app_catalog/catalog.html", context=context)


def get_variant_data(request, variant_id):
    """
    API-представление для получения полных данных варианта товара
    включая цену, соусы, доски и добавки
    """
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product

    # Базовые данные варианта
    variant_data = {
        "id": variant.id,
        "price": float(variant.price),
        "size_name": variant.size.name if variant.size else None,
        "value": variant.value,
        "unit": variant.get_unit_display() if variant.unit else None,
    }

    # Проверяем, является ли товар пиццей, кальцоне или комбо
    is_pizza_or_combo = product.category.name in ["Пицца", "Кальцоне", "Комбо"]

    if is_pizza_or_combo and variant.size:
        # Получаем соусы
        sauces = PizzaSauce.objects.filter(is_active=True)
        variant_data["sauces"] = [{"id": sauce.id, "name": sauce.name, "price": 0.0} for sauce in sauces]

        # Получаем доски для размера
        boards = BoardParams.objects.filter(size=variant.size)
        variant_data["boards"] = [
            {"id": board.id, "name": board.board.name, "price": float(board.price)} for board in boards  # Возвращаем ID BoardParams, чтобы форма получала корректный идентификатор
        ]

        # Получаем добавки для размера
        addons = AddonParams.objects.filter(size=variant.size)
        variant_data["addons"] = [
            {"id": addon.id, "name": addon.addon.name, "price": float(addon.price)} for addon in addons  # Возвращаем ID AddonParams, чтобы форма получала корректный идентификатор
        ]
    else:
        variant_data["sauces"] = []
        variant_data["boards"] = []
        variant_data["addons"] = []

    # Проверяем, является ли товар комбо
    if product.category.name == "Комбо":
        # Получаем напитки (предполагаем, что они в категории "Напитки")
        try:
            drinks_category = Category.objects.get(name="Напитки")
            drinks = Product.objects.filter(category=drinks_category, is_active=True)
            variant_data["drinks"] = [{"id": drink.id, "name": drink.name, "price": float(drink.price) if hasattr(drink, "price") else 0} for drink in drinks]
        except Category.DoesNotExist:
            variant_data["drinks"] = []
    else:
        variant_data["drinks"] = []

    return JsonResponse(variant_data)
