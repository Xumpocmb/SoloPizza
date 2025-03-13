from django.contrib import messages
from django.shortcuts import render, redirect


def home_page(request):
    return render(request, 'app_home/home.html')


def select_branch(request):
    branch_id = request.GET.get('branch_id')
    if branch_id:
        request.session['selected_branch_id'] = branch_id
        messages.success(request, 'Филиал изменен!', extra_tags='success')
    else:
        messages.error(request, 'Ошибка: филиал не выбран!', extra_tags='error')
    return redirect(request.META.get('HTTP_REFERER'))