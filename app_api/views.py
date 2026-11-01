from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from app_api import serializers as api_serializers
from app_api.filters import branch_or_none, catalog_products, visible_categories
from app_home.context_processors import DEFAULT_BRANCH_ID
from app_home.models import CafeBranch

BRANCH_ID_PARAM = OpenApiParameter(
    "branch_id",
    OpenApiTypes.INT,
    OpenApiParameter.QUERY,
    required=True,
    description="id выбранного филиала",
)


class CatalogViewMixin:
    """Каталог публичный и только для чтения: ни аутентификации, ни прав."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get_branch_id(self):
        raw = self.request.query_params.get("branch_id")
        if raw is None:
            raise ValidationError({"branch_id": "Обязательный параметр branch_id"})
        if not raw.isdigit():
            raise ValidationError({"branch_id": "branch_id должен быть числом"})
        branch = branch_or_none(raw)
        if branch is None:
            raise NotFound("Филиал не найден или неактивен")
        return branch.pk


class BranchListView(ListAPIView):
    serializer_class = api_serializers.BranchSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    queryset = CafeBranch.objects.filter(is_active=True).prefetch_related("branch_phones").order_by("id")


class MetaView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(
            {
                "currency": settings.CURRENCY,
                "timezone": settings.TIME_ZONE,
                "default_branch_id": DEFAULT_BRANCH_ID,
                "languages": [code for code, _ in settings.LANGUAGES],
            }
        )


@extend_schema(parameters=[BRANCH_ID_PARAM])
class CategoryListView(CatalogViewMixin, ListAPIView):
    serializer_class = api_serializers.CategorySerializer

    def get_queryset(self):
        return visible_categories(self.get_branch_id())


@extend_schema(parameters=[BRANCH_ID_PARAM], responses=api_serializers.CategoryDetailSerializer)
class CategoryDetailView(CatalogViewMixin, RetrieveAPIView):
    serializer_class = api_serializers.CategoryDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return visible_categories(self.get_branch_id())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["branch_id"] = self.get_branch_id()
        return context


@extend_schema(
    parameters=[
        BRANCH_ID_PARAM,
        OpenApiParameter("category", OpenApiTypes.STR, OpenApiParameter.QUERY, description="slug категории"),
    ],
    responses=api_serializers.ProductListItemSerializer(many=True),
)
class ProductListView(CatalogViewMixin, ListAPIView):
    serializer_class = api_serializers.ProductListItemSerializer

    def get_queryset(self):
        products = catalog_products(self.get_branch_id())
        category_slug = self.request.query_params.get("category")
        if category_slug:
            products = products.filter(category__slug=category_slug)
        return products.order_by("category__order", "name")


@extend_schema(parameters=[BRANCH_ID_PARAM], responses=api_serializers.ProductDetailSerializer)
class ProductDetailView(CatalogViewMixin, RetrieveAPIView):
    serializer_class = api_serializers.ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return catalog_products(self.get_branch_id())
