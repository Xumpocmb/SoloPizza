import uuid

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView

from app_api import serializers as api_serializers
from app_api.filters import branch_or_none, catalog_products, visible_categories
from app_home.context_processors import DEFAULT_BRANCH_ID
from app_cart.models import Cart
from app_home.models import Announcement, CafeBranch, Vacancy

BRANCH_ID_PARAM = OpenApiParameter(
    "branch_id",
    OpenApiTypes.INT,
    OpenApiParameter.QUERY,
    required=True,
    description="id выбранного филиала",
)


class PublicViewMixin:
    """Публичные эндпоинты приложения: ни аутентификации, ни прав."""

    permission_classes = [AllowAny]
    authentication_classes = []


class CatalogViewMixin(PublicViewMixin):
    """Каталог требует выбранный филиал — он задаёт видимый набор товаров и категорий."""

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


class BranchListView(PublicViewMixin, ListAPIView):
    serializer_class = api_serializers.BranchSerializer
    queryset = CafeBranch.objects.filter(is_active=True).prefetch_related("branch_phones").order_by("id")


@extend_schema(responses=api_serializers.ContactsSerializer)
class ContactsView(PublicViewMixin, APIView):
    """Контакты для мобильного приложения: филиалы, телефоны, адреса и Instagram."""

    def get(self, request):
        branches = (
            CafeBranch.objects.filter(is_active=True)
            .prefetch_related("branch_phones")
            .order_by("id")
        )
        serializer = api_serializers.ContactsSerializer(
            {"instagram_url": settings.INSTAGRAM_URL, "branches": branches},
            context={"request": request},
        )
        return Response(serializer.data)


class MetaView(PublicViewMixin, APIView):
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


@extend_schema(parameters=[BRANCH_ID_PARAM], responses=api_serializers.ProductListItemSerializer(many=True))
class FeaturedProductListView(CatalogViewMixin, ListAPIView):
    """Товары с флагом display_on_main — аналог блока «на главной» в web-меню."""

    serializer_class = api_serializers.ProductListItemSerializer

    def get_queryset(self):
        return catalog_products(self.get_branch_id()).filter(display_on_main=True).order_by("category__order", "name")


@extend_schema(parameters=[BRANCH_ID_PARAM], responses=api_serializers.ProductDetailSerializer)
class WeeklySpecialProductView(CatalogViewMixin, RetrieveAPIView):
    """Текущая «Пицца недели» — один товар, как на web-странице акций."""

    serializer_class = api_serializers.ProductDetailSerializer

    def get_queryset(self):
        return catalog_products(self.get_branch_id()).filter(is_weekly_special=True).order_by("category__order", "name")

    def get_object(self, queryset=None):
        product = self.get_queryset().first()
        if product is None:
            raise NotFound("Акция «Пицца недели» сейчас не проводится")
        return product


@extend_schema(parameters=[BRANCH_ID_PARAM], responses=api_serializers.ProductDetailSerializer)
class ProductDetailView(CatalogViewMixin, RetrieveAPIView):
    serializer_class = api_serializers.ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return catalog_products(self.get_branch_id())


class AnnouncementListView(PublicViewMixin, ListAPIView):
    """Активные объявления (бывшая «бегущая строка») для главной и приложения."""

    serializer_class = api_serializers.AnnouncementSerializer
    queryset = Announcement.objects.filter(is_active=True).order_by("id")


class VacancyListView(PublicViewMixin, ListAPIView):
    serializer_class = api_serializers.VacancyListItemSerializer
    queryset = Vacancy.objects.filter(is_active=True)


class VacancyDetailView(PublicViewMixin, RetrieveAPIView):
    serializer_class = api_serializers.VacancyDetailSerializer

    def get_queryset(self):
        return Vacancy.objects.filter(is_active=True)


