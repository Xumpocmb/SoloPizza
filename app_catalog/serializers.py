from rest_framework import serializers
from .models import Category, Product, ProductVariant, PizzaSizes, PizzaBoard, PizzaAddon, BoardParams, AddonParams, PizzaSauce

class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий товаров"""
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'parent', 'is_active')

class PizzaSizesSerializer(serializers.ModelSerializer):
    """Сериализатор для размеров пиццы"""
    class Meta:
        model = PizzaSizes
        fields = ('id', 'name', 'diameter')

class BoardSerializer(serializers.ModelSerializer):
    """Сериализатор для бортов пиццы"""
    class Meta:
        model = PizzaBoard
        fields = ('id', 'name', 'slug', 'is_active')

class AddonSerializer(serializers.ModelSerializer):
    """Сериализатор для добавок к пицце"""
    class Meta:
        model = PizzaAddon
        fields = ('id', 'name', 'slug', 'is_active')

class ProductVariantSerializer(serializers.ModelSerializer):
    """Сериализатор для вариантов продукта"""
    size = PizzaSizesSerializer(read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = ('id', 'product', 'size', 'value', 'unit', 'price', 'old_price', 'weight')

class BoardParamsSerializer(serializers.ModelSerializer):
    """Сериализатор для параметров бортов пиццы"""
    board = BoardSerializer(read_only=True)
    size = PizzaSizesSerializer(read_only=True)
    
    class Meta:
        model = BoardParams
        fields = ('id', 'board', 'size', 'price')

class AddonParamsSerializer(serializers.ModelSerializer):
    """Сериализатор для параметров добавок к пицце"""
    addon = AddonSerializer(read_only=True)
    size = PizzaSizesSerializer(read_only=True)
    
    class Meta:
        model = AddonParams
        fields = ('id', 'addon', 'size', 'price')

class PizzaSauceSerializer(serializers.ModelSerializer):
    """Сериализатор для соусов к пицце"""
    class Meta:
        model = PizzaSauce
        fields = ('id', 'name', 'slug', 'is_active')

class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для продуктов"""
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'description', 'image', 'category', 
            'is_active', 'is_new', 'is_hit', 'created_at', 'updated_at',
            'variants'
        )
