from django.db.models import Min
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from app_catalog.models import Category, Product, AddonParams, BoardParams, ProductVariant, PizzaSauce, PizzaAddon, PizzaBoard, PizzaSizes, ComboDrinks


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    items = Product.objects.filter(category=category, is_active=True).prefetch_related("variants").annotate(min_price=Min("variants__price"))

    breadcrumbs = [
        {"title": "Главная", "url": "/"},
        {"title": "Каталог", "url": reverse("app_catalog:catalog")},
        {"title": category.name, "url": category.get_absolute_url()},
    ]
    context = {
        "title": f"Solo Pizza | Категория: {category.name}",
        "category": category,
        "items": items,
        "breadcrumbs": breadcrumbs,
        "weekly_pizza_discount": "Пицца недели",
    }

    if request.user.is_staff:
        sauces = PizzaSauce.objects.filter(is_active=True)
        boards = BoardParams.objects.all()
        addons = AddonParams.objects.all()
        drinks = ComboDrinks.objects.filter(is_active=True)

        context.update(
            {
                "sauces": sauces,
                "boards": boards,
                "addons": addons,
                "drinks": drinks,
            }
        )

        template_name = "app_catalog/category_detail_admin.html"
    else:
        template_name = "app_catalog/category_detail.html"

    return render(request, template_name, context=context)


def item_detail(request, slug):
    """Страница карточки товара без формы, просто отображаем данные."""
    item = get_object_or_404(Product, slug=slug)
    variants = ProductVariant.objects.filter(product=item)

    selected_variant_id = request.GET.get("size")
    selected_variant = None

    if selected_variant_id and selected_variant_id.isdigit():
        try:
            selected_variant = variants.get(id=selected_variant_id)
        except ProductVariant.DoesNotExist:
            selected_variant = variants.first()
    else:
        selected_variant = variants.first()

    # Инициализируем переменные по умолчанию
    sauces = []
    boards = []
    addons = []
    drinks = []
    min_price = None

    # Определяем параметры на основе выбранных опций товара
    if selected_variant:
        min_price = selected_variant.price

        # Проверяем параметры товара
        if item.has_base_sauce:
            sauces = list(PizzaSauce.objects.filter(is_active=True))

        if item.has_border and selected_variant.size:
            boards = list(BoardParams.objects.filter(size=selected_variant.size))

        if item.has_addons and selected_variant.size:
            addons = list(AddonParams.objects.filter(size=selected_variant.size))

    # Обработка напитков
    if item.has_drink:
        drinks = list(ComboDrinks.objects.filter(is_active=True))

    # Обработка дополнительных соусов
    if item.has_additional_sauces:
        additional_sauces = list(PizzaSauce.objects.filter(is_active=True))
        sauces.extend(additional_sauces)

    # Обработка комбо-наборов
    if item.is_combo:
        size_32 = PizzaSizes.objects.filter(name="32").first()
        if size_32:
            boards = list(BoardParams.objects.filter(size=size_32))

    category = item.category
    breadcrumbs = [
        {"title": "Главная", "url": "/"},
        {"title": "Каталог", "url": reverse("app_catalog:catalog")},
        {"title": category.name, "url": category.get_absolute_url()},
        {"title": item.name, "url": "#"},
    ]

    # Формируем контекст
    context = {
        "item": item,
        "variants": variants,
        "selected_variant": selected_variant,
        "sauces": sauces,
        "boards": boards,
        "addons": addons,
        "drinks": drinks,
        "min_price": min_price,
        "breadcrumbs": breadcrumbs,
        "category": category,
    }

    return render(request, "app_catalog/item_detail.html", context)


def catalog_view(request):

    context = {}

    breadcrumbs = [
        {"title": "Главная", "url": "/"},
        {"title": "Каталог", "url": reverse("app_catalog:catalog")},
    ]

    # Добавляем общие параметры каталога
    context = {
        "breadcrumbs": breadcrumbs,
        "has_base_sauce_options": PizzaSauce.objects.filter(is_active=True).exists(),
        "has_border_options": PizzaBoard.objects.filter(is_active=True).exists(),
        "has_addon_options": PizzaAddon.objects.filter(is_active=True).exists(),
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

    if product.has_base_sauce:
        # Получаем соусы
        sauces = PizzaSauce.objects.filter(is_active=True)
        variant_data["sauces"] = [{"id": sauce.id, "name": sauce.name, "price": 0.0} for sauce in sauces]
    else:
        variant_data["sauces"] = []

    if product.is_combo:
        size_32 = PizzaSizes.objects.filter(name="32").first()
        if size_32:
            boards = list(BoardParams.objects.filter(size=size_32))
    else:
        boards = BoardParams.objects.filter(size=variant.size)
        variant_data["boards"] = [
            {"id": board.id, "name": board.board.name, "price": float(board.price)} for board in boards  # Возвращаем ID BoardParams, чтобы форма получала корректный идентификатор
        ]

    if product.has_addons:
        addons = AddonParams.objects.filter(size=variant.size)
        variant_data["addons"] = [
            {"id": addon.id, "name": addon.addon.name, "price": float(addon.price)} for addon in addons  # Возвращаем ID AddonParams, чтобы форма получала корректный идентификатор
        ]
    else:

        variant_data["addons"] = []

    if product.has_drink:
        # Получаем напитки из модели ComboDrinks
        combo_drinks = ComboDrinks.objects.filter(is_active=True)
        variant_data["drinks"] = [{"id": drink.id, "name": drink.name, "price": 0.0} for drink in combo_drinks]
    else:
        variant_data["drinks"] = []

    return JsonResponse(variant_data)


def get_product_variants(request, product_id):
    """
    API-представление для получения вариантов продукта.
    """
    product = get_object_or_404(Product, id=product_id)
    variants = ProductVariant.objects.filter(product=product)
    variants_data = [
        {
            "id": variant.id,
            "name": str(variant),
            "size": {"id": variant.size.id, "name": variant.size.name} if variant.size else None,
        }
        for variant in variants
    ]
    return JsonResponse(variants_data, safe=False)
