from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from app_catalog.models import Category, Product, ProductVariant, PizzaSizes
from app_cart.models import CartItem

User = get_user_model()

class CartAPITestCase(TestCase):
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
        
        # Создаем элемент корзины для другого пользователя
        self.other_cart_item = CartItem.objects.create(
            user=self.other_user,
            item=self.product,
            item_variant=self.variant,
            quantity=1
        )
    
    def test_cart_item_list_unauthorized(self):
        """Тест доступа к списку элементов корзины без авторизации"""
        url = reverse('cart_item_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cart_item_list_get(self):
        """Тест получения списка элементов корзины"""
        url = reverse('cart_item_list')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # У пользователя должен быть 1 элемент в корзине
    
    def test_cart_item_create(self):
        """Тест создания нового элемента корзины"""
        url = reverse('cart_item_list')
        self.client.force_authenticate(user=self.user)
        data = {
            'product': self.product.id,
            'variant': self.variant.id,
            'quantity': 3
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 2)
    
    def test_cart_item_detail_get(self):
        """Тест получения деталей элемента корзины"""
        url = reverse('cart_item_detail', kwargs={'pk': self.cart_item.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 2)
    
    def test_cart_item_detail_update(self):
        """Тест обновления элемента корзины"""
        url = reverse('cart_item_detail', kwargs={'pk': self.cart_item.pk})
        self.client.force_authenticate(user=self.user)
        data = {'quantity': 5}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что данные обновились
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 5)
    
    def test_cart_item_detail_delete(self):
        """Тест удаления элемента корзины"""
        url = reverse('cart_item_detail', kwargs={'pk': self.cart_item.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)
    
    def test_cart_item_other_user_access(self):
        """Тест доступа к элементу корзины другого пользователя"""
        url = reverse('cart_item_detail', kwargs={'pk': self.other_cart_item.pk})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_cart_summary_unauthorized(self):
        """Тест доступа к сводке корзины без авторизации"""
        url = reverse('cart_summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cart_summary_get(self):
        """Тест получения сводки корзины"""
        url = reverse('cart_summary')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items_count'], 1)
        self.assertEqual(float(response.data['total_price']), 900.0)  # 2 * 450 = 900
    
    def test_cart_summary_empty(self):
        """Тест получения сводки пустой корзины"""
        # Удаляем все элементы корзины пользователя
        CartItem.objects.filter(user=self.user).delete()
        
        url = reverse('cart_summary')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items_count'], 0)
        self.assertEqual(float(response.data['total_price']), 0.0)