class VacancyApplicationView(PublicViewMixin, APIView):
    """Отклик на вакансию. CSRF не нужен: эндпоинт без сессий, аутентификации и cookies."""

    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        request=api_serializers.VacancyApplicationSerializer,
        responses={201: api_serializers.VacancyApplicationSerializer},
    )
    def post(self, request, vacancy_pk):
        vacancy = get_object_or_404(Vacancy, pk=vacancy_pk, is_active=True)
        serializer = api_serializers.VacancyApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save(vacancy=vacancy)

        if not settings.DEBUG:
            from app_home.tasks import send_vacancy_application_notification

            send_vacancy_application_notification.delay(application.pk)

        return Response(serializer.data, status=201)


# ─── Корзина приложения ─────────────────────────────────────────────────────

CART_TOKEN_HEADER = "X-Cart-Token"
CART_TOKEN_PARAM = OpenApiParameter(
    CART_TOKEN_HEADER,
    OpenApiTypes.UUID,
    OpenApiParameter.HEADER,
    required=True,
    description="token из ответа POST /cart/",
)


class CartViewMixin(PublicViewMixin):
    """Гостевая корзина по токену из заголовка X-Cart-Token (UUID4 — не подобрать перебором)."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cart"

    def get_cart(self):
        try:
            token = uuid.UUID(str(self.request.headers.get(CART_TOKEN_HEADER)))
        except ValueError:
            raise NotFound("Корзина не найдена")
        # shortcut: только гостевые корзины; корзины пользователей появятся вместе со входом по JWT
        cart = Cart.objects.filter(token=token, user__isnull=True).first()
        if cart is None:
            raise NotFound("Корзина не найдена")
        return cart

    def cart_response(self, cart, status=200):
        cart.refresh_from_db()
        return Response(api_serializers.CartSerializer(api_serializers.cart_data(cart, self.request)).data, status=status)


class CartView(CartViewMixin, APIView):
    @extend_schema(parameters=[CART_TOKEN_PARAM], responses=api_serializers.CartSerializer)
    def get(self, request):
        return self.cart_response(self.get_cart())

    @extend_schema(request=api_serializers.CartBranchSerializer, responses={201: api_serializers.CartSerializer})
    def post(self, request):
        """Новая пустая гостевая корзина для филиала; token из ответа клиент шлёт в X-Cart-Token."""
        serializer = api_serializers.CartBranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = Cart.objects.create(branch=serializer.validated_data["branch_id"])
        return self.cart_response(cart, status=201)


class CartItemsView(CartViewMixin, APIView):
    @extend_schema(
        parameters=[CART_TOKEN_PARAM],
        request=api_serializers.CartItemAddSerializer,
        responses=api_serializers.CartSerializer,
    )
    def post(self, request):
        cart = self.get_cart()
        serializer = api_serializers.CartItemAddSerializer(data=request.data, context={"cart": cart})
        serializer.is_valid(raise_exception=True)
        cart.add_item(**serializer.validated_data)
        return self.cart_response(cart)


class CartItemDetailView(CartViewMixin, APIView):
    @extend_schema(
        parameters=[CART_TOKEN_PARAM],
        request=api_serializers.CartQuantitySerializer,
        responses=api_serializers.CartSerializer,
    )
    def patch(self, request, pk):
        cart = self.get_cart()
        item = get_object_or_404(cart.items, pk=pk)
        serializer = api_serializers.CartQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data["quantity"]
        item.save(update_fields=["quantity"])
        cart.touch()
        return self.cart_response(cart)

    @extend_schema(parameters=[CART_TOKEN_PARAM], responses=api_serializers.CartSerializer)
    def delete(self, request, pk):
        cart = self.get_cart()
        get_object_or_404(cart.items, pk=pk).delete()
        cart.touch()
        return self.cart_response(cart)


class CartBranchView(CartViewMixin, APIView):
    @extend_schema(
        parameters=[CART_TOKEN_PARAM],
        request=api_serializers.CartBranchSerializer,
        responses=api_serializers.CartSerializer,
    )
    def put(self, request):
        """Смена филиала очищает корзину, как на сайте."""
        cart = self.get_cart()
        serializer = api_serializers.CartBranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart.change_branch(serializer.validated_data["branch_id"])
        return self.cart_response(cart)
