from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CartItem
from .serializers import CartItemSerializer, CartSummarySerializer

class CartItemListView(generics.ListCreateAPIView):
    """API endpoint для просмотра и добавления товаров в корзину"""
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint для просмотра, обновления и удаления товара из корзины"""
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

class CartSummaryView(APIView):
    """API endpoint для получения сводной информации о корзине"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user)
        
        # Если корзина пуста, возвращаем пустую корзину
        if not cart_items.exists():
            return Response({
                'items_count': 0,
                'total_price': 0,
                'items': []
            })
        
        # Рассчитываем общую стоимость и количество товаров
        total_price = sum(item.get_total_price() for item in cart_items)
        items_count = cart_items.count()
        
        # Сериализуем данные корзины
        serializer = CartSummarySerializer({
            'items_count': items_count,
            'total_price': total_price,
            'items': cart_items
        })
        
        return Response(serializer.data)