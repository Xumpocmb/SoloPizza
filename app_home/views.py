from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
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


@staff_member_required
def utm_analytics_view(request):
    # Aggregate UTM data
    utm_data = TrackedUTM.objects.values("utm_source", "utm_medium", "utm_campaign").annotate(count=Count("id")).order_by("-count")

    # Get TrackedURL data
    tracked_url_data = TrackedURL.objects.all().order_by("-clicks")

    context = {
        "utm_data": utm_data,
        "tracked_url_data": tracked_url_data,
        "title": "UTM Analytics",
        "breadcrumbs": [{"title": "Главная", "url": "/"}, {"title": "UTM Analytics", "url": "#"}],
    }
    return render(request, "app_home/utm_analytics.html", context)


def partners_view(request):
    """Отображает страницу с информацией о партнерах"""
    from app_home.models import Partner

    partners = Partner.objects.all()

    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Партнеры", "url": reverse("app_home:partners")}]

    context = {"partners": partners, "title": "Наши партнеры", "breadcrumbs": breadcrumbs}

    return render(request, "app_home/partners.html", context=context)
