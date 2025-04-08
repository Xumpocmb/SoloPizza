from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.shortcuts import redirect, render

from app_cart.models import CartItem
from app_catalog.models import Item, ItemParams
from app_user.forms import PhoneAuthenticationForm, PhoneRegistrationForm


def register_view(request):
    if request.method == 'POST':
        form = PhoneRegistrationForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                user = authenticate(request,
                                    username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Вы успешно зарегистрировались и вошли в систему.', extra_tags='success')

                    add_to_cart_after_login(request, user)

                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    else:
                        return redirect('app_home:home')
                else:
                    messages.error(request, 'Ошибка аутентификации. Пожалуйста, попробуйте снова.', extra_tags='error')
            except Exception as e:
                messages.error(request, f'Произошла ошибка при регистрации: {e}', extra_tags='error')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.', extra_tags='error')
    else:
        form = PhoneRegistrationForm()

    return render(request, 'app_user/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('app_home:home')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = PhoneAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print(f"Authenticating user with phone_number={username}, password={password}")
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Вы успешно вошли в систему.', extra_tags='success')

                add_to_cart_after_login(request, user)

                if next_url:
                    return redirect(next_url)
                return redirect('app_home:home')
            else:
                messages.error(request, 'Ошибка аутентификации. Пожалуйста, попробуйте снова.', extra_tags='error')
        else:
            print("Form errors:", form.errors)
            print("Form cleaned data:", form.cleaned_data)
            print("Form is valid:", form.is_valid())
            messages.error(request, 'Неверный номер телефона или пароль. Пожалуйста, попробуйте снова.',
                           extra_tags='error')
    else:
        form = PhoneAuthenticationForm()

    return render(request, 'app_user/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    try:
        logout(request)
        messages.success(request, 'Вы успешно вышли из системы.', extra_tags='success')
    except Exception as e:
        messages.error(request, f'Произошла ошибка при выходе из системы: {e}', extra_tags='error')
    return redirect('app_home:home')


def add_to_cart_after_login(request, user):
    """Добавляем товары из сессии в корзину"""
    cart_in_session = request.session.get('cart_in_session', [])
    for item_data in cart_in_session:
        item = Item.objects.get(slug=item_data['item_slug'])
        size = ItemParams.objects.get(id=item_data['size_id'])

        # Создаем или обновляем запись в корзине
        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            item=item,
            item_params=size,
            defaults={'quantity': item_data['quantity']}
        )
        if not created:
            cart_item.quantity += item_data['quantity']
            cart_item.save()

        # Добавляем борт
        if item_data['board_id']:
            cart_item.board_id = item_data['board_id']
            cart_item.save()

        # Добавляем добавки
        if item_data['addon_ids']:
            cart_item.addons.set(item_data['addon_ids'])

        messages.success(request, f'{item.name} успешно добавлен в корзину.', extra_tags='success')

    request.session.pop('cart_in_session', None)
