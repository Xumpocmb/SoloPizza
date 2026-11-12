from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from app_api.filters import branch_or_none, catalog_products
from app_api.orders import DELIVERY_TYPES, PAYMENT_METHODS
from app_cart.models import MAX_CART_ITEM_QUANTITY
from app_order.models import Order
from app_catalog.models import (
    AddonParams,
    BoardParams,
    Category,
    ComboDrinks,
    PizzaSauce,
    PizzaSizes,
    Product,
)
from app_home.models import CafeBranch, CafeBranchPhone, Vacancy, VacancyApplication, Announcement

IMAGE_SCHEMA = {"type": "string", "format": "uri", "nullable": True}


def _media_url(request, image):
    if not image:
        return None
    return request.build_absolute_uri(image.url)


class NamedOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class PricedOptionSerializer(NamedOptionSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class VariantSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    size = serializers.CharField(allow_null=True)
    value = serializers.CharField(allow_null=True)
    unit = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    boards = PricedOptionSerializer(many=True)
    addons = PricedOptionSerializer(many=True)


class BranchSerializer(serializers.ModelSerializer):
    phones = serializers.SerializerMethodField()

    class Meta:
        model = CafeBranch
        fields = ["id", "name", "address", "phones"]

    @extend_schema_field(list[str])
    def get_phones(self, obj):
        return [phone.dial for phone in obj.branch_phones.all()]


class ContactPhoneSerializer(serializers.ModelSerializer):
    """Телефон филиала: номер для показа и номер для ссылки tel:."""

    number = serializers.CharField(source="phone")
    dial = serializers.CharField(read_only=True)

    class Meta:
        model = CafeBranchPhone
        fields = ["number", "dial"]


class ContactBranchSerializer(serializers.ModelSerializer):
    phones = serializers.SerializerMethodField()

    class Meta:
        model = CafeBranch
        fields = ["id", "name", "address", "phones"]

    @extend_schema_field(ContactPhoneSerializer(many=True))
    def get_phones(self, obj):
        # Пустые телефоны в админке возможны — в контакты они не попадают.
        phones = [phone for phone in obj.branch_phones.all() if phone.phone]
        return ContactPhoneSerializer(phones, many=True).data


class ContactsSerializer(serializers.Serializer):
    instagram_url = serializers.URLField()
    branches = ContactBranchSerializer(many=True)


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "slug", "name", "image", "product_count"]

    @extend_schema_field(IMAGE_SCHEMA)
    def get_image(self, obj):
        return _media_url(self.context.get("request"), obj.image)


class ProductListItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, allow_null=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "image",
            "min_price",
            "is_weekly_special",
            "is_spicy",
            "is_sweet",
            "is_combo",
        ]

    @extend_schema_field(IMAGE_SCHEMA)
    def get_image(self, obj):
        return _media_url(self.context.get("request"), obj.image)


class CategoryDetailSerializer(CategorySerializer):
    products = serializers.SerializerMethodField()

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ["products"]

    @extend_schema_field(ProductListItemSerializer(many=True))
    def get_products(self, obj):
        products = catalog_products(self.context["branch_id"], category=obj)
        return ProductListItemSerializer(products, many=True, context=self.context).data


def combo_board_size(product):
    """У комбо борты всегда от пиццы 32 см, какой бы ни был вариант набора."""
    return PizzaSizes.objects.filter(name="32").first() if product.is_combo else None


def variant_boards(product, variant, size_32):
    """Борты, доступные варианту. Те же правила у карточки товара и у корзины приложения."""
    if not (product.has_border and variant.size):
        return BoardParams.objects.none()
    board_size = size_32 if (product.is_combo and size_32 is not None) else variant.size
    return BoardParams.objects.filter(size=board_size, board__is_active=True).select_related("board", "size")


def variant_addons(product, variant):
    """Добавки, доступные варианту: только своего размера."""
    if not (product.has_addons and variant.size):
        return AddonParams.objects.none()
    return AddonParams.objects.filter(size=variant.size, addon__is_active=True).select_related("addon", "size")


def board_name(board_params):
    return f"{board_params.board.name} ({board_params.size.name})"


def _variant_payload(variant, product, size_32):
    """Опции варианта — те же правила, что у web-эндпоинта catalog/variant-data/."""
    boards = [
        {"id": bp.pk, "name": board_name(bp), "price": bp.price}
        for bp in variant_boards(product, variant, size_32)
    ]
    addons = [
        {"id": ap.pk, "name": ap.get_display_name(), "price": ap.price}
        for ap in variant_addons(product, variant)
    ]

    return {
        "id": variant.pk,
        "size": variant.size.name if variant.size else None,
        "value": variant.value,
        "unit": variant.get_unit_display(),
        "price": variant.price,
        "boards": boards,
        "addons": addons,
    }


