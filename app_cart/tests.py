from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app_catalog.models import Category, PizzaAddon, PizzaBoard, PizzaSizes, Product, ProductVariant, BoardParams, PizzaSauce, AddonParams

User = get_user_model()


def create_test_data():
    # Создаем пользователя
    user = User.objects.create_user(username="testuser", password="password")

    # Категории
    category_pizza = Category.objects.create(name="Пицца", slug="pizza")
    category_drink = Category.objects.create(name="Напитки", slug="drinks")

    # Размеры пиццы
    size_large = PizzaSizes.objects.create(name="Большая")
    size_medium = PizzaSizes.objects.create(name="Средняя")

    # Продукты
    product_pizza = Product.objects.create(name="Пепперони", slug="pepperoni", description="Острая пицца", category=category_pizza)

    product_drink = Product.objects.create(name="Кола", slug="cola", description="Газировка", category=category_drink)

    # Варианты товара
    variant_pizza = ProductVariant.objects.create(product=product_pizza, size=size_large, price=500)

    variant_drink = ProductVariant.objects.create(product=product_drink, value="0.5", unit="l", price=80)

    # Борты
    board_cheese = PizzaBoard.objects.create(name="Сырный борт", slug="cheese")
    board_regular = PizzaBoard.objects.create(name="Обычный", slug="regular")

    BoardParams.objects.create(board=board_cheese, size=size_large, price=50)
    BoardParams.objects.create(board=board_regular, size=size_large, price=0)

    # Соусы
    sauce_tomato = PizzaSauce.objects.create(name="Томатный", slug="tomato")

    # Добавки
    addon_olives = PizzaAddon.objects.create(name="Маслины", slug="olives")
    AddonParams.objects.create(addon=addon_olives, size=size_large, price=30)

    return {
        "user": user,
        "product_pizza": product_pizza,
        "product_drink": product_drink,
        "variant_pizza": variant_pizza,
        "variant_drink": variant_drink,
        "sauce_tomato": sauce_tomato,
        "board_cheese": board_cheese,
        "board_regular": board_regular,
        "addon_olives": addon_olives,
    }


class AddToCartViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.data = create_test_data()
        self.user = self.data["user"]
        self.client.login(username="testuser", password="password")

    def test_add_pizza_with_options_to_cart(self):
        data = self.data
        pizza = data["product_pizza"]
        variant = data["variant_pizza"]
        sauce = data["sauce_tomato"]
        board_cheese = data["board_cheese"]
        board_regular = data["board_regular"]
        addon_olives = data["addon_olives"]

        board_params_cheese = BoardParams.objects.get(board=board_cheese, size=variant.size)
        board_params_regular = BoardParams.objects.get(board=board_regular, size=variant.size)

        response = self.client.post(
            reverse("app_cart:add_to_cart", args=[pizza.slug]),
            {
                "variant_id": variant.id,
                "quantity": 2,
                "board1_id": board_params_cheese.id,
                "board2_id": board_params_regular.id,
                "sauce_id": sauce.id,
                "addon_ids": [addon_olives.id],
            },
        )

        self.assertEqual(response.status_code, 302)  # Редирект после POST

        cart_item = self.user.cart_items.get(item=pizza)

        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.board1, board_params_cheese)
        self.assertEqual(cart_item.board2, board_params_regular)
        self.assertEqual(cart_item.sauce, sauce)
        self.assertIn(addon_olives, cart_item.addons.all())

    def test_cannot_add_same_board_twice(self):
        data = self.data
        pizza = data["product_pizza"]
        variant = data["variant_pizza"]
        board_cheese = data["board_cheese"]

        board_params_cheese = BoardParams.objects.get(board=board_cheese, size=variant.size)

        response = self.client.post(
            reverse("app_cart:add_to_cart", args=[pizza.slug]),
            {
                "variant_id": variant.id,
                "board1_id": board_params_cheese.id,
                "board2_id": board_params_cheese.id,
            },
            follow=True,
        )

        messages = list(response.context["messages"])
        self.assertTrue(any("одинаковые борты" in m.message for m in messages))

    def test_adding_same_item_increases_quantity(self):
        data = self.data
        pizza = data["product_pizza"]
        variant = data["variant_pizza"]

        # Первый раз
        self.client.post(reverse("app_cart:add_to_cart", args=[pizza.slug]), {"variant_id": variant.id, "quantity": 1})

        # Второй раз
        self.client.post(reverse("app_cart:add_to_cart", args=[pizza.slug]), {"variant_id": variant.id, "quantity": 2})

        cart_item = self.user.cart_items.get(item=pizza)
        self.assertEqual(cart_item.quantity, 3)

    def test_add_drink_without_options(self):
        data = self.data
        drink = data["product_drink"]
        variant = data["variant_drink"]

        response = self.client.post(reverse("app_cart:add_to_cart", args=[drink.slug]), {"variant_id": variant.id, "quantity": 2})

        self.assertEqual(response.status_code, 302)
        cart_item = self.user.cart_items.get(item=drink)
        self.assertEqual(cart_item.quantity, 2)
        self.assertIsNone(cart_item.board1)
        self.assertIsNone(cart_item.board2)
        self.assertIsNone(cart_item.sauce)
        self.assertEqual(cart_item.addons.count(), 0)
