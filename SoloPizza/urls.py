from django.contrib import admin
from django.urls import path
from django.urls import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/social/', include('allauth.socialaccount.urls')),
    path('', include('app_home.urls')),
    path('user/', include('app_user.urls')),
    path('catalog/', include('app_catalog.urls')),
    path('cart/', include('app_cart.urls')),
    path('order/', include('app_order.urls')),
]
