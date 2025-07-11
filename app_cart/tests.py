from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app_catalog.models import Product, ProductVariant, BoardParams, PizzaSauce, AddonParams, Addon

User = get_user_model()


def create_test_data():
    user = User.objects.create_user(username='testuser', password='password')

    # Создаем товары
    product_pizza = Product.objects.create(
        name="Пепперони",
        slug="pepperoni",
        description="Пицца Пепперони",
        category=Product.CATEGORY_PIZZA,
        is_weekly_special=False
    )

    product_drink = Product.objects.create(
        name="Кола",
        slug="cola",
        description="Газировка",
        category=Product.CATEGORY_DRINK
    )

    # Размеры
    variant_pizza = ProductVariant.objects.create(
        product=product_pizza,
        size_name="Большая",
        price=500
    )

    variant_drink = ProductVariant.objects.create(
        product=product_drink,
        value=0.5,
        unit=ProductVariant.UNIT_LITER,
        price=80
    )

    # Борты
    board1 = BoardParams.objects.create(
        board_name="Обычный борт",
        price=0
    )
    board2 = BoardParams.objects.create(
        board_name="Сырный борт",
        price=50
    )

    # Соус
    sauce = PizzaSauce.objects.create(name="Томатный")

    # Добавки
    addon_type = Addon.objects.create(name="Маслины")
    addon = AddonParams.objects.create(addon=addon_type, price=30, size=variant_pizza.size)

    return {
        'user': user,
        'pizza': product_pizza,
        'drink': product_drink,
        'pizza_variant': variant_pizza,
        'drink_variant': variant_drink,
        'board1': board1,
        'board2': board2,
        'sauce': sauce,
        'addon': addon
    }
    


class AddToCartTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.data = create_test_data()
        self.user = self.data['user']
        self.client.login(username='testuser', password='password')

    def test_add_drink_to_cart(self):
        drink = self.data['drink']
        variant = self.data['drink_variant']

        response = self.client.post(reverse('app_cart:add_to_cart', args=[drink.slug]), {
            'variant_id': variant.id,
            'quantity': 2
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user.cart_items.filter(item=drink, item_variant=variant).exists())

        cart_item = self.user.cart_items.get(item=drink)
        self.assertEqual(cart_item.quantity, 2)
        

    def test_add_pizza_with_options_to_cart(self):
        pizza = self.data['pizza']
        variant = self.data['pizza_variant']
        board1 = self.data['board1']
        board2 = self.data['board2']
        sauce = self.data['sauce']
        addon = self.data['addon']

        response = self.client.post(reverse('app_cart:add_to_cart', args=[pizza.slug]), {
            'variant_id': variant.id,
            'quantity': 1,
            'board1_id': board1.id,
            'board2_id': board2.id,
            'sauce_id': sauce.id,
            'addon_ids': [addon.id]
        })

        self.assertEqual(response.status_code, 302)
        cart_item = self.user.cart_items.get(item=pizza)

        self.assertEqual(cart_item.board1, board1)
        self.assertEqual(cart_item.board2, board2)
        self.assertEqual(cart_item.sauce, sauce)
        self.assertIn(addon, cart_item.addons.all())

    def test_cannot_add_same_boards(self):
        pizza = self.data['pizza']
        variant = self.data['pizza_variant']
        board1 = self.data['board1']

        response = self.client.post(reverse('app_cart:add_to_cart', args=[pizza.slug]), {
            'variant_id': variant.id,
            'board1_id': board1.id,
            'board2_id': board1.id,  # Одинаковые борты
        }, follow=True)

        messages = list(response.context.get('messages', []))
        self.assertTrue(any("одинаковые борты" in m.message for m in messages))
        
    
    def test_adding_same_item_increases_quantity(self):
        pizza = self.data['pizza']
        variant = self.data['pizza_variant']

        # Первый раз
        self.client.post(reverse('app_cart:add_to_cart', args=[pizza.slug]), {
            'variant_id': variant.id,
            'quantity': 1
        })

        # Второй раз
        self.client.post(reverse('app_cart:add_to_cart', args=[pizza.slug]), {
            'variant_id': variant.id,
            'quantity': 2
        })

        cart_item = self.user.cart_items.get(item=pizza)
        self.assertEqual(cart_item.quantity, 3)
