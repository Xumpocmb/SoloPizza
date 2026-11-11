import uuid

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from app_api import auth as api_auth
from app_api import orders as api_orders
from app_api import serializers as api_serializers
from app_api.filters import branch_or_none, catalog_products, visible_categories
from app_home.context_processors import DEFAULT_BRANCH_ID
from app_cart.models import Cart
from app_order.models import Order
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
    required=False,
    description="token гостевой корзины из ответа POST /cart/; после входа не нужен — корзина по JWT",
)


class CartViewMixin(PublicViewMixin):
    """Корзина пользователя по JWT; без входа — гостевая по X-Cart-Token (UUID4 — не подобрать перебором)."""

    authentication_classes = [JWTAuthentication]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cart"

    def get_cart(self):
        if self.request.user.is_authenticated:
            cart = Cart.objects.filter(user=self.request.user).first()
        else:
            try:
                token = uuid.UUID(str(self.request.headers.get(CART_TOKEN_HEADER)))
            except ValueError:
                raise NotFound("Корзина не найдена")
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

    @extend_schema(
        request=api_serializers.CartBranchSerializer,
        responses={200: api_serializers.CartSerializer, 201: api_serializers.CartSerializer},
    )
    def post(self, request):
        """Новая пустая корзина для филиала. Гостю — token для X-Cart-Token; у пользователя корзина одна (200)."""
        serializer = api_serializers.CartBranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                user=request.user, defaults={"branch": serializer.validated_data["branch_id"]}
            )
            return self.cart_response(cart, status=201 if created else 200)
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


# ─── Вход и профиль ─────────────────────────────────────────────────────────


class ProviderUnavailable(APIException):
    status_code = 503
    default_detail = "Вход через этого провайдера ещё не настроен на сервере"


class SocialLoginView(PublicViewMixin, APIView):
    """Общий вход: проверка токена провайдера → пользователь → перенос гостевой корзины → JWT."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
    provider = None
    serializer_class = None

    def verify(self, data):
        raise NotImplementedError

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            claims = self.verify(serializer.validated_data)
        except api_auth.ProviderNotConfigured:
            raise ProviderUnavailable()
        user = api_auth.resolve_user(
            self.provider,
            claims,
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
        )
        if not user.is_active:
            raise PermissionDenied("Аккаунт заблокирован")
        api_auth.merge_guest_cart(user, request.headers.get(CART_TOKEN_HEADER))
        return Response({**api_auth.issue_tokens(user), "user": api_serializers.me_data(user)})


@extend_schema(
    parameters=[CART_TOKEN_PARAM],
    request=api_serializers.GoogleLoginSerializer,
    responses=api_serializers.AuthResponseSerializer,
)
class GoogleLoginView(SocialLoginView):
    provider = "google"
    serializer_class = api_serializers.GoogleLoginSerializer

    def verify(self, data):
        return api_auth.verify_google(data["id_token"])


@extend_schema(
    parameters=[CART_TOKEN_PARAM],
    request=api_serializers.AppleLoginSerializer,
    responses=api_serializers.AuthResponseSerializer,
)
class AppleLoginView(SocialLoginView):
    provider = "apple"
    serializer_class = api_serializers.AppleLoginSerializer

    def verify(self, data):
        return api_auth.verify_apple(data["identity_token"])


class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=api_serializers.MeSerializer)
    def get(self, request):
        return Response(api_serializers.me_data(request.user))

    @extend_schema(request=api_serializers.MeSerializer, responses=api_serializers.MeSerializer)
    def patch(self, request):
        serializer = api_serializers.MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(api_serializers.me_data(request.user))

    @extend_schema(responses={204: None})
    def delete(self, request):
        """Удаление аккаунта (требование App Store): заказы остаются без привязки к пользователю."""
        # shortcut: токен Sign in with Apple не отзывается (нужен ключ .p8 из Apple Developer);
        # добавить вызов appleid.apple.com/auth/revoke, когда ключ появится — до публикации в App Store
        request.user.delete()
        return Response(status=204)


# ─── Оформление и заказы ────────────────────────────────────────────────────


class UserApiMixin:
    """Эндпоинты только для вошедших: JWT из POST /auth/google/ или /auth/apple/."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "orders"

    def user_cart(self):
        cart = Cart.objects.select_related("branch").filter(user=self.request.user).first()
        if cart is None:
            raise NotFound("Корзина не найдена")
        return cart


class CheckoutOptionsView(UserApiMixin, APIView):
    @extend_schema(responses=api_serializers.CheckoutOptionsSerializer)
    def get(self, request):
        """Способы получения и оплаты; можно ли оформить заказ в филиале корзины прямо сейчас."""
        available, reason = api_orders.availability(self.user_cart(), request.user)
        return Response(api_serializers.CheckoutOptionsSerializer(api_serializers.checkout_options_data(available, reason)).data)


class CheckoutQuoteView(UserApiMixin, APIView):
    @extend_schema(request=api_serializers.QuoteRequestSerializer, responses=api_serializers.QuoteSerializer)
    def post(self, request):
        """Итог корзины для способа получения: скидки самовывоза и «Пиццы недели», доставка."""
        serializer = api_serializers.QuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = self.user_cart()
        available, reason = api_orders.availability(cart, request.user)
        result = api_orders.quote(cart, serializer.validated_data["delivery_type"])
        return Response(api_serializers.QuoteSerializer(api_serializers.quote_data(result, available, reason)).data)


class OrderListView(UserApiMixin, APIView):
    @extend_schema(responses=api_serializers.OrderSerializer(many=True))
    def get(self, request):
        """Последние 50 заказов пользователя — и с сайта, и из приложения."""
        orders = Order.objects.filter(user=request.user).select_related("branch").order_by("-created_at")[:50]
        return Response(api_serializers.OrderSerializer([api_serializers.order_data(order) for order in orders], many=True).data)

    @extend_schema(
        request=api_serializers.OrderCreateSerializer,
        responses={201: api_serializers.OrderSerializer, 200: api_serializers.OrderSerializer},
    )
    def post(self, request):
        """Заказ из корзины пользователя; повтор с тем же client_order_id возвращает тот же заказ (200)."""
        serializer = api_serializers.OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, created = api_orders.create_order(request.user, self.user_cart(), serializer.validated_data)
        return Response(api_serializers.OrderSerializer(api_serializers.order_data(order)).data, status=201 if created else 200)


class OrderDetailView(UserApiMixin, APIView):
    @extend_schema(responses=api_serializers.OrderSerializer)
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        return Response(api_serializers.OrderSerializer(api_serializers.order_data(order)).data)
