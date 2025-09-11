from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from app_catalog.models import Product, PizzaSizes, BoardParams, AddonParams, Category, ProductVariant, PizzaBoard, PizzaAddon, PizzaSauce
from .serializers import (CategorySerializer, ProductSerializer, ProductVariantSerializer,
                         BoardParamsSerializer, AddonParamsSerializer, PizzaSauceSerializer,
                         BoardSerializer, AddonSerializer, PizzaSizesSerializer)


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
    
    serializer = BoardParamsSerializer(board_params, many=True)
    return JsonResponse(serializer.data, safe=False)


def get_size_addons(request, size_id):
    """
    API-представление для получения добавок для размера пиццы
    """
    size = get_object_or_404(PizzaSizes, id=size_id)
    addon_params = AddonParams.objects.filter(size=size)
    
    serializer = AddonParamsSerializer(addon_params, many=True)
    return JsonResponse(serializer.data, safe=False)


def get_variant_data(request, variant_id):
    """
    API-представление для получения полных данных варианта товара
    включая цену, соусы, доски и добавки
    """
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product
    
    # Базовые данные варианта
    variant_data = {
        'id': variant.id,
        'price': float(variant.price),
        'size_name': variant.size.name if variant.size else None,
        'value': variant.value,
        'unit': variant.get_unit_display() if variant.unit else None,
    }
    
    # Проверяем, является ли товар пиццей, кальцоне или комбо
    is_pizza_or_combo = product.category.name in ["Пицца", "Кальцоне", "Комбо"]
    
    if is_pizza_or_combo and variant.size:
        # Получаем соусы
        sauces = PizzaSauce.objects.filter(is_active=True)
        variant_data['sauces'] = [{
            'id': sauce.id,
            'name': sauce.name,
            'price': 0.0
        } for sauce in sauces]
        
        # Получаем доски для размера
        boards = BoardParams.objects.filter(size=variant.size)
        variant_data['boards'] = [{
            'id': board.id,  # Возвращаем ID BoardParams, чтобы форма получала корректный идентификатор
            'name': board.board.name,
            'price': float(board.price)
        } for board in boards]
        
        # Получаем добавки для размера
        addons = AddonParams.objects.filter(size=variant.size)
        variant_data['addons'] = [{
            'id': addon.id,  # Возвращаем ID AddonParams, чтобы форма получала корректный идентификатор
            'name': addon.addon.name,
            'price': float(addon.price)
        } for addon in addons]
    else:
        variant_data['sauces'] = []
        variant_data['boards'] = []
        variant_data['addons'] = []
    
    # Проверяем, является ли товар комбо
    if product.category.name == "Комбо":
        # Получаем напитки (предполагаем, что они в категории "Напитки")
        try:
            drinks_category = Category.objects.get(name="Напитки")
            drinks = Product.objects.filter(category=drinks_category, is_active=True)
            variant_data['drinks'] = [{
                'id': drink.id,
                'name': drink.name,
                'price': float(drink.price) if hasattr(drink, 'price') else 0
            } for drink in drinks]
        except Category.DoesNotExist:
            variant_data['drinks'] = []
    else:
        variant_data['drinks'] = []
    
    return JsonResponse(variant_data)


# DRF API Views
class CategoryListView(generics.ListAPIView):
    """
    API endpoint для получения списка категорий
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # Удалено поле 'parent', так как оно отсутствует в модели Category
    search_fields = ['name']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class CategoryDetailView(generics.RetrieveAPIView):
    """
    API endpoint для получения детальной информации о категории
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class ProductListView(generics.ListAPIView):
    """
    API endpoint для получения списка продуктов
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'price']


class ProductDetailView(generics.RetrieveAPIView):
    """
    API endpoint для получения детальной информации о продукте
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]


class ProductVariantListView(generics.ListAPIView):
    """
    API endpoint для получения списка вариантов продуктов
    """
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'size']


class PizzaSauceListView(generics.ListAPIView):
    """
    API endpoint для получения списка соусов для пиццы
    """
    queryset = PizzaSauce.objects.filter(is_active=True)
    serializer_class = PizzaSauceSerializer
    permission_classes = [permissions.AllowAny]


class PizzaBoardListView(generics.ListAPIView):
    """
    API endpoint для получения списка бортов для пиццы
    """
    queryset = PizzaBoard.objects.filter(is_active=True)
    serializer_class = BoardSerializer
    permission_classes = [permissions.AllowAny]


class PizzaAddonListView(generics.ListAPIView):
    """
    API endpoint для получения списка добавок для пиццы
    """
    queryset = PizzaAddon.objects.filter(is_active=True)
    serializer_class = AddonSerializer
    permission_classes = [permissions.AllowAny]


class PizzaSizesListView(generics.ListAPIView):
    """
    API endpoint для получения списка размеров пиццы
    """
    queryset = PizzaSizes.objects.all()
    serializer_class = PizzaSizesSerializer
    permission_classes = [permissions.AllowAny]


# Вторая функция get_size_addons удалена, так как она дублирует функционал
# первой функции get_size_addons, которая использует сериализатор AddonParamsSerializer