class ProductDetailSerializer(ProductListItemSerializer):
    variants = serializers.SerializerMethodField()
    sauces = serializers.SerializerMethodField()
    drinks = serializers.SerializerMethodField()

    class Meta(ProductListItemSerializer.Meta):
        fields = ProductListItemSerializer.Meta.fields + [
            "has_base_sauce",
            "has_border",
            "has_addons",
            "has_drink",
            "variants",
            "sauces",
            "drinks",
        ]

    @extend_schema_field(VariantSerializer(many=True))
    def get_variants(self, obj):
        size_32 = combo_board_size(obj)
        payloads = [_variant_payload(variant, obj, size_32) for variant in obj.variants.all()]
        return VariantSerializer(payloads, many=True).data

    @extend_schema_field(NamedOptionSerializer(many=True))
    def get_sauces(self, obj):
        if not obj.has_base_sauce:
            return []
        return NamedOptionSerializer(PizzaSauce.objects.filter(is_active=True), many=True).data

    @extend_schema_field(NamedOptionSerializer(many=True))
    def get_drinks(self, obj):
        if not obj.has_drink:
            return []
        return NamedOptionSerializer(ComboDrinks.objects.filter(is_active=True), many=True).data


class VacancyListItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = ["id", "title", "image"]

    @extend_schema_field(IMAGE_SCHEMA)
    def get_image(self, obj):
        return _media_url(self.context.get("request"), obj.image)


class VacancyDetailSerializer(VacancyListItemSerializer):
    class Meta(VacancyListItemSerializer.Meta):
        fields = VacancyListItemSerializer.Meta.fields + ["description"]


class AnnouncementSerializer(serializers.ModelSerializer):
    """Объявление: только id и текст (эндпоинт отдаёт лишь активные)."""

    class Meta:
        model = Announcement
        fields = ["id", "text"]


class VacancyApplicationSerializer(serializers.ModelSerializer):
    """Отклик на вакансию — те же поля и правила, что у web-формы VacancyApplicationForm."""

    # Модельный RegexValidator и max_length=17 требуют уже очищённые цифры, а
    # пользователь вводит «+375 (29) 123-45-67», поэтому валидатор поля свой.
    phone = serializers.CharField(max_length=32)

    class Meta:
        model = VacancyApplication
        fields = ["name", "age", "phone", "experience_years", "work_experience"]

    def validate_phone(self, value):
        digits = "".join(char for char in value if char.isdigit())
        if not 12 <= len(digits) <= 17:
            raise serializers.ValidationError("Номер телефона должен содержать от 12 до 17 цифр.")
        return digits


# ─── Корзина приложения ─────────────────────────────────────────────────────


class CartItemAddSerializer(serializers.Serializer):
    """Позиция в корзину: только id. Цены сервер берёт из каталога, а не от клиента."""

    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField()
    board1_id = serializers.IntegerField(required=False, allow_null=True)
    board2_id = serializers.IntegerField(required=False, allow_null=True)
    sauce_id = serializers.IntegerField(required=False, allow_null=True)
    addon_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list, max_length=50)
    drink_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_CART_ITEM_QUANTITY, default=1)

    def validate(self, data):
        cart = self.context["cart"]
        product = catalog_products(cart.branch_id).filter(pk=data["product_id"]).first()
        if product is None:
            raise serializers.ValidationError({"product_id": "Товар недоступен в выбранном филиале"})
        variant = product.variants.select_related("size").filter(pk=data["variant_id"]).first()
        if variant is None:
            raise serializers.ValidationError({"variant_id": "У товара нет такого варианта"})

        # Борты и добавки — только своего размера: у каждого размера своя цена
        allowed_boards = variant_boards(product, variant, combo_board_size(product))
        boards = []
        for field in ("board1_id", "board2_id"):
            board_id = data.get(field)
            board = allowed_boards.filter(pk=board_id).first() if board_id is not None else None
            if board_id is not None and board is None:
                raise serializers.ValidationError({field: "Борт недоступен для этого размера"})
            boards.append(board)
        if boards[0] and boards[1] and boards[0].pk == boards[1].pk:
            raise serializers.ValidationError({"board2_id": "Нельзя выбрать одинаковые борты"})

        addon_ids = set(data.get("addon_ids") or [])
        addons = list(variant_addons(product, variant).filter(pk__in=addon_ids))
        if len(addons) != len(addon_ids):
            raise serializers.ValidationError({"addon_ids": "Добавка недоступна для этого размера"})

        sauce = None
        if data.get("sauce_id") is not None:
            sauce = PizzaSauce.objects.filter(pk=data["sauce_id"], is_active=True).first() if product.has_base_sauce else None
            if sauce is None:
                raise serializers.ValidationError({"sauce_id": "Соус недоступен для этого товара"})
        elif product.has_base_sauce and PizzaSauce.objects.filter(is_active=True).exists():
            raise serializers.ValidationError({"sauce_id": "Выберите соус-основу"})

        drink = None
        if product.has_drink:
            drink = ComboDrinks.objects.filter(pk=data.get("drink_id"), is_active=True).first() if data.get("drink_id") is not None else None
            if drink is None:
                raise serializers.ValidationError({"drink_id": "Выберите напиток"})
        elif data.get("drink_id") is not None:
            raise serializers.ValidationError({"drink_id": "У товара нет напитка"})

        return {
            "product": product,
            "variant": variant,
            "board1": boards[0],
            "board2": boards[1],
            "sauce": sauce,
            "addons": addons,
            "drink": drink.name if drink else None,  # в CartItem/OrderItem напиток хранится названием
            "quantity": data["quantity"],
        }


class CartQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_CART_ITEM_QUANTITY)


class CartBranchSerializer(serializers.Serializer):
    branch_id = serializers.IntegerField()

    def validate_branch_id(self, value):
        branch = branch_or_none(value)
        if branch is None:
            raise serializers.ValidationError("Филиал не найден или неактивен")
        return branch


class CartVariantSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    size = serializers.CharField(allow_null=True)
    value = serializers.CharField(allow_null=True)
    unit = serializers.CharField()


class CartLineSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    slug = serializers.CharField()
    name = serializers.CharField()
    image = serializers.CharField(allow_null=True)
    variant = CartVariantSerializer()
    board1 = PricedOptionSerializer(allow_null=True)
    board2 = PricedOptionSerializer(allow_null=True)
    sauce = NamedOptionSerializer(allow_null=True)
    addons = PricedOptionSerializer(many=True)
    drink = serializers.CharField(allow_null=True)
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartSerializer(serializers.Serializer):
    """Корзина целиком. Суммы без скидок: самовывоз и «Пицца недели» считаются при оформлении."""

    token = serializers.UUIDField()
    branch_id = serializers.IntegerField()
    items = CartLineSerializer(many=True)
    items_count = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)


def _priced(board_params):
    return {"id": board_params.pk, "name": board_name(board_params), "price": board_params.price} if board_params else None


def cart_data(cart, request):
    """Корзина в форме CartSerializer; цены — из каталога через CartItem.calculate_cart_item_total()."""
    items = cart.items.select_related(
        "item", "item_variant__size", "sauce", "board1__board", "board1__size", "board2__board", "board2__size"
    ).prefetch_related("addons__addon", "addons__size")
    lines, subtotal, count = [], Decimal("0.00"), 0
    for item in items:
        total = item.calculate_cart_item_total()["final_total"]
        variant = item.item_variant
        lines.append({
            "id": item.pk,
            "product_id": item.item_id,
            "slug": item.item.slug,
            "name": item.item.name,
            "image": _media_url(request, item.item.image),
            "variant": {
                "id": variant.pk,
                "size": variant.size.name if variant.size else None,
                "value": variant.value,
                "unit": variant.get_unit_display(),
            },
            "board1": _priced(item.board1),
            "board2": _priced(item.board2),
            "sauce": {"id": item.sauce.pk, "name": item.sauce.name} if item.sauce else None,
            "addons": [{"id": a.pk, "name": a.get_display_name(), "price": a.price} for a in item.addons.all()],
            "drink": item.drink,
            "quantity": item.quantity,
            "unit_price": (total / item.quantity).quantize(Decimal("0.01")),
            "total": total,
        })
        subtotal += total
        count += item.quantity
    return {"token": cart.token, "branch_id": cart.branch_id, "items": lines, "items_count": count, "subtotal": subtotal}


