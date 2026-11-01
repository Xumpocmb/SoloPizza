from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from app_api.filters import catalog_products
from app_catalog.models import (
    AddonParams,
    BoardParams,
    Category,
    ComboDrinks,
    PizzaSauce,
    PizzaSizes,
    Product,
)
from app_home.models import CafeBranch

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


def _variant_payload(variant, product, size_32):
    """Опции варианта — те же правила, что у web-эндпоинта catalog/variant-data/."""
    boards = []
    if product.has_border and variant.size:
        board_size = size_32 if (product.is_combo and size_32 is not None) else variant.size
        boards = [
            {"id": bp.pk, "name": f"{bp.board.name} ({bp.size.name})", "price": bp.price}
            for bp in BoardParams.objects.filter(size=board_size, board__is_active=True).select_related("board", "size")
        ]

    addons = []
    if product.has_addons and variant.size:
        addons = [
            {"id": ap.pk, "name": ap.get_display_name(), "price": ap.price}
            for ap in AddonParams.objects.filter(size=variant.size, addon__is_active=True).select_related("addon", "size")
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
        size_32 = PizzaSizes.objects.filter(name="32").first() if obj.is_combo else None
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
