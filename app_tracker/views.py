from django.shortcuts import get_object_or_404, redirect
from .models import TrackedURL
from urllib.parse import urlencode, urlparse

def redirect_to_original_url(request):
    tracking_code = request.GET.get('code')
    if not tracking_code:
        # Handle cases where no 'code' is provided, e.g., redirect to homepage
        return redirect('/')

    tracked_url, created = TrackedURL.objects.get_or_create(
        tracking_code=tracking_code,
        defaults={'original_url': '/'}  # Set a default original_url if created
    )
    tracked_url.clicks += 1
    tracked_url.save()

    # Get all GET parameters, excluding 'code' if it's there
    query_params = request.GET.copy()
    if 'code' in query_params:
        del query_params['code']

    # Construct the final URL with original query parameters
    final_url = tracked_url.original_url
    if query_params:
        parsed_url = urlparse(tracked_url.original_url)
        if parsed_url.query:
            final_url += '&' + urlencode(query_params)
        else:
            final_url += '?' + urlencode(query_params)

    return redirect(final_url)