# ─── Вход и профиль ─────────────────────────────────────────────────────────


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class AppleLoginSerializer(serializers.Serializer):
    identity_token = serializers.CharField()
    # Apple отдаёт имя приложению только при первом входе и не кладёт его в токен
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    email = serializers.EmailField(read_only=True)
    phone = serializers.CharField(read_only=True, allow_null=True)

    def update(self, instance, validated_data):
        for field in ("first_name", "last_name"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save(update_fields=["first_name", "last_name"])
        return instance


class AuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = MeSerializer()


def me_data(user):
    """Профиль; телефон — из последнего заказа (у User телефона нет, сайт хранит его в заказе)."""
    phone = user.order_set.exclude(phone_number__isnull=True).exclude(phone_number="").order_by("-created_at")
    return {
        "id": user.pk,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": phone.values_list("phone_number", flat=True).first(),
    }



# ─── Оформление и заказы ────────────────────────────────────────────────────

ORDER_DELIVERY_CHOICES = [(code, label) for code, label in Order.DELIVERY_CHOICES if code in DELIVERY_TYPES]
ORDER_PAYMENT_CHOICES = [(code, label) for code, label in Order.PAYMENT_CHOICES if code in PAYMENT_METHODS]


class ChoiceOptionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class CheckoutOptionsSerializer(serializers.Serializer):
    delivery_types = ChoiceOptionSerializer(many=True)
    payment_methods = ChoiceOptionSerializer(many=True)
    available = serializers.BooleanField()
    reason = serializers.CharField(allow_blank=True)


def checkout_options_data(available, reason):
    return {
        "delivery_types": [{"id": code, "name": str(label)} for code, label in ORDER_DELIVERY_CHOICES],
        "payment_methods": [{"id": code, "name": str(label)} for code, label in ORDER_PAYMENT_CHOICES],
        "available": available,
        "reason": reason,
    }


class QuoteRequestSerializer(serializers.Serializer):
    delivery_type = serializers.ChoiceField(choices=ORDER_DELIVERY_CHOICES)


class QuoteLineSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    quantity = serializers.IntegerField()
    original_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)


class QuoteSerializer(serializers.Serializer):
    lines = QuoteLineSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    available = serializers.BooleanField()
    reason = serializers.CharField(allow_blank=True)


def quote_data(result, available, reason):
    return {
        "lines": [
            {
                "id": item.pk,
                "name": item.item.name,
                "quantity": item.quantity,
                "original_total": calc["original_total"],
                "discount_amount": calc["discount_amount"],
                "total": calc["final_total"],
            }
            for item, calc in result["lines"]
        ],
        **{key: result[key] for key in ("subtotal", "discount_amount", "delivery_cost", "total_price")},
        "available": available,
        "reason": reason,
    }


class OrderCreateSerializer(serializers.Serializer):
    """Только данные клиента: состав — из корзины, суммы, скидки, филиал и статус — от сервера."""

    client_order_id = serializers.UUIDField()
    delivery_type = serializers.ChoiceField(choices=ORDER_DELIVERY_CHOICES)
    payment_method = serializers.ChoiceField(choices=ORDER_PAYMENT_CHOICES)
    customer_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=32)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    consent = serializers.BooleanField()

    def validate_phone(self, value):
        # как у формы отклика: «+375 (29) 123-45-67» → 375291234567 (в Order.phone_number до 20 символов)
        digits = "".join(char for char in value if char.isdigit())
        if not 9 <= len(digits) <= 15:
            raise serializers.ValidationError("Проверьте номер телефона")
        return f"+{digits}"

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError("Нужно согласие на обработку персональных данных")
        return value

    def validate(self, data):
        if data["delivery_type"] == "delivery" and not data.get("address", "").strip():
            raise serializers.ValidationError({"address": "Укажите адрес для доставки"})
        return data


class OrderLineSerializer(serializers.Serializer):
    name = serializers.CharField()
    options = serializers.CharField(allow_blank=True)
    quantity = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    number = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    created_at = serializers.DateTimeField()
    branch_id = serializers.IntegerField(allow_null=True)
    delivery_type = serializers.CharField()
    payment_method = serializers.CharField()
    customer_name = serializers.CharField()
    phone = serializers.CharField(allow_null=True)
    address = serializers.CharField(allow_null=True)
    comment = serializers.CharField(allow_blank=True)
    items = OrderLineSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)


def order_data(order):
    lines = []
    for item in order.items.select_related(
        "product__category", "variant__size", "board1__board", "board2__board", "sauce"
    ).prefetch_related("addons__addon"):
        size = item.variant.size.name if item.variant.size else f"{item.variant.value} {item.variant.get_unit_display()}"
        options = [size]
        options += [f"Борт: {board.board.name}" for board in (item.board1, item.board2) if board]
        options += [item.sauce.name] if item.sauce else []
        options += [addon.addon.name for addon in item.addons.all()]
        options += [item.drink] if item.drink else []
        lines.append({
            "name": item.product.name,
            "options": " · ".join(option for option in options if option),
            "quantity": item.quantity,
            "total": item.calculate_item_total()["final_total"],
        })
    return {
        "id": order.pk,
        "number": order.print_number,
        "status": order.status,
        "status_display": str(order.get_status_display()),
        "created_at": order.created_at,
        "branch_id": order.branch_id,
        "delivery_type": order.delivery_type,
        "payment_method": order.payment_method,
        "customer_name": order.customer_name,
        "phone": order.phone_number,
        "address": order.address,
        "comment": order.comment,
        "items": lines,
        "subtotal": order.subtotal,
        "discount_amount": order.discount_amount,
        "delivery_cost": order.delivery_cost,
        "total_price": order.total_price,
    }
