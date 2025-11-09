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
    return redirect(tracked_url.original_url)
