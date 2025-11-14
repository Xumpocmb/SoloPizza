from django.shortcuts import get_object_or_404, redirect
from .models import TrackedURL

def redirect_to_original_url(request):
    tracking_code = request.GET.get('code')
    if not tracking_code:
        # Handle case where 'code' parameter is missing, e.g., redirect to home or show an error
        return redirect('/') # Or render an error page
    tracked_url = get_object_or_404(TrackedURL, tracking_code=tracking_code)
    tracked_url.clicks += 1
    tracked_url.save()

    # Get all GET parameters except 'code'
    query_params = request.GET.copy()
    if 'code' in query_params:
        del query_params['code']

    # Construct the final URL with original query parameters
    final_url = tracked_url.original_url
    if query_params:
        from urllib.parse import urlencode, urlparse, urlunparse
        parsed_url = urlparse(tracked_url.original_url)
        if parsed_url.query:
            final_url += '&' + urlencode(query_params)
        else:
            final_url += '?' + urlencode(query_params)

    return redirect(final_url)
