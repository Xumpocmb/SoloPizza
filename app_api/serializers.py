from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from app_api.filters import branch_or_none, catalog_products
from app_cart.models import MAX_CART_ITEM_QUANTITY
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
    benefits = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = ["id", "title", "salary", "benefits", "image"]

    @extend_schema_field(IMAGE_SCHEMA)
    def get_image(self, obj):
        return _media_url(self.context.get("request"), obj.image)

    @extend_schema_field(list[str])
    def get_benefits(self, obj):
        # Преимущества хранятся одной строкой через запятую — режем их, как в web-шаблоне.
        return [benefit.strip() for benefit in (obj.benefits or "").split(",") if benefit.strip()]


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

        # Борты и добавки — только своего размера: иначе можно взять дешёвый борт маленькой пиццы
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
