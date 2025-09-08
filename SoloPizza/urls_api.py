from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Настройка Swagger для документации API
schema_view = get_schema_view(
    openapi.Info(
        title="SoloPizza API",
        default_version='v1',
        description="API для мобильного приложения SoloPizza",
        terms_of_service="https://www.solo-pizza.by/terms/",
        contact=openapi.Contact(email="contact@solo-pizza.by"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Документация API
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API endpoints
    path('auth/', include('app_user.urls_api')),
    path('catalog/', include('app_catalog.urls_api')),
    path('cart/', include('app_cart.urls_api')),
    path('order/', include('app_order.urls_api')),
]