from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from app_user.forms import PhoneAuthenticationForm, PhoneRegistrationForm


def register(request):
    if request.method == 'POST':
        form = PhoneRegistrationForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                # Аутентификация с использованием phone_number
                user = authenticate(
                    request,
                    phone_number=form.cleaned_data['phone_number'],  # Используем phone_number
                    password=form.cleaned_data['password1']
                )
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Вы успешно зарегистрировались и вошли в систему.', extra_tags='success')
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


def user_login(request):
    if request.user.is_authenticated:
        return redirect('app_home:home')

    if request.method == 'POST':
        form = PhoneAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(username=username, password=password)
                if user:
                    login(request, user)
                    messages.success(request, 'Вы успешно вошли в систему.', extra_tags='success')
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    else:
                        return redirect('app_home:home')
                else:
                    messages.error(request, 'Ошибка аутентификации. Пожалуйста, попробуйте снова.', extra_tags='error')
                    return redirect(request.META.get('HTTP_REFERER'))
            except Exception as e:
                messages.error(request, f'Произошла ошибка при входе в систему.', extra_tags='error')
        else:
            messages.error(request, 'Неверный номер телефона или пароль. Пожалуйста, попробуйте снова.', extra_tags='error')
    else:
        form = PhoneAuthenticationForm()

    return render(request, 'app_user/login.html', {'form': form})


def logout_view(request):
    try:
        logout(request)
        messages.success(request, 'Вы успешно вышли из системы.', extra_tags='success')
    except Exception as e:
        messages.error(request, f'Произошла ошибка при выходе из системы: {e}', extra_tags='error')
    return redirect('app_home:home')
