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
                login(request, user)
                # Cart merging logic
                session_cart = SessionCart(request)
                if session_cart.cart:
                    for item_data in session_cart:
                        product = item_data['product']
                        variant = item_data['variant']
                        board1 = item_data['board1']
                        board2 = item_data['board2']
                        sauce = item_data['sauce']
                        addons = item_data['addons']
                        drink = item_data['drink']
                        quantity = item_data['quantity']

                        cart_item, created = CartItem.objects.get_or_create(
                            user=user,
                            item=product,
                            item_variant=variant,
                            board1=board1,
                            board2=board2,
                            sauce=sauce,
                            drink=drink,
                            defaults={'quantity': quantity}
                        )
                        if not created:
                            cart_item.quantity += quantity
                            cart_item.save()
                        
                        if addons:
                            cart_item.addons.set(addons)

                    session_cart.clear()
                
                return redirect("app_home:home")
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
