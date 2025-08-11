from decimal import Decimal
from django.test import TestCase

from app_catalog.models import Category, Product, ProductVariant, PizzaSizes
from app_home.models import Discount, CafeBranch
from app_order.models import Order, OrderItem


class OrderCalculationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаем филиал
        cls.branch = CafeBranch.objects.create(name="Тестовый филиал", address="Тестовый адрес")
        
        # Создаем скидки
        cls.pickup_discount = Discount.objects.create(name="Самовывоз", slug="pickup", percent=10)
        cls.weekly_pizza_discount = Discount.objects.create(name="Пицца недели", slug="weekly-pizza", percent=20)
        cls.partner_discount = Discount.objects.create(name="Партнер", slug="partner", percent=15)
        
        # Создаем размеры пиццы
        cls.size_32 = PizzaSizes.objects.create(name="32")
        cls.size_25 = PizzaSizes.objects.create(name="25")
        
        # Создаем категории
        cls.pizza_category = Category.objects.create(name="Пицца", slug="picca")
        cls.fastfood_category = Category.objects.create(name="Фастфуд", slug="fastfood")
        cls.drink_category = Category.objects.create(name="Напитки", slug="napitki")
        
        # Создаем товары
        # Пицца недели
        cls.weekly_pizza = Product.objects.create(
            category=cls.pizza_category,
            name="Пицца недели",
            slug="weekly-pizza",
            is_weekly_special=True
        )
        
        # Обычная пицца
        cls.regular_pizza = Product.objects.create(
            category=cls.pizza_category,
            name="Обычная пицца",
            slug="regular-pizza"
        )
        
        # Фастфуд
        cls.fastfood = Product.objects.create(
            category=cls.fastfood_category,
            name="Бургер",
            slug="burger"
        )
        
        # Напиток
        cls.drink = Product.objects.create(
            category=cls.drink_category,
            name="Кола",
            slug="cola"
        )
        
        # Создаем варианты товаров
        # Варианты пиццы недели
        cls.weekly_pizza_variant_32 = ProductVariant.objects.create(
            product=cls.weekly_pizza,
            size=cls.size_32,
            price=Decimal("20.00")
        )
        
        cls.weekly_pizza_variant_25 = ProductVariant.objects.create(
            product=cls.weekly_pizza,
            size=cls.size_25,
            price=Decimal("15.00")
        )
        
        # Варианты обычной пиццы
        cls.regular_pizza_variant_32 = ProductVariant.objects.create(
            product=cls.regular_pizza,
            size=cls.size_32,
            price=Decimal("18.00")
        )
        
        cls.regular_pizza_variant_25 = ProductVariant.objects.create(
            product=cls.regular_pizza,
            size=cls.size_25,
            price=Decimal("14.00")
        )
        
        # Вариант фастфуда
        cls.fastfood_variant = ProductVariant.objects.create(
            product=cls.fastfood,
            value="1",
            unit="pcs",
            price=Decimal("10.00")
        )
        
        # Вариант напитка
        cls.drink_variant = ProductVariant.objects.create(
            product=cls.drink,
            value="500",
            unit="ml",
            price=Decimal("5.00")
        )
    
    def create_test_order(self, delivery_type="pickup", is_partner=False):
        """Создает тестовый заказ с одинаковым набором товаров"""
        order = Order.objects.create(
            branch=self.branch,
            customer_name="Тестовый заказчик",
            phone_number="+79001234567",
            delivery_type=delivery_type,
            payment_method="cash",
            is_partner=is_partner
        )
        
        # Добавляем товары в заказ
        # 1. Пицца недели (32)
        OrderItem.objects.create(
            order=order,
            product=self.weekly_pizza,
            variant=self.weekly_pizza_variant_32,
            quantity=1
        )
        
        # 2. Обычная пицца (25)
        OrderItem.objects.create(
            order=order,
            product=self.regular_pizza,
            variant=self.regular_pizza_variant_25,
            quantity=2
        )
        
        # 3. Фастфуд
        OrderItem.objects.create(
            order=order,
            product=self.fastfood,
            variant=self.fastfood_variant,
            quantity=1
        )
        
        # 4. Напиток
        OrderItem.objects.create(
            order=order,
            product=self.drink,
            variant=self.drink_variant,
            quantity=1
        )
        
        # Пересчитываем итоги заказа
        Order.objects.get_order_totals(order.id)
        
        # Обновляем заказ из базы данных
        order.refresh_from_db()
        return order
    
    def test_pickup_order_calculation(self):
        """Тест расчета заказа с самовывозом"""
        order = self.create_test_order(delivery_type="pickup", is_partner=False)
        
        # Проверяем, что скидка на самовывоз применена к пиццам
        self.assertTrue(order.has_pickup_discount)
        
        # Проверяем, что скидка на пиццу недели применена
        weekly_pizza_item = order.items.get(product=self.weekly_pizza)
        calculation = weekly_pizza_item.calculate_item_total()
        self.assertTrue(calculation["is_weekly_pizza"])
        
        # Проверяем итоговые суммы
        # Сумма без скидок: 20 (пицца недели) + 14*2 (обычная пицца) + 10 (фастфуд) + 5 (напиток) = 63
        self.assertEqual(order.subtotal, Decimal("63.00"))
        
        # Проверяем, что скидка применена
        self.assertGreater(order.discount_amount, Decimal("0.00"))
        
        # Стоимость доставки при самовывозе = 0
        self.assertEqual(order.delivery_cost, Decimal("0.00"))
        
        # Проверяем, что итоговая сумма меньше суммы без скидок
        self.assertLess(order.total_price, order.subtotal)
    
    def test_delivery_order_calculation(self):
        """Тест расчета заказа с доставкой"""
        # Создаем заказ с меньшей суммой, чтобы гарантировать платную доставку
        order = Order.objects.create(
            branch=self.branch,
            customer_name="Тестовый заказчик",
            phone_number="+79001234567",
            delivery_type="delivery",
            payment_method="cash",
            is_partner=False
        )
        
        # Добавляем только один товар с низкой стоимостью
        OrderItem.objects.create(
            order=order,
            product=self.drink,
            variant=self.drink_variant,
            quantity=1
        )
        
        # Пересчитываем итоги заказа
        Order.objects.get_order_totals(order.id)
        
        # Обновляем заказ из базы данных
        order.refresh_from_db()
        
        # Проверяем, что скидка на самовывоз не применена
        self.assertFalse(order.has_pickup_discount)
        
        # Проверяем итоговые суммы
        # Сумма без скидок: 5 (напиток)
        self.assertEqual(order.subtotal, Decimal("5.00"))
        
        # При доставке скидка не должна применяться
        self.assertEqual(order.discount_amount, Decimal("0.00"))
        
        # Стоимость доставки должна быть положительной для маленького заказа
        self.assertGreater(order.delivery_cost, Decimal("0.00"))
        
        # Итоговая сумма должна быть больше суммы без скидок (из-за стоимости доставки)
        self.assertGreater(order.total_price, order.subtotal)
    
    def test_partner_order_calculation(self):
        """Тест расчета заказа с партнерской скидкой"""
        order = self.create_test_order(delivery_type="pickup", is_partner=True)
        
        # Проверяем, что скидка партнера применена к пиццам
        pizza_items = order.items.filter(product__category=self.pizza_category)
        for item in pizza_items:
            calculation = item.calculate_item_total()
            self.assertTrue(calculation["is_partner_discount"])
            # Проверяем, что процент скидки соответствует партнерской скидке
            self.assertEqual(calculation["discount_percent"], Decimal(str(self.partner_discount.percent)))
        
        # Проверяем итоговые суммы
        # Сумма без скидок: 20 (пицца недели) + 14*2 (обычная пицца) + 10 (фастфуд) + 5 (напиток) = 63
        self.assertEqual(order.subtotal, Decimal("63.00"))
        
        # Проверяем, что скидка применена
        self.assertGreater(order.discount_amount, Decimal("0.00"))
        
        # Стоимость доставки при самовывозе = 0
        self.assertEqual(order.delivery_cost, Decimal("0.00"))
        
        # Проверяем, что итоговая сумма меньше суммы без скидок
        self.assertLess(order.total_price, order.subtotal)