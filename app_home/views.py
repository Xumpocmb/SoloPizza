from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from django.views.decorators.cache import cache_page
from django.conf import settings

from app_cart.models import CartItem
from app_cart.utils import validate_cart_items_for_branch
from app_catalog.models import Product
from app_home.models import CafeBranch, Vacancy, VacancyApplication, Feedback
from app_home.forms import VacancyApplicationForm, FeedbackForm


@cache_page(60 * 60 * 6)  # Кеширование на 6 часов
def home_page(request):
    active_vacancies = Vacancy.objects.filter(is_active=True)
    context = {
        "vacancies": active_vacancies,
    }
    return render(request, "app_home/home.html", context=context)


@require_POST
def select_branch(request):
    branch_id = request.POST.get("branch_id")
    try:
        if branch_id:
            branch = CafeBranch.objects.get(id=branch_id)
            request.session["selected_branch_id"] = branch_id
            messages.success(request, "Филиал изменен!", extra_tags="success")

            cart_items = CartItem.objects.filter(user=request.user).select_related('item__category')
            unavailable_items = validate_cart_items_for_branch(cart_items, branch)

            if unavailable_items:
                messages.warning(
                    request,
                    f"Некоторые товары в корзине недоступны в филиале '{branch.name}'. "
                    "Пожалуйста, удалите их перед оформлением заказа."
                )

            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request, "Ошибка: филиал не выбран!", extra_tags="error")
    except CafeBranch.DoesNotExist:
        messages.error(request, "Выбранный филиал не найден", extra_tags="error")
        return redirect('/')
    return redirect(request.META.get("HTTP_REFERER"))


@cache_page(60 * 60 * 6)  # Кеширование на 6 часов
def discounts_view(request):
    pizza_weekly = Product.objects.filter(category__slug="picca", is_active=True, is_weekly_special=True).first()
    context = {"pizza_weekly": pizza_weekly}
    return render(request, "app_home/discounts.html", context=context)


@cache_page(60 * 60 * 12)  # Кеширование на 12 часов
def vacancy_list(request):
    """Отображает список всех активных вакансий"""
    vacancies = Vacancy.objects.filter(is_active=True)
    context = {
        "vacancies": vacancies,
        "title": "Вакансии"
    }
    return render(request, "app_home/vacancy_list.html", context=context)


@cache_page(60 * 60 * 12)  # Кеширование на 12 часов
def vacancy_detail(request, vacancy_id):
    """Отображает детальную информацию о конкретной вакансии"""
    vacancy = get_object_or_404(Vacancy, id=vacancy_id, is_active=True)
    context = {
        "vacancy": vacancy,
        "title": vacancy.title
    }
    return render(request, "app_home/vacancy_detail.html", context=context)


@csrf_protect
def vacancy_apply(request, vacancy_id):
    """Отображает форму для отклика на вакансию и обрабатывает её отправку"""
    vacancy = get_object_or_404(Vacancy, id=vacancy_id, is_active=True)
    
    if request.method == 'POST':
        form = VacancyApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.vacancy = vacancy
            application.save()
            messages.success(request, "Ваш отклик успешно отправлен! Мы свяжемся с вами в ближайшее время.", extra_tags="success")
            return redirect(reverse('app_home:vacancy_detail', kwargs={'vacancy_id': vacancy_id}))
    else:
        form = VacancyApplicationForm()
    
    context = {
        "vacancy": vacancy,
        "form": form,
        "title": f"Отклик на вакансию: {vacancy.title}"
    }
    return render(request, "app_home/vacancy_apply.html", context=context)


@cache_page(60 * 60 * 6)  # Кеширование на 6 часов
def contacts_view(request):
    """Отображает страницу контактов с информацией о выбранном филиале"""
    # Информация о филиале уже доступна через контекстный процессор
    # selected_branch передается через app_home.context_processors.site_context_processor
    # и уже кешируется там
    
    breadcrumbs = [
        {'title': 'Главная', 'url': '/'},
        {'title': 'Контакты', 'url': reverse('app_home:contacts')}
    ]
    
    context = {
        "breadcrumbs": breadcrumbs,
        "title": "Контакты"
    }
    
    return render(request, "app_home/contacts.html", context=context)


@csrf_protect
def feedback_view(request):
    """Отображает форму вопросов и предложений и обрабатывает её отправку"""
    
    breadcrumbs = [
        {'title': 'Главная', 'url': '/'},
        {'title': 'Вопросы и предложения', 'url': reverse('app_home:feedback')}
    ]
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ваш вопрос/предложение успешно отправлено! Мы свяжемся с вами в ближайшее время.", extra_tags="success")
            return redirect(reverse('app_home:feedback'))
    else:
        form = FeedbackForm()
    
    context = {
        "breadcrumbs": breadcrumbs,
        "form": form,
        "title": "Вопросы и предложения"
    }
    
    return render(request, "app_home/feedback.html", context=context)
