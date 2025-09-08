from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusSerializer
from app_cart.models import CartItem

class OrderListView(generics.ListAPIView):
    """API endpoint для получения списка заказов пользователя"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class OrderDetailView(generics.RetrieveAPIView):
    """API endpoint для получения детальной информации о заказе"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderCreateView(generics.CreateAPIView):
    """API endpoint для создания нового заказа"""
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Получаем товары из корзины пользователя
        cart_items = CartItem.objects.filter(user=self.request.user)
        
        if not cart_items.exists():
            return Response(
                {"error": "Корзина пуста. Невозможно создать заказ."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем заказ
        order = serializer.save(user=self.request.user)
        
        # Добавляем товары из корзины в заказ
        for cart_item in cart_items:
            order.add_item_from_cart(cart_item)
        
        # Очищаем корзину пользователя
        cart_items.delete()
        
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderStatusView(APIView):
    """API endpoint для получения статуса заказа"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
            serializer = OrderStatusSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response(
                {"error": "Заказ не найден."}, 
                status=status.HTTP_404_NOT_FOUND
            )