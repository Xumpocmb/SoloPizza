from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from app_catalog.models import Category, Product, ProductVariant, PizzaSizes
from app_cart.models import CartItem
from app_order.models import Order, OrderItem

User = get_user_model()

class OrderAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Создаем пользователей
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword123'
        )
        
        # Устанавливаем адрес пользователя
        self.user.address = 'Москва, Тверская ул., д. 1, кв. 10'
        self.user.save()
        
        # Создаем категории
        self.category = Category.objects.create(
            name='Пицца',
            slug='pizza',
            is_active=True
        )
        
        # Создаем размеры
        self.size = PizzaSizes.objects.create(name='25 см')
        
        # Создаем продукты
        self.product = Product.objects.create(
            category=self.category,
            name='Пепперони',
            slug='pepperoni',
            description='Острая пицца с пепперони',
            is_active=True
        )
        
        # Создаем варианты продуктов
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size=self.size,
            price=450
        )
        
        # Создаем элементы корзины
        self.cart_item = CartItem.objects.create(
            user=self.user,
            item=self.product,
            item_variant=self.variant,
            quantity=2
        )
        
        # Создаем заказ
        self.order = Order.objects.create(
            user=self.user,
            delivery_type='delivery',
            address=self.user.address,
            phone_number='+79001234567',
            payment='cash',
            status='new'
        )
        
        # Добавляем товар в заказ
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_variant=self.variant,
            quantity=1,
            price=self.variant.price
        )
        
        # Создаем заказ для другого пользователя
        self.other_order = Order.objects.create(
            user=self.other_user,
            delivery_type='pickup',
            phone='+79009876543',
            payment_method='card',
            status='new'
        )
    
    def test_order_list_unauthorized(self):
        """Тест доступа к списку заказов без авторизации"""
        url = reverse('order_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_order_list_get(self):
        """Тест получения списка заказов пользователя"""
        url = reverse('order_list')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # У пользователя должен быть 1 заказ
    
    def test_order_detail_get(self):
        """Тест получения деталей заказа"""
        url = reverse('order_detail', kwargs={'pk': self.order.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order.id)
        self.assertEqual(len(response.data['items']), 1)
    
    def test_order_detail_other_user(self):
        """Тест доступа к заказу другого пользователя"""
        url = reverse('order_detail', kwargs={'pk': self.other_order.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_order_create_empty_cart(self):
        """Тест создания заказа с пустой корзиной"""
        # Очищаем корзину
        CartItem.objects.filter(user=self.user).delete()
        
        url = reverse('order_create')
        self.client.force_authenticate(user=self.user)
        data = {
            'delivery_type': 'delivery',
            'address': self.user.address,
            'customer_phone': '+79001234567',
            'payment': 'cash',
            'comment': 'Тестовый заказ'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_order_create_success(self):
        """Тест успешного создания заказа"""
        url = reverse('order_create')
        self.client.force_authenticate(user=self.user)
        data = {
            'delivery_type': 'delivery',
            'address': self.user.address,
            'customer_phone': '+79001234567',
            'payment': 'cash',
            'comment': 'Тестовый заказ'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем, что заказ создан
        self.assertEqual(Order.objects.filter(user=self.user).count(), 2)
        
        # Проверяем, что корзина очищена
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)
    
    def test_order_status_get(self):
        """Тест получения статуса заказа"""
        url = reverse('order_status', kwargs={'pk': self.order.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'new')
    
    def test_order_status_other_user(self):
        """Тест доступа к статусу заказа другого пользователя"""
        url = reverse('order_status', kwargs={'pk': self.other_order.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
