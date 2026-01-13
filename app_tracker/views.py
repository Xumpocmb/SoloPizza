from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import render
from .models import TrackedUTM, TrackedURL
from urllib.parse import urlencode, urlparse


def redirect_to_original_url(request):
    tracking_code = request.GET.get("code")
    if not tracking_code:
        # Handle cases where no 'code' is provided, e.g., redirect to homepage
        return redirect("/")

    tracked_url, created = TrackedURL.objects.get_or_create(tracking_code=tracking_code, defaults={"original_url": "/"})  # Set a default original_url if created
    tracked_url.clicks += 1
    tracked_url.save()

    # Get all GET parameters, excluding 'code' if it's there
    query_params = request.GET.copy()
    if "code" in query_params:
        del query_params["code"]

    # Construct the final URL with original query parameters
    final_url = tracked_url.original_url
    if query_params:
        parsed_url = urlparse(tracked_url.original_url)
        if parsed_url.query:
            final_url += "&" + urlencode(query_params)
        else:
            final_url += "?" + urlencode(query_params)

    return redirect(final_url)


@staff_member_required
def utm_analytics_view(request):
    # Aggregate UTM data - теперь используем поле counter вместо подсчета количества записей
    utm_data = TrackedUTM.objects.values("utm_source", "utm_medium", "utm_campaign", "counter").order_by("-counter")

    # Get TrackedURL data
    tracked_url_data = TrackedURL.objects.all().order_by("-clicks")

    context = {
        "utm_data": utm_data,
        "tracked_url_data": tracked_url_data,
        "title": "UTM Analytics",
        "breadcrumbs": [{"title": "Главная", "url": "/"}, {"title": "UTM Analytics", "url": "#"}],
    }
    return render(request, "app_tracker/utm_analytics.html", context)
