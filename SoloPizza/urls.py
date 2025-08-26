from django.contrib import admin
from django.urls import path
from django.urls import include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from .sitemap import StaticViewSitemap, CategorySitemap, ProductSitemap, VacancySitemap, ReviewSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
    'products': ProductSitemap,
    'vacancies': VacancySitemap,
    'reviews': ReviewSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("accounts/social/", include("allauth.socialaccount.urls")),
    path("", include("app_home.urls")),
    path("user/", include("app_user.urls")),
    path("catalog/", include("app_catalog.urls")),
    path("cart/", include("app_cart.urls")),
    path("order/", include("app_order.urls")),
    path("reviews/", include("app_reviews.urls")),
    path("api/", include("app_catalog.urls_api", namespace="api")),
    
    # SEO URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
