from app_cart.models import CartItem
from app_home.models import CafeBranch, Company, Discount, SiteSettings
from app_catalog.models import Category
from django.conf import settings
from app_cart.session_cart import SessionCart  # Import SessionCart

DEFAULT_BRANCH_ID = 1


def get_active_branches(request):
    """Активные филиалы вместе с телефонами и графиком, один запрос на запрос.

    Список живёт на request, поэтому контекстный процессор и представления берут
    одни и те же объекты: филиалы не выбираются заново в каждом шаблоне, а телефоны
    и график приходят вместе с ними.
    """
    branches = getattr(request, "_active_branches", None)
    if branches is None:
        branches = list(CafeBranch.objects.filter(is_active=True).prefetch_related("working_hours", "branch_phones"))
        request._active_branches = branches
    return branches


def get_selected_branch_id(request):
    """Идентификатор выбранного филиала из сессии, всегда целое число.

    В сессии значение лежит строкой и может быть испорчено, поэтому приводим его к
    числу, а при неудаче возвращаем филиал по умолчанию и сразу чистим сессию.
    """
    raw_branch_id = request.session.get("selected_branch_id", DEFAULT_BRANCH_ID)

    try:
        selected_branch_id = int(raw_branch_id)
    except (TypeError, ValueError):
        selected_branch_id = DEFAULT_BRANCH_ID

    if str(selected_branch_id) != str(raw_branch_id):
        request.session["selected_branch_id"] = str(selected_branch_id)

    return selected_branch_id


def get_company(request):
    """Юридическое лицо продавца: реквизиты, банк, адрес. Единая запись.

    Оставляем на request, чтобы не ходить в БД на каждый рендер футера.
    """
    company = getattr(request, "_company", None)
    if company is None:
        company = Company.objects.filter(is_active=True).order_by("pk").first()
        request._company = company
    return company


def company_context(request):
    """Контекст шаблонов: юридическое лицо продавца для футера и страниц."""
    return {"company": get_company(request)}


def site_context_processor(request):
    # Телефоны и график нужны шапке, подвалу, главной и микроразметке, поэтому
    # забираем их одним запросом и делимся одними и теми же объектами: иначе
    # branch_phones выбирается заново в каждом шаблоне, а branches — ещё раз
    # в restaurant_schema.
    branches = get_active_branches(request)

    selected_branch_id = get_selected_branch_id(request)

    selected_branch = next((branch for branch in branches if branch.id == selected_branch_id), None) or (branches[0] if branches else None)

    if not selected_branch:
        return {
            "branches": [],
            "categories": [],
            "selected_branch_id": None,
            "selected_branch": None,
            "company": get_company(request),
        }

    if str(selected_branch_id) != str(selected_branch.id):
        request.session["selected_branch_id"] = str(selected_branch.id)

    # Получаем категории для конкретного филиала
    try:
        if request.user.is_superuser or request.user.is_staff:
            categories = Category.objects.filter(is_active=True, branch=selected_branch).order_by("order")
        else:
            categories = Category.objects.filter(is_active=True, branch=selected_branch, is_for_admin=False).order_by("order")
    except Exception:
        categories = []

    return {
        "branches": branches,
        "categories": categories,
        "selected_branch_id": str(selected_branch.id),
        "selected_branch": selected_branch,
        "company": get_company(request),
    }


def canonical_context(request):
    """Канонический URL страницы без GET-параметров.

    Параметры вроде ``utm_*``, ``yclid`` или ``size`` не создают отдельного
    содержимого, поэтому все их варианты должны указывать на один адрес.
    Домен берём из настроек, чтобы canonical всегда был с нужным протоколом
    и без ``www``, даже если запрос пришёл через прокси.
    """
    base_url = (getattr(settings, "DOMAIN_NAME", "") or "").rstrip("/")
    if not base_url:
        base_url = f"{request.scheme}://{request.get_host()}"

    return {"canonical_url": f"{base_url}{request.path}"}


def cart_context(request):
    session_cart = SessionCart(request)
    cart_total_quantity = len(session_cart)  # SessionCart has __len__ method

    return {
        "cart_total_quantity": cart_total_quantity,
    }


def site_settings_context_processor(request):
    """Настройки сайта: логотип, доступность заказов и снег."""
    site_settings = SiteSettings.get_solo()
    return {
        "site_settings": site_settings,
        "SNOW_ENABLED": site_settings.snow_enabled,
    }
