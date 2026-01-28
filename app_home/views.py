from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from app_tracker.models import TrackedUTM, TrackedURL
from app_cart.models import CartItem
from app_cart.utils import validate_cart_items_for_branch
from app_catalog.models import Product
from app_home.models import CafeBranch, Vacancy, Marquee
from app_home.forms import VacancyApplicationForm, FeedbackForm
from app_cart.session_cart import SessionCart  # Import SessionCart


def home_page(request):
    active_vacancies = Vacancy.objects.filter(is_active=True)
    active_marquees = Marquee.objects.filter(is_active=True)
    context = {
        "vacancies": active_vacancies,
        "marquees": active_marquees,
    }
    return render(request, "app_home/home.html", context=context)


@require_POST
def select_branch(request):
    """Выбор филиала пользователем."""
    branch_id = request.POST.get("branch_id")
    try:
        if branch_id:
            branch = CafeBranch.objects.get(id=branch_id)
            request.session["selected_branch_id"] = branch_id
            messages.success(request, "Филиал изменен. Корзина очищена!", extra_tags="success")

            # Очищаем корзину при смене филиала
            session_cart = SessionCart(request)
            session_cart.clear()

            return redirect(request.META.get("HTTP_REFERER", "/"))
        else:
            messages.error(request, "Ошибка: филиал не выбран!", extra_tags="error")
    except CafeBranch.DoesNotExist:
        messages.error(request, "Выбранный филиал не найден", extra_tags="error")
        return redirect("/")
    return redirect(request.META.get("HTTP_REFERER"))


def discounts_view(request):
    pizza_weekly = Product.objects.filter(category__slug="picca", is_active=True, is_weekly_special=True).first()
    context = {"pizza_weekly": pizza_weekly}
    return render(request, "app_home/discounts.html", context=context)


def vacancy_list(request):
    """Отображает список всех активных вакансий"""
    vacancies = Vacancy.objects.filter(is_active=True)

    # Добавляем хлебные крошки
    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Вакансии", "url": "#"}]

    context = {"vacancies": vacancies, "title": "Вакансии", "breadcrumbs": breadcrumbs}
    return render(request, "app_home/vacancy_list.html", context=context)


def vacancy_detail(request, vacancy_id):
    """Отображает детальную информацию о конкретной вакансии"""
    vacancy = get_object_or_404(Vacancy, id=vacancy_id, is_active=True)

    # Добавляем хлебные крошки
    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Вакансии", "url": reverse("app_home:vacancy_list")}, {"title": vacancy.title, "url": "#"}]

    context = {"vacancy": vacancy, "title": vacancy.title, "breadcrumbs": breadcrumbs}
    return render(request, "app_home/vacancy_detail.html", context=context)


@csrf_protect
def vacancy_apply(request, vacancy_id):
    """Отображает форму для отклика на вакансию и обрабатывает её отправку"""
    vacancy = get_object_or_404(Vacancy, id=vacancy_id, is_active=True)

    if request.method == "POST":
        form = VacancyApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.vacancy = vacancy
            application.save()

            # Отправляем уведомление о новом отклике на вакансию
            if not settings.DEBUG:
                from app_home.tasks import send_vacancy_application_notification

                send_vacancy_application_notification.delay(application.id)

            messages.success(request, "Ваш отклик успешно отправлен! Мы свяжемся с вами в ближайшее время.", extra_tags="success")
            return redirect(reverse("app_home:vacancy_detail", kwargs={"vacancy_id": vacancy_id}))
        else:
            # Добавляем сообщение об ошибке, если форма не валидна
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.", extra_tags="error")
    else:
        form = VacancyApplicationForm()

    # Добавляем хлебные крошки
    breadcrumbs = [
        {"title": "Главная", "url": "/"},
        {"title": "Вакансии", "url": reverse("app_home:vacancy_list")},
        {"title": vacancy.title, "url": reverse("app_home:vacancy_detail", kwargs={"vacancy_id": vacancy_id})},
        {"title": "Отклик на вакансию", "url": "#"},
    ]

    context = {"vacancy": vacancy, "form": form, "breadcrumbs": breadcrumbs, "title": f"Отклик на вакансию: {vacancy.title}"}
    return render(request, "app_home/vacancy_apply.html", context=context)


def contacts_view(request):
    """Отображает страницу контактов с информацией о выбранном филиале"""

    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Контакты", "url": reverse("app_home:contacts")}]

    context = {"breadcrumbs": breadcrumbs, "title": "Контакты"}

    return render(request, "app_home/contacts.html", context=context)


