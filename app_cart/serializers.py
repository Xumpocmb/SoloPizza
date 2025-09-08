from rest_framework import serializers
from .models import CartItem
from app_catalog.serializers import ProductVariantSerializer

class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элементов корзины"""
    variant_details = ProductVariantSerializer(source='variant', read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ('id', 'product', 'variant', 'variant_details', 'quantity', 'boards', 'addons', 'sauce', 'drink', 'total_price')
        read_only_fields = ('id', 'total_price')
    
    def get_total_price(self, obj):
        return obj.get_total_price()

class CartSummarySerializer(serializers.Serializer):
    """Сериализатор для сводной информации о корзине"""
    items_count = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    items = CartItemSerializer(many=True)