from django.test import TestCase

from app_home.models import Discount


class WeeklyPizzaDiscountTest(TestCase):
    def test_weekly_pizza_discount_from_database(self):
        # Создаем скидку в базе данных
        discount = Discount.objects.create(
            name='Пицца недели',
            slug='picca-nedeli',
            percent=25
        )

        # Получаем скидку из базы данных
        try:
            weekly_pizza_discount = Discount.objects.get(slug='picca-nedeli').percent
        except Discount.DoesNotExist:
            weekly_pizza_discount = 20
        
        # Проверяем, что получено правильное значение
        self.assertEqual(weekly_pizza_discount, 25)

    def test_weekly_pizza_discount_default_value(self):
        # Убеждаемся, что скидки нет в базе данных
        Discount.objects.filter(slug='picca-nedeli').delete()

        # Пытаемся получить скидку из базы данных
        try:
            weekly_pizza_discount = Discount.objects.get(slug='picca-nedeli').percent
        except Discount.DoesNotExist:
            weekly_pizza_discount = 20
        
        # Проверяем, что получено значение по умолчанию
        self.assertEqual(weekly_pizza_discount, 20)