@csrf_protect
def feedback_view(request):
    """Отображает форму вопросов и предложений и обрабатывает её отправку"""

    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Вопросы и предложения", "url": reverse("app_home:feedback")}]

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save()
            # Отправляем уведомление о новом вопросе/предложении
            # if not settings.DEBUG:
            from app_home.tasks import send_feedback_notification

            send_feedback_notification.delay(feedback.id)
            messages.success(request, "Ваш вопрос/предложение успешно отправлено! Мы свяжемся с вами в ближайшее время.", extra_tags="success")
            return redirect(reverse("app_home:feedback"))
        else:
            # Добавляем сообщение об ошибке, если форма не валидна
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.", extra_tags="error")
    else:
        form = FeedbackForm()

    context = {"breadcrumbs": breadcrumbs, "form": form, "title": "Вопросы и предложения"}

    return render(request, "app_home/feedback.html", context=context)


def info_view(request):
    """Отображает страницу с информацией о компании"""

    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Информация", "url": reverse("app_home:info")}]

    context = {"breadcrumbs": breadcrumbs, "title": "Информация о компании"}

    return render(request, "app_home/info.html", context=context)


def delivery_view(request):
    """Отображает страницу с информацией о доставке"""

    branches = CafeBranch.objects.filter(is_active=True)

    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Доставка", "url": reverse("app_home:delivery")}]

    context = {"breadcrumbs": breadcrumbs, "title": "Доставка", "branches": branches}

    return render(request, "app_home/delivery.html", context=context)


# Удалено: представление utm_analytics_view перемещено в app_tracker/views.py


def partners_view(request):
    """Отображает страницу с информацией о партнерах"""
    from app_home.models import Partner

    partners = Partner.objects.all()

    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Партнеры", "url": reverse("app_home:partners")}]

    context = {"partners": partners, "title": "Наши партнеры", "breadcrumbs": breadcrumbs}

    return render(request, "app_home/partners.html", context=context)


from .models import Certificate


@login_required
def certificate_sell(request):
    """View for selling certificates - generates unique code and allows staff to save it"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "У вас нет прав для доступа к этой странице.")
        return redirect('app_home:home')

    # Generate a new unique certificate code
    import random
    import string
    from datetime import timedelta

    def generate_unique_code():
        """Generate a unique certificate code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Certificate.objects.filter(code=code).exists():
                return code

    certificate_code = generate_unique_code()

    # Calculate expiration date (3 months from now)
    expiration_date = timezone.now() + timedelta(days=90)

    if request.method == 'POST':
        # Create and save the certificate with the code that was displayed
        certificate = Certificate.objects.create(
            code=request.POST.get('certificate_code', certificate_code),
            expires_at=expiration_date
        )
        messages.success(request, f"Сертификат {certificate.code} успешно создан!")
        # Regenerate code for next use
        certificate_code = generate_unique_code()
        expiration_date = timezone.now() + timedelta(days=90)

    context = {
        'certificate_code': certificate_code,
        'expiration_date': expiration_date,
    }
    return render(request, 'app_home/certificates/sell_certificate.html', context)


@login_required
def certificate_check(request):
    """View for checking certificate validity"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "У вас нет прав для доступа к этой странице.")
        return redirect('app_home:home')

    certificate = None
    searched = False
    now = timezone.now()

    if request.method == 'POST':
        certificate_code = request.POST.get('certificate_code', '').strip()
        if certificate_code:
            certificate = Certificate.objects.filter(code=certificate_code).first()
            searched = True

    context = {
        'certificate': certificate,
        'searched': searched,
        'now': now,
    }
    return render(request, 'app_home/certificates/check_certificate.html', context)


@login_required
def certificate_use(request, certificate_id):
    """Mark a certificate as used"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "У вас нет прав для доступа к этой странице.")
        return redirect('app_home:home')

    certificate = get_object_or_404(Certificate, id=certificate_id)

    # Check if certificate is still valid
    if certificate.is_used:
        messages.error(request, "Сертификат уже использован.")
    elif certificate.expires_at < timezone.now():
        messages.error(request, "Сертификат просрочен.")
    else:
        certificate.is_used = True
        certificate.used_at = timezone.now()
        certificate.save()
        messages.success(request, f"Сертификат {certificate.code} успешно отмечен как использованный.")

    return redirect('app_home:certificate_check')


@login_required
def certificate_search(request):
    """API endpoint to search for certificate by code - not used in current implementation"""
    # This view is not used since we switched to standard Django forms
    # Keeping it for potential future use
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        import json
        data = json.loads(request.body)
        code = data.get('code', '')

        try:
            certificate = Certificate.objects.get(code=code)
            return JsonResponse({
                'success': True,
                'certificate': {
                    'code': certificate.code,
                    'is_used': certificate.is_used,
                    'created_at': certificate.created_at.isoformat(),
                    'expires_at': certificate.expires_at.isoformat(),
                    'used_at': certificate.used_at.isoformat() if certificate.used_at else None
                }
            })
        except Certificate.DoesNotExist:
            return JsonResponse({'success': False})

    return JsonResponse({'success': False})


def handler404(request, exception):
    """
    Custom 404 handler to serve a styled 404 page.
    """
    return render(request, "404.html", status=404)
