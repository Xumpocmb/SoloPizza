from rest_framework import serializers
from .models import Order, OrderItem
from app_catalog.serializers import ProductVariantSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элементов заказа"""
    variant_details = ProductVariantSerializer(source='variant', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product_name', 'variant_name', 'variant', 'variant_details', 'quantity', 
                 'price', 'total_price', 'boards', 'addons', 'sauce', 'drink')
        read_only_fields = ('id', 'product_name', 'variant_name', 'price', 'total_price')

class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказов"""
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_display = serializers.CharField(source='get_payment_display', read_only=True)
    delivery_type_display = serializers.CharField(source='get_delivery_type_display', read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'order_number', 'status', 'status_display', 'payment', 'payment_display',
                 'delivery_type', 'delivery_type_display', 'delivery_cost', 'total_price',
                 'customer_name', 'customer_phone', 'address', 'delivery_time',
                 'delivery_by', 'comment', 'created_at', 'updated_at', 'items')
        read_only_fields = ('id', 'order_number', 'status', 'status_display', 'total_price',
                           'created_at', 'updated_at')

class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заказа"""
    
    class Meta:
        model = Order
        fields = (
            'branch', 'customer_name', 'customer_phone',
            'delivery_type', 'address',
            'payment', 'comment'
        )

class OrderStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для статуса заказа"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'order_number', 'status', 'status_display', 'created_at', 'updated_at')
        read_only_fields = ('id', 'order_number', 'status', 'status_display', 'created_at', 'updated_at')