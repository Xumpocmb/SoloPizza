from app_home.models import CafeBranch
from app_catalog.models import Category

DEFAULT_BRANCH_ID = 1

def site_context_processor(request):
    branches = CafeBranch.objects.filter(is_active=True)
    selected_branch_id = request.session.get('selected_branch_id', DEFAULT_BRANCH_ID)
    try:
        selected_branch_id = int(selected_branch_id)
    except (ValueError, TypeError):
        selected_branch_id = DEFAULT_BRANCH_ID

    selected_branch = CafeBranch.objects.get(id=selected_branch_id)
    if request.user.is_superuser:
        categories = Category.objects.filter(is_active=True, branch=selected_branch).order_by('id')
    else:
        categories = Category.objects.filter(is_active=True, branch=selected_branch, is_for_admin=False)


    return {
        'branches': branches,
        'categories': categories,
        'selected_branch_id': str(selected_branch_id)
    }
