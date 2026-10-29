from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import redirect, render

from app_cart.models import CartItem
from app_cart.session_cart import SessionCart
from app_catalog.models import Product, ProductVariant, BoardParams, AddonParams, PizzaSauce


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Вы успешно зарегистрировались!")
            return redirect("app_user:login")
    else:
        form = UserCreationForm()
    return render(request, "app_user/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(username=username, password=password)
            if user is not None:
                # Get current guest_token and session_key before login
                guest_token = request.COOKIES.get('guest_token')
                session_key = request.session.session_key or request.session.create()
                
                login(request, user)
                
                # Order migration logic
                from app_order.models import Order # Import Order model

                # Migrate orders that match the guest_token (if exists) and have no user assigned
                if guest_token:
                    Order.objects.filter(guest_token=guest_token, user__isnull=True).update(user=user)
                
                # Migrate orders that match the session_key (if exists) and have no user assigned
                if session_key:
                    Order.objects.filter(session_key=session_key, user__isnull=True).update(user=user)

                # Do not clear guest_token cookie to allow user to access unauthenticated orders after logout
                next_url = request.GET.get('next')
                print(next_url)
                if next_url:
                    response = redirect(next_url)
                else:
                    response = redirect('app_home:home')
                
                return response
            else:
                form.add_error(None, "Неверное имя пользователя или пароль.")
    else:
        form = AuthenticationForm()
    return render(request, "app_user/login.html", {"form": form})


def logout_view(request):
    try:
        logout(request)
        messages.success(request, "Вы успешно вышли из системы.", extra_tags="success")
    except Exception as e:
        messages.error(request, f"Произошла ошибка при выходе из системы: {e}", extra_tags="error")
    return redirect("app_home:home")
