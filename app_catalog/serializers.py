from rest_framework import serializers
from .models import Category, Product, ProductVariant, PizzaSizes, PizzaBoard, PizzaAddon, BoardParams, AddonParams, PizzaSauce

class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий товаров"""
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image', 'is_active')
    
    def get_image(self, obj):
        if obj.image and obj.image.url:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""  # Возвращаем пустую строку вместо null"}]}}}

class PizzaSizesSerializer(serializers.ModelSerializer):
    """Сериализатор для размеров пиццы"""
    class Meta:
        model = PizzaSizes
        fields = ('id', 'name')

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
        fields = ('id', 'product', 'size', 'value', 'unit', 'price')

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
            'is_active', 'created_at', 'variants'
        )
