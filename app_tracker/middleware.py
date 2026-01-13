from .models import TrackedUTM


class UTMTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        utm_params = {}
        for param in ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]:
            if param in request.GET:
                utm_params[param] = request.GET[param]

        if utm_params:
            ip_address = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT")

            # Проверяем, существует ли уже запись с такими параметрами UTM
            tracked_utm, created = TrackedUTM.objects.get_or_create(
                utm_source=utm_params.get("utm_source"),
                utm_medium=utm_params.get("utm_medium"),
                utm_campaign=utm_params.get("utm_campaign"),
                utm_term=utm_params.get("utm_term"),
                utm_content=utm_params.get("utm_content"),
                defaults={"counter": 1},
            )

            # Если запись уже существовала, увеличиваем счётчик
            if not created:
                tracked_utm.counter += 1
                tracked_utm.save()
        response = self.get_response(request)
        return response
