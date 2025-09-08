from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from app_catalog.models import Category, Product, ProductVariant, PizzaSizes

class CatalogAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Создаем категории
        self.category1 = Category.objects.create(
            name='Пицца',
            slug='pizza',
            is_active=True
        )
        
        self.category2 = Category.objects.create(
            name='Напитки',
            slug='drinks',
            is_active=True
        )
        
        self.inactive_category = Category.objects.create(
            name='Неактивная категория',
            slug='inactive',
            is_active=False
        )
        
        # Создаем размеры
        self.size1 = PizzaSizes.objects.create(name='25 см')
        self.size2 = PizzaSizes.objects.create(name='30 см')
        
        # Создаем продукты
        self.product1 = Product.objects.create(
            category=self.category1,
            name='Пепперони',
            slug='pepperoni',
            description='Острая пицца с пепперони',
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            category=self.category1,
            name='Маргарита',
            slug='margarita',
            description='Классическая пицца',
            is_active=True
        )
        
        self.product3 = Product.objects.create(
            category=self.category2,
            name='Кола',
            slug='cola',
            description='Газированный напиток',
            is_active=True
        )
        
        self.inactive_product = Product.objects.create(
            category=self.category1,
            name='Неактивный продукт',
            slug='inactive-product',
            is_active=False
        )
        
        # Создаем варианты продуктов
        self.variant1 = ProductVariant.objects.create(
            product=self.product1,
            size=self.size1,
            price=450
        )
        
        self.variant2 = ProductVariant.objects.create(
            product=self.product1,
            size=self.size2,
            price=650
        )
        
        self.variant3 = ProductVariant.objects.create(
            product=self.product2,
            size=self.size1,
            price=400
        )
        
        self.variant4 = ProductVariant.objects.create(
            product=self.product3,
            value='0.5',
            unit='л',
            price=80
        )
    
    def test_category_list(self):
        """Тест получения списка категорий"""
        url = reverse('category_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Только активные категории
        
        # Проверяем, что неактивная категория не включена
        category_slugs = [category['slug'] for category in response.data]
        self.assertIn('pizza', category_slugs)
        self.assertIn('drinks', category_slugs)
        self.assertNotIn('inactive', category_slugs)
    
    def test_category_detail(self):
        """Тест получения детальной информации о категории"""
        url = reverse('category_detail', kwargs={'pk': self.category1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Пицца')
        self.assertEqual(response.data['slug'], 'pizza')
    
    def test_inactive_category_detail(self):
        """Тест получения детальной информации о неактивной категории"""
        url = reverse('category_detail', kwargs={'pk': self.inactive_category.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_product_list(self):
        """Тест получения списка продуктов"""
        url = reverse('product_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Только активные продукты
        
        # Проверяем, что неактивный продукт не включен
        product_slugs = [product['slug'] for product in response.data]
        self.assertIn('pepperoni', product_slugs)
        self.assertIn('margarita', product_slugs)
        self.assertIn('cola', product_slugs)
        self.assertNotIn('inactive-product', product_slugs)
    
    def test_product_list_filter_by_category(self):
        """Тест фильтрации продуктов по категории"""
        url = f"{reverse('product_list')}?category={self.category1.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Только продукты из категории 'Пицца'
        
        product_names = [product['name'] for product in response.data]
        self.assertIn('Пепперони', product_names)
        self.assertIn('Маргарита', product_names)
        self.assertNotIn('Кола', product_names)
    
    def test_product_list_search(self):
        """Тест поиска продуктов"""
        url = f"{reverse('product_list')}?search=пепперони"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Пепперони')
    
    def test_product_detail(self):
        """Тест получения детальной информации о продукте"""
        url = reverse('product_detail', kwargs={'pk': self.product1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Пепперони')
        self.assertEqual(response.data['slug'], 'pepperoni')
        
        # Проверяем, что варианты продукта включены в ответ
        self.assertEqual(len(response.data['variants']), 2)
        variant_prices = [variant['price'] for variant in response.data['variants']]
        self.assertIn(450, variant_prices)
        self.assertIn(650, variant_prices)
    
    def test_inactive_product_detail(self):
        """Тест получения детальной информации о неактивном продукте"""
        url = reverse('product_detail', kwargs={'pk': self.inactive_product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_variant_list(self):
        """Тест получения списка вариантов продуктов"""
        url = reverse('variant_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # Все варианты продуктов
    
    def test_variant_list_filter_by_product(self):
        """Тест фильтрации вариантов по продукту"""
        url = f"{reverse('variant_list')}?product={self.product1.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Только варианты продукта 'Пепперони'
        
        variant_prices = [variant['price'] for variant in response.data]
        self.assertIn(450, variant_prices)
        self.assertIn(650, variant_prices)
    
    def test_variant_list_filter_by_size(self):
        """Тест фильтрации вариантов по размеру"""
        url = f"{reverse('variant_list')}?size={self.size1.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Только варианты с размером '25 см'
        
        product_ids = [variant['product'] for variant in response.data]
        self.assertIn(self.product1.pk, product_ids)
        self.assertIn(self.product2.pk, product_ids)

class LegacyAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
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
    
    def test_get_product_variants(self):
        """Тест получения вариантов продукта через legacy API"""
        url = reverse('get_product_variants', kwargs={'product_id': self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['price'], 450.0)
    
    def test_get_product_variants_invalid_product(self):
        """Тест получения вариантов несуществующего продукта"""
        url = reverse('get_product_variants', kwargs={'product_id': